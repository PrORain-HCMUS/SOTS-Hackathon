"""
Celery tasks for aggregating crop statistics.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.workers.celery_app import celery_app
from app.core.db import get_db_context
from app.core.crud import get_asset
from app.core.aggregation import aggregate_crop_map_to_stats

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.workers.tasks_aggregate.aggregate_crop_map")
def aggregate_crop_map(
    self,
    asset_id: str,
    period_start_iso: str,
    period_end_iso: str,
    admin_level: int = 1,
):
    """
    Aggregate a crop map asset to area statistics.
    
    Args:
        asset_id: UUID of the crop map asset
        period_start_iso: Period start as ISO string
        period_end_iso: Period end as ISO string
        admin_level: Admin level for aggregation (1=province, 2=district)
    """
    logger.info(f"Aggregating crop map: asset_id={asset_id}, admin_level={admin_level}")
    
    try:
        asset_uuid = UUID(asset_id)
        period_start = datetime.fromisoformat(period_start_iso)
        period_end = datetime.fromisoformat(period_end_iso)
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return {"status": "error", "message": str(e)}
    
    with get_db_context() as db:
        # Get the asset
        asset = get_asset(db, asset_uuid)
        if not asset:
            logger.error(f"Asset not found: {asset_id}")
            return {"status": "error", "message": f"Asset not found: {asset_id}"}
        
        if asset.asset_type != "crop_map_patch":
            logger.warning(f"Asset is not a crop map: {asset.asset_type}")
        
        # Run aggregation
        stats = aggregate_crop_map_to_stats(
            db=db,
            crop_map_asset=asset,
            period_start=period_start,
            period_end=period_end,
            admin_level=admin_level,
        )
        
        logger.info(f"Created {len(stats)} area stat records")
        
        return {
            "status": "success",
            "asset_id": asset_id,
            "stats_count": len(stats),
        }


@celery_app.task(bind=True, name="app.workers.tasks_aggregate.aggregate_all_pending")
def aggregate_all_pending(self, admin_level: int = 1):
    """
    Find all crop map assets without aggregated stats and process them.
    
    Args:
        admin_level: Admin level for aggregation
    """
    logger.info("Aggregating all pending crop maps")
    
    from sqlalchemy import text
    
    with get_db_context() as db:
        # Find crop maps without corresponding area_stats
        query = text("""
            SELECT a.asset_id, a.period_start, a.period_end
            FROM assets a
            WHERE a.asset_type = 'crop_map_patch'
            AND NOT EXISTS (
                SELECT 1 FROM area_stats s
                WHERE s.source_asset_id = a.asset_id
            )
            ORDER BY a.created_at DESC
            LIMIT 100
        """)
        
        result = db.execute(query)
        pending = result.fetchall()
        
        logger.info(f"Found {len(pending)} pending crop maps to aggregate")
        
        processed = 0
        for asset_id, period_start, period_end in pending:
            try:
                aggregate_crop_map.delay(
                    asset_id=str(asset_id),
                    period_start_iso=period_start.isoformat(),
                    period_end_iso=period_end.isoformat(),
                    admin_level=admin_level,
                )
                processed += 1
            except Exception as e:
                logger.error(f"Failed to queue aggregation for {asset_id}: {e}")
        
        return {
            "status": "success",
            "pending_count": len(pending),
            "queued_count": processed,
        }
