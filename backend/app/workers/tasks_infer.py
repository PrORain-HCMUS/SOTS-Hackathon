"""
Celery tasks for S4A model inference.
"""

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import numpy as np

from app.workers.celery_app import celery_app
from app.core.db import get_db_context
from app.core.config import get_settings
from app.core.spaces import get_spaces_client
from app.core.raster_utils import write_cog
from app.core.crud import (
    get_tile, get_model_by_task, upsert_asset,
    create_inference_run, update_inference_run
)
from app.core.time_utils import get_month_range, format_period_key
from app.core.s4a_infer import (
    run_s4a_on_bbox, S4AModelNotFoundError, download_model_weights
)

logger = logging.getLogger(__name__)


def get_tile_bbox(db, tile_id: str) -> Optional[Tuple[float, float, float, float]]:
    """Get bbox from tile geometry."""
    from geoalchemy2.shape import to_shape
    
    tile = get_tile(db, tile_id)
    if not tile:
        return None
    
    geom = to_shape(tile.geom)
    return geom.bounds


@celery_app.task(bind=True, name="app.workers.tasks_infer.run_s4a_inference")
def run_s4a_inference(
    self,
    tile_id: str,
    end_year: int,
    end_month: int,
    window_len: int = 6,
    size: Tuple[int, int] = (61, 61),
):
    """
    Run S4A ConvLSTM inference on a tile.
    
    Args:
        tile_id: Tile ID
        end_year: End year
        end_month: End month (1-12)
        window_len: Number of months for input
        size: Output size (width, height)
    """
    logger.info(
        f"Running S4A inference: tile={tile_id}, "
        f"end={end_year}-{end_month:02d}, window_len={window_len}"
    )
    
    settings = get_settings()
    
    with get_db_context() as db:
        # Get tile bbox
        bbox = get_tile_bbox(db, tile_id)
        if not bbox:
            logger.error(f"Tile not found: {tile_id}")
            return {"status": "error", "message": f"Tile not found: {tile_id}"}
        
        # Get S4A model from database
        model = get_model_by_task(db, task="crop_classification", name="S4A-ConvLSTM")
        if not model:
            logger.error("S4A model not registered in database")
            return {"status": "error", "message": "S4A model not registered"}
        
        # Calculate period
        from dateutil.relativedelta import relativedelta
        end_date = datetime(end_year, end_month, 1)
        start_date = end_date - relativedelta(months=window_len - 1)
        
        period_start, _ = get_month_range(start_date.year, start_date.month)
        _, period_end = get_month_range(end_year, end_month)
        
        # Create inference run record
        run = create_inference_run(db, model_id=model.model_id, status="running")
        
        try:
            # Run S4A inference
            pred_map, stats = run_s4a_on_bbox(
                bbox=bbox,
                end_year=end_year,
                end_month=end_month,
                weights_s3_key=model.weights_s3_key,
                window_len=window_len,
                size=size,
                device="cpu",
            )
            
            # Save prediction map as GeoTIFF
            with tempfile.TemporaryDirectory() as tmpdir:
                tif_path = Path(tmpdir) / "crop_map.tif"
                write_cog(
                    data=pred_map,
                    output_path=tif_path,
                    bbox=bbox,
                    crs="EPSG:4326",
                    dtype="uint16",
                )
                
                # Upload to Spaces
                period_key = format_period_key(period_start, period_end)
                s3_key = f"assets/crop_maps/{tile_id}/{period_key}/crop_map.tif"
                
                spaces = get_spaces_client()
                upload_result = spaces.upload_file(
                    local_path=tif_path,
                    s3_key=s3_key,
                    content_type="image/tiff",
                    public=True,
                )
                
                # Create asset record
                asset, _ = upsert_asset(
                    db=db,
                    asset_type="crop_map_patch",
                    tile_id=tile_id,
                    period_start=period_start,
                    period_end=period_end,
                    s3_bucket=upload_result["s3_bucket"],
                    s3_key=upload_result["s3_key"],
                    etag=upload_result["etag"],
                    size_bytes=upload_result["size_bytes"],
                    resolution_m=10,
                    crs="EPSG:4326",
                    bbox=list(bbox),
                )
                
                # Update inference run
                update_inference_run(
                    db=db,
                    run_id=run.run_id,
                    status="completed",
                    output_asset_id=asset.asset_id,
                    metrics={"stats": stats},
                    finished=True,
                )
                
                logger.info(f"S4A inference completed: asset_id={asset.asset_id}")
                
                return {
                    "status": "success",
                    "run_id": str(run.run_id),
                    "asset_id": str(asset.asset_id),
                    "s3_key": s3_key,
                    "stats": stats,
                }
                
        except S4AModelNotFoundError as e:
            logger.error(f"S4A model not available: {e}")
            update_inference_run(
                db=db,
                run_id=run.run_id,
                status="failed",
                metrics={"error": str(e)},
                finished=True,
            )
            return {"status": "error", "message": str(e)}
            
        except Exception as e:
            logger.error(f"S4A inference failed: {e}")
            update_inference_run(
                db=db,
                run_id=run.run_id,
                status="failed",
                metrics={"error": str(e)},
                finished=True,
            )
            raise


@celery_app.task(bind=True, name="app.workers.tasks_infer.run_s4a_on_bbox_task")
def run_s4a_on_bbox_task(
    self,
    bbox: Tuple[float, float, float, float],
    end_year: int,
    end_month: int,
    window_len: int = 6,
    size: Tuple[int, int] = (61, 61),
):
    """
    Run S4A inference directly on a bbox (without tile lookup).
    
    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat)
        end_year: End year
        end_month: End month
        window_len: Number of months
        size: Output size
    """
    logger.info(f"Running S4A on bbox: {bbox}")
    
    with get_db_context() as db:
        model = get_model_by_task(db, task="crop_classification", name="S4A-ConvLSTM")
        if not model:
            return {"status": "error", "message": "S4A model not registered"}
        
        try:
            pred_map, stats = run_s4a_on_bbox(
                bbox=bbox,
                end_year=end_year,
                end_month=end_month,
                weights_s3_key=model.weights_s3_key,
                window_len=window_len,
                size=size,
                device="cpu",
            )
            
            return {
                "status": "success",
                "shape": list(pred_map.shape),
                "stats": stats,
            }
            
        except S4AModelNotFoundError as e:
            return {"status": "error", "message": str(e)}
