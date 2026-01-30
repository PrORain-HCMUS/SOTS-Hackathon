"""
Celery tasks for anomaly detection and alerts.
"""

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from uuid import UUID

import numpy as np

from app.workers.celery_app import celery_app
from app.core.db import get_db_context
from app.core.spaces import get_spaces_client
from app.core.raster_utils import read_geotiff
from app.core.crud import get_asset, get_admin_unit_by_name
from app.core.alerts import run_anomaly_detection

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.workers.tasks_alerts.run_anomaly_detection_task")
def run_anomaly_detection_task(
    self,
    asset_id: str,
    admin_name: Optional[str] = None,
    period_start_iso: Optional[str] = None,
    period_end_iso: Optional[str] = None,
):
    """
    Run anomaly detection on a monthly stack asset.
    
    Args:
        asset_id: UUID of the monthly stack asset
        admin_name: Optional admin unit name for context
        period_start_iso: Period start as ISO string
        period_end_iso: Period end as ISO string
    """
    logger.info(f"Running anomaly detection: asset_id={asset_id}")
    
    try:
        asset_uuid = UUID(asset_id)
        period_start = datetime.fromisoformat(period_start_iso) if period_start_iso else None
        period_end = datetime.fromisoformat(period_end_iso) if period_end_iso else None
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return {"status": "error", "message": str(e)}
    
    with get_db_context() as db:
        # Get the asset
        asset = get_asset(db, asset_uuid)
        if not asset:
            logger.error(f"Asset not found: {asset_id}")
            return {"status": "error", "message": f"Asset not found: {asset_id}"}
        
        # Get admin unit if specified
        admin_id = None
        if admin_name:
            admin = get_admin_unit_by_name(db, admin_name)
            if admin:
                admin_id = admin.admin_id
        
        # Download the asset from Spaces
        spaces = get_spaces_client()
        
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            spaces.download_file(asset.s3_key, tmp_path)
            
            # Read the GeoTIFF
            data, metadata = read_geotiff(tmp_path)
            
            # Reshape data back to (1, T, C, H, W) format
            # Assuming it was stored as (T*C, H, W)
            total_bands = data.shape[0]
            C = 4  # B02, B03, B04, B08
            T = total_bands // C
            H, W = data.shape[1], data.shape[2]
            
            monthly_stack = data.reshape(T, C, H, W)
            monthly_stack = np.expand_dims(monthly_stack, axis=0)  # (1, T, C, H, W)
            
            # Run anomaly detection
            alerts = run_anomaly_detection(
                db=db,
                monthly_stack=monthly_stack,
                admin_id=admin_id,
                period_start=period_start or asset.period_start,
                period_end=period_end or asset.period_end,
                source_asset_id=asset_uuid,
            )
            
            logger.info(f"Created {len(alerts)} alerts")
            
            return {
                "status": "success",
                "asset_id": asset_id,
                "alerts_count": len(alerts),
                "alert_ids": [str(a.alert_id) for a in alerts],
            }
            
        finally:
            tmp_path.unlink(missing_ok=True)


@celery_app.task(bind=True, name="app.workers.tasks_alerts.check_all_recent_assets")
def check_all_recent_assets(self, hours_back: int = 24):
    """
    Check all recent monthly stack assets for anomalies.
    
    Args:
        hours_back: Number of hours to look back for assets
    """
    from datetime import timedelta
    from app.core.time_utils import get_utc_now
    from sqlalchemy import text
    
    logger.info(f"Checking recent assets for anomalies (hours_back={hours_back})")
    
    with get_db_context() as db:
        cutoff = get_utc_now() - timedelta(hours=hours_back)
        
        query = text("""
            SELECT asset_id, period_start, period_end
            FROM assets
            WHERE asset_type = 's2_monthly_stack_patch'
            AND created_at >= :cutoff
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        result = db.execute(query, {"cutoff": cutoff})
        assets = result.fetchall()
        
        logger.info(f"Found {len(assets)} recent assets to check")
        
        queued = 0
        for asset_id, period_start, period_end in assets:
            try:
                run_anomaly_detection_task.delay(
                    asset_id=str(asset_id),
                    period_start_iso=period_start.isoformat() if period_start else None,
                    period_end_iso=period_end.isoformat() if period_end else None,
                )
                queued += 1
            except Exception as e:
                logger.error(f"Failed to queue anomaly detection for {asset_id}: {e}")
        
        return {
            "status": "success",
            "assets_found": len(assets),
            "queued": queued,
        }
