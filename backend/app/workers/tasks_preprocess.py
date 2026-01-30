"""
Celery tasks for preprocessing Sentinel-2 data.
"""

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

import numpy as np

from app.workers.celery_app import celery_app
from app.core.db import get_db_context
from app.core.config import get_settings
from app.core.sentinelhub_client import get_sentinelhub_client
from app.core.spaces import get_spaces_client
from app.core.raster_utils import write_cog
from app.core.crud import (
    get_tile, asset_exists, upsert_asset
)
from app.core.time_utils import get_month_range, format_period_key

logger = logging.getLogger(__name__)


def get_tile_bbox(db, tile_id: str) -> Optional[Tuple[float, float, float, float]]:
    """Get bbox from tile geometry."""
    from geoalchemy2.shape import to_shape
    
    tile = get_tile(db, tile_id)
    if not tile:
        return None
    
    geom = to_shape(tile.geom)
    return geom.bounds  # (minx, miny, maxx, maxy)


@celery_app.task(bind=True, name="app.workers.tasks_preprocess.preprocess_monthly_stack")
def preprocess_monthly_stack(
    self,
    tile_id: str,
    end_year: int,
    end_month: int,
    window_len: int = 6,
    size: Tuple[int, int] = (61, 61),
):
    """
    Preprocess monthly stack for S4A model input.
    
    Fetches 6 monthly composites from Sentinel Hub, applies cloud masking,
    and uploads to Spaces.
    
    Args:
        tile_id: Tile ID
        end_year: End year
        end_month: End month (1-12)
        window_len: Number of months (default 6)
        size: Output size (width, height)
    """
    logger.info(
        f"Preprocessing monthly stack: tile={tile_id}, "
        f"end={end_year}-{end_month:02d}, window_len={window_len}"
    )
    
    settings = get_settings()
    
    with get_db_context() as db:
        # Get tile bbox
        bbox = get_tile_bbox(db, tile_id)
        if not bbox:
            logger.error(f"Tile not found: {tile_id}")
            return {"status": "error", "message": f"Tile not found: {tile_id}"}
        
        # Calculate period
        period_start, _ = get_month_range(
            end_year - (window_len // 12),
            ((end_month - window_len) % 12) + 1
        )
        _, period_end = get_month_range(end_year, end_month)
        
        # Check if asset already exists (idempotent)
        if asset_exists(db, "s2_monthly_stack_patch", tile_id, period_start, period_end):
            logger.info(f"Asset already exists for tile {tile_id}, period {period_start} to {period_end}")
            return {"status": "skipped", "message": "Asset already exists"}
        
        # Fetch monthly stack from Sentinel Hub
        sh_client = get_sentinelhub_client()
        monthly_stack = sh_client.fetch_monthly_stack(
            bbox=bbox,
            end_year=end_year,
            end_month=end_month,
            window_len=window_len,
            size=size,
        )
        
        logger.info(f"Fetched monthly stack with shape {monthly_stack.shape}")
        
        # Save preview GeoTIFF (last month composite)
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save the full stack as a multi-band GeoTIFF
            # Shape: (1, T, C, H, W) -> reshape to (T*C, H, W) for storage
            stack_2d = monthly_stack[0]  # (T, C, H, W)
            T, C, H, W = stack_2d.shape
            stack_flat = stack_2d.reshape(T * C, H, W)  # (T*C, H, W)
            
            tif_path = Path(tmpdir) / "monthly_stack.tif"
            write_cog(
                data=stack_flat,
                output_path=tif_path,
                bbox=bbox,
                crs="EPSG:4326",
                dtype="float32",
            )
            
            # Upload to Spaces
            period_key = format_period_key(period_start, period_end)
            s3_key = f"assets/s2_monthly_stack/{tile_id}/{period_key}/monthly_stack.tif"
            
            spaces = get_spaces_client()
            upload_result = spaces.upload_file(
                local_path=tif_path,
                s3_key=s3_key,
                content_type="image/tiff",
                public=True,
            )
            
            # Insert asset record
            asset, created = upsert_asset(
                db=db,
                asset_type="s2_monthly_stack_patch",
                tile_id=tile_id,
                period_start=period_start,
                period_end=period_end,
                s3_bucket=upload_result["s3_bucket"],
                s3_key=upload_result["s3_key"],
                etag=upload_result["etag"],
                size_bytes=upload_result["size_bytes"],
                resolution_m=10,
                bands=["B02", "B03", "B04", "B08"] * window_len,
                crs="EPSG:4326",
                bbox=list(bbox),
            )
            
            logger.info(f"Created asset {asset.asset_id} for monthly stack")
            
            return {
                "status": "success",
                "asset_id": str(asset.asset_id),
                "s3_key": s3_key,
                "shape": list(monthly_stack.shape),
            }


@celery_app.task(bind=True, name="app.workers.tasks_preprocess.preprocess_weekly_composite")
def preprocess_weekly_composite(
    self,
    tile_id: str,
    year: int,
    week: int,
    size: Tuple[int, int] = (61, 61),
):
    """
    Create a weekly cloud-masked composite.
    
    Args:
        tile_id: Tile ID
        year: Year
        week: ISO week number (1-52)
        size: Output size
    """
    from datetime import timedelta
    from app.core.time_utils import get_utc_now
    
    logger.info(f"Creating weekly composite: tile={tile_id}, year={year}, week={week}")
    
    settings = get_settings()
    
    with get_db_context() as db:
        bbox = get_tile_bbox(db, tile_id)
        if not bbox:
            return {"status": "error", "message": f"Tile not found: {tile_id}"}
        
        # Calculate week start/end dates
        # ISO week 1 is the week containing Jan 4
        jan4 = datetime(year, 1, 4)
        week_start = jan4 + timedelta(weeks=week - 1) - timedelta(days=jan4.weekday())
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        period_start = week_start.replace(tzinfo=None)
        period_end = week_end.replace(tzinfo=None)
        
        # Check idempotency
        if asset_exists(db, "s2_weekly_composite", tile_id, period_start, period_end):
            logger.info(f"Weekly composite already exists")
            return {"status": "skipped", "message": "Asset already exists"}
        
        # Fetch composite from Sentinel Hub
        sh_client = get_sentinelhub_client()
        composite = sh_client.fetch_monthly_composite(
            bbox=bbox,
            year=year,
            month=week_start.month,  # Approximate - uses month-based fetch
            size=size,
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tif_path = Path(tmpdir) / "weekly_composite.tif"
            write_cog(
                data=composite,
                output_path=tif_path,
                bbox=bbox,
                crs="EPSG:4326",
                dtype="float32",
            )
            
            period_key = format_period_key(period_start, period_end)
            s3_key = f"assets/s2_weekly/{tile_id}/{period_key}/weekly_composite.tif"
            
            spaces = get_spaces_client()
            upload_result = spaces.upload_file(
                local_path=tif_path,
                s3_key=s3_key,
                content_type="image/tiff",
                public=True,
            )
            
            asset, _ = upsert_asset(
                db=db,
                asset_type="s2_weekly_composite",
                tile_id=tile_id,
                period_start=period_start,
                period_end=period_end,
                s3_bucket=upload_result["s3_bucket"],
                s3_key=upload_result["s3_key"],
                etag=upload_result["etag"],
                size_bytes=upload_result["size_bytes"],
                resolution_m=10,
                bands=["B02", "B03", "B04", "B08"],
                crs="EPSG:4326",
                bbox=list(bbox),
            )
            
            return {
                "status": "success",
                "asset_id": str(asset.asset_id),
                "s3_key": s3_key,
            }
