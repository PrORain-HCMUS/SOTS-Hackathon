"""
Aggregation module for zonal statistics calculation.

Computes crop area statistics by administrative boundaries.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.models_sqlalchemy import AdminUnit, AreaStat, Asset, CropClass
from app.core.raster_utils import read_geotiff, calculate_pixel_area_ha

logger = logging.getLogger(__name__)


def get_crop_classes(db: Session) -> Dict[int, Dict[str, Any]]:
    """Get all crop classes from database."""
    classes = db.query(CropClass).all()
    return {
        c.class_id: {
            "code": c.code,
            "name_vi": c.name_vi,
            "name_en": c.name_en,
            "is_food_crop": c.is_food_crop,
        }
        for c in classes
    }


def compute_zonal_stats_simple(
    pred_map: np.ndarray,
    bbox: Tuple[float, float, float, float],
) -> List[Dict[str, Any]]:
    """
    Compute simple zonal statistics for entire prediction map.
    
    Args:
        pred_map: Prediction map of shape (H, W) with class indices
        bbox: (min_lon, min_lat, max_lon, max_lat)
        
    Returns:
        List of dicts with class_id, pixel_count, area_ha
    """
    height, width = pred_map.shape
    pixel_area_ha = calculate_pixel_area_ha(bbox, width, height)
    
    unique_classes, counts = np.unique(pred_map, return_counts=True)
    
    stats = []
    for class_id, pixel_count in zip(unique_classes, counts):
        stats.append({
            "class_id": int(class_id),
            "pixel_count": int(pixel_count),
            "area_ha": float(pixel_count * pixel_area_ha),
        })
    
    return stats


def compute_zonal_stats_by_admin(
    db: Session,
    pred_map: np.ndarray,
    bbox: Tuple[float, float, float, float],
    admin_level: int = 1,
) -> Dict[UUID, List[Dict[str, Any]]]:
    """
    Compute zonal statistics per administrative unit.
    
    This is a simplified implementation that assigns the entire prediction
    to admin units that intersect with the bbox. For production, you would
    need proper rasterization of admin boundaries.
    
    Args:
        db: Database session
        pred_map: Prediction map of shape (H, W)
        bbox: (min_lon, min_lat, max_lon, max_lat)
        admin_level: Admin level (0=country, 1=province, 2=district)
        
    Returns:
        Dict mapping admin_id to list of stats
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    
    # Find admin units that intersect with bbox
    bbox_wkt = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
    
    query = text("""
        SELECT admin_id, name, ST_Area(ST_Intersection(geom, ST_GeomFromText(:bbox_wkt, 4326))) / ST_Area(geom) as coverage_ratio
        FROM admin_units
        WHERE level = :level
        AND ST_Intersects(geom, ST_GeomFromText(:bbox_wkt, 4326))
    """)
    
    result = db.execute(query, {"bbox_wkt": bbox_wkt, "level": admin_level})
    admin_units = result.fetchall()
    
    if not admin_units:
        logger.warning(f"No admin units found intersecting bbox {bbox}")
        return {}
    
    # Compute overall stats
    overall_stats = compute_zonal_stats_simple(pred_map, bbox)
    
    # Distribute stats proportionally based on coverage ratio
    admin_stats = {}
    for admin_id, name, coverage_ratio in admin_units:
        if coverage_ratio is None or coverage_ratio <= 0:
            continue
            
        admin_stats[admin_id] = []
        for stat in overall_stats:
            admin_stats[admin_id].append({
                "class_id": stat["class_id"],
                "pixel_count": int(stat["pixel_count"] * coverage_ratio),
                "area_ha": stat["area_ha"] * coverage_ratio,
            })
    
    return admin_stats


def upsert_area_stats(
    db: Session,
    admin_id: UUID,
    class_id: int,
    period_start: datetime,
    period_end: datetime,
    area_ha: float,
    pixel_count: int,
    source_asset_id: Optional[UUID] = None,
    confidence_low: Optional[float] = None,
    confidence_high: Optional[float] = None,
) -> AreaStat:
    """
    Insert or update area statistics record.
    
    Uses upsert logic based on unique constraint (admin_id, class_id, period_start, period_end).
    """
    # Check for existing record
    existing = db.query(AreaStat).filter(
        AreaStat.admin_id == admin_id,
        AreaStat.class_id == class_id,
        AreaStat.period_start == period_start,
        AreaStat.period_end == period_end,
    ).first()
    
    if existing:
        # Update existing record
        existing.area_ha = area_ha
        existing.pixel_count = pixel_count
        existing.source_asset_id = source_asset_id
        existing.confidence_low = confidence_low
        existing.confidence_high = confidence_high
        db.commit()
        logger.info(f"Updated area_stat {existing.stat_id}")
        return existing
    else:
        # Create new record
        stat = AreaStat(
            admin_id=admin_id,
            class_id=class_id,
            period_start=period_start,
            period_end=period_end,
            area_ha=area_ha,
            pixel_count=pixel_count,
            source_asset_id=source_asset_id,
            confidence_low=confidence_low,
            confidence_high=confidence_high,
        )
        db.add(stat)
        db.commit()
        db.refresh(stat)
        logger.info(f"Created area_stat {stat.stat_id}")
        return stat


