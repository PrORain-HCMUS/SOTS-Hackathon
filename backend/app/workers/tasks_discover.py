"""
Celery tasks for discovering new Sentinel-2 scenes.
"""

import logging
from datetime import datetime, timedelta

from app.workers.celery_app import celery_app
from app.core.db import get_db_context
from app.core.config import get_settings
from app.core.sentinelhub_client import get_sentinelhub_client
from app.core.crud import (
    get_tiles, scene_exists, create_scene, update_tile_sensing_time
)
from app.core.time_utils import get_utc_now, parse_iso_datetime

logger = logging.getLogger(__name__)

# Vietnam bounding box (approximate)
VIETNAM_BBOX = (102.0, 8.0, 110.0, 24.0)


@celery_app.task(bind=True, name="app.workers.tasks_discover.discover_new_scenes")
def discover_new_scenes(self, days_back: int = 7):
    """
    Discover new Sentinel-2 scenes over Vietnam.
    
    This task runs every 6 hours via Celery Beat.
    It searches for scenes in the last N days and inserts new ones.
    
    Args:
        days_back: Number of days to look back for scenes
    """
    logger.info(f"Starting scene discovery (days_back={days_back})")
    
    try:
        sh_client = get_sentinelhub_client()
        
        end_date = get_utc_now()
        start_date = end_date - timedelta(days=days_back)
        
        # Search for scenes over Vietnam
        scenes = sh_client.search_scenes(
            bbox=VIETNAM_BBOX,
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=80.0,
        )
        
        logger.info(f"Found {len(scenes)} scenes from Sentinel Hub")
        
        new_count = 0
        with get_db_context() as db:
            for scene_data in scenes:
                scene_id = scene_data["scene_id"]
                
                # Idempotent: skip if already exists
                if scene_exists(db, scene_id):
                    continue
                
                # Parse sensing time
                sensing_time_str = scene_data.get("sensing_time")
                if sensing_time_str:
                    sensing_time = parse_iso_datetime(sensing_time_str)
                else:
                    continue
                
                # Convert footprint geometry to WKT if available
                footprint = scene_data.get("footprint")
                footprint_wkt = None
                if footprint and footprint.get("type") == "Polygon":
                    coords = footprint.get("coordinates", [[]])[0]
                    if coords:
                        coord_str = ", ".join(f"{c[0]} {c[1]}" for c in coords)
                        footprint_wkt = f"POLYGON(({coord_str}))"
                
                # Create scene record
                create_scene(
                    db=db,
                    scene_id=scene_id,
                    sensing_time=sensing_time,
                    cloud_cover=scene_data.get("cloud_cover"),
                    footprint_wkt=footprint_wkt,
                    provider=scene_data.get("provider", "sentinel-hub"),
                    collection=scene_data.get("collection", "sentinel-2-l2a"),
                    status="discovered",
                )
                new_count += 1
        
        logger.info(f"Inserted {new_count} new scenes")
        return {"status": "success", "new_scenes": new_count, "total_found": len(scenes)}
        
    except Exception as e:
        logger.error(f"Scene discovery failed: {e}")
        raise


@celery_app.task(bind=True, name="app.workers.tasks_discover.discover_scenes_for_tile")
def discover_scenes_for_tile(self, tile_id: str, days_back: int = 30):
    """
    Discover scenes for a specific tile.
    
    Args:
        tile_id: Tile ID to search for
        days_back: Number of days to look back
    """
    logger.info(f"Discovering scenes for tile {tile_id}")
    
    with get_db_context() as db:
        from app.core.crud import get_tile
        from shapely import wkb
        from geoalchemy2.shape import to_shape
        
        tile = get_tile(db, tile_id)
        if not tile:
            logger.error(f"Tile not found: {tile_id}")
            return {"status": "error", "message": f"Tile not found: {tile_id}"}
        
        # Get tile bbox from geometry
        geom = to_shape(tile.geom)
        bbox = geom.bounds  # (minx, miny, maxx, maxy)
        
        sh_client = get_sentinelhub_client()
        end_date = get_utc_now()
        start_date = end_date - timedelta(days=days_back)
        
        scenes = sh_client.search_scenes(
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=80.0,
        )
        
        new_count = 0
        latest_sensing = None
        
        for scene_data in scenes:
            scene_id = scene_data["scene_id"]
            
            if scene_exists(db, scene_id):
                continue
            
            sensing_time_str = scene_data.get("sensing_time")
            if sensing_time_str:
                sensing_time = parse_iso_datetime(sensing_time_str)
            else:
                continue
            
            create_scene(
                db=db,
                scene_id=scene_id,
                sensing_time=sensing_time,
                tile_id=tile_id,
                cloud_cover=scene_data.get("cloud_cover"),
                provider=scene_data.get("provider", "sentinel-hub"),
                collection=scene_data.get("collection", "sentinel-2-l2a"),
                status="discovered",
            )
            new_count += 1
            
            if latest_sensing is None or sensing_time > latest_sensing:
                latest_sensing = sensing_time
        
        # Update tile's last seen sensing time
        if latest_sensing:
            update_tile_sensing_time(db, tile_id, latest_sensing)
        
        logger.info(f"Inserted {new_count} new scenes for tile {tile_id}")
        return {"status": "success", "tile_id": tile_id, "new_scenes": new_count}