def aggregate_crop_map_to_stats(
    db: Session,
    crop_map_asset: Asset,
    period_start: datetime,
    period_end: datetime,
    admin_level: int = 1,
) -> List[AreaStat]:
    """
    Aggregate a crop map asset to area statistics by admin units.
    
    Args:
        db: Database session
        crop_map_asset: Asset record for the crop map
        period_start: Period start datetime
        period_end: Period end datetime
        admin_level: Admin level for aggregation
        
    Returns:
        List of created/updated AreaStat records
    """
    from app.core.spaces import get_spaces_client
    import tempfile
    from pathlib import Path
    
    # Download crop map from Spaces
    spaces = get_spaces_client()
    
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        spaces.download_file(crop_map_asset.s3_key, tmp_path)
        
        # Read the GeoTIFF
        data, metadata = read_geotiff(tmp_path)
        pred_map = data[0] if data.ndim == 3 else data
        bbox = tuple(metadata["bbox"])
        
        # Compute zonal stats by admin
        admin_stats = compute_zonal_stats_by_admin(
            db=db,
            pred_map=pred_map,
            bbox=bbox,
            admin_level=admin_level,
        )
        
        # Upsert stats to database
        created_stats = []
        for admin_id, stats_list in admin_stats.items():
            for stat in stats_list:
                area_stat = upsert_area_stats(
                    db=db,
                    admin_id=admin_id,
                    class_id=stat["class_id"],
                    period_start=period_start,
                    period_end=period_end,
                    area_ha=stat["area_ha"],
                    pixel_count=stat["pixel_count"],
                    source_asset_id=crop_map_asset.asset_id,
                )
                created_stats.append(area_stat)
        
        logger.info(f"Aggregated {len(created_stats)} area stats from asset {crop_map_asset.asset_id}")
        return created_stats
        
    finally:
        tmp_path.unlink(missing_ok=True)


def get_country_stats(
    db: Session,
    period_start: datetime,
    period_end: datetime,
) -> List[Dict[str, Any]]:
    """Get aggregated statistics for the entire country."""
    # Get country admin unit (level 0)
    country = db.query(AdminUnit).filter(AdminUnit.level == 0).first()
    
    if not country:
        # Aggregate from all provinces
        query = text("""
            SELECT 
                c.class_id,
                c.code,
                c.name_en,
                SUM(s.area_ha) as total_area_ha,
                SUM(s.pixel_count) as total_pixel_count
            FROM area_stats s
            JOIN crop_classes c ON s.class_id = c.class_id
            JOIN admin_units a ON s.admin_id = a.admin_id
            WHERE a.level = 1
            AND s.period_start = :period_start
            AND s.period_end = :period_end
            GROUP BY c.class_id, c.code, c.name_en
            ORDER BY total_area_ha DESC
        """)
    else:
        query = text("""
            SELECT 
                c.class_id,
                c.code,
                c.name_en,
                s.area_ha as total_area_ha,
                s.pixel_count as total_pixel_count
            FROM area_stats s
            JOIN crop_classes c ON s.class_id = c.class_id
            WHERE s.admin_id = :admin_id
            AND s.period_start = :period_start
            AND s.period_end = :period_end
            ORDER BY s.area_ha DESC
        """)
    
    params = {"period_start": period_start, "period_end": period_end}
    if country:
        params["admin_id"] = country.admin_id
    
    result = db.execute(query, params)
    rows = result.fetchall()
    
    return [
        {
            "class_id": row.class_id,
            "code": row.code,
            "name": row.name_en,
            "area_ha": float(row.total_area_ha),
            "pixel_count": int(row.total_pixel_count),
        }
        for row in rows
    ]


def get_province_stats(
    db: Session,
    province_name: str,
    period_start: datetime,
    period_end: datetime,
) -> List[Dict[str, Any]]:
    """Get aggregated statistics for a specific province."""
    # Find province by name
    province = db.query(AdminUnit).filter(
        AdminUnit.level == 1,
        AdminUnit.name.ilike(f"%{province_name}%"),
    ).first()
    
    if not province:
        logger.warning(f"Province not found: {province_name}")
        return []
    
    query = text("""
        SELECT 
            c.class_id,
            c.code,
            c.name_en,
            s.area_ha,
            s.pixel_count
        FROM area_stats s
        JOIN crop_classes c ON s.class_id = c.class_id
        WHERE s.admin_id = :admin_id
        AND s.period_start = :period_start
        AND s.period_end = :period_end
        ORDER BY s.area_ha DESC
    """)
    
    result = db.execute(query, {
        "admin_id": province.admin_id,
        "period_start": period_start,
        "period_end": period_end,
    })
    rows = result.fetchall()
    
    return [
        {
            "class_id": row.class_id,
            "code": row.code,
            "name": row.name_en,
            "area_ha": float(row.area_ha),
            "pixel_count": int(row.pixel_count),
        }
        for row in rows
    ]
