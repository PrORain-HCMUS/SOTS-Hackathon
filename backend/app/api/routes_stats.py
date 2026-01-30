"""
Statistics API routes.
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.aggregation import get_country_stats, get_province_stats
from app.core.time_utils import get_week_range, get_month_range

router = APIRouter(prefix="/stats", tags=["stats"])


class CropStatItem(BaseModel):
    """Single crop statistic item."""
    
    class_id: int
    code: str
    name: str
    area_ha: float
    pixel_count: int


class StatsResponse(BaseModel):
    """Statistics response."""
    
    period: str
    period_start: str
    period_end: str
    admin_level: str
    admin_name: Optional[str] = None
    stats: List[CropStatItem]
    total_area_ha: float


def parse_date(date_str: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date format. Use YYYY-MM-DD",
        )


@router.get("/country", response_model=StatsResponse)
def get_country_statistics(
    period: str = Query(
        default="weekly",
        description="Period type: weekly or monthly",
        regex="^(weekly|monthly)$",
    ),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
):
    """
    Get country-level crop statistics.
    
    Args:
        period: Period type (weekly or monthly)
        date: Date within the period
    """
    target_date = parse_date(date)
    
    # Calculate period bounds
    if period == "weekly":
        period_start, period_end = get_week_range(target_date)
    else:
        period_start, period_end = get_month_range(target_date.year, target_date.month)
    
    # Get stats from database
    stats = get_country_stats(db, period_start, period_end)
    
    if not stats:
        return StatsResponse(
            period=period,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            admin_level="country",
            admin_name="Vietnam",
            stats=[],
            total_area_ha=0.0,
        )
    
    total_area = sum(s["area_ha"] for s in stats)
    
    return StatsResponse(
        period=period,
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        admin_level="country",
        admin_name="Vietnam",
        stats=[
            CropStatItem(
                class_id=s["class_id"],
                code=s["code"],
                name=s["name"],
                area_ha=s["area_ha"],
                pixel_count=s["pixel_count"],
            )
            for s in stats
        ],
        total_area_ha=total_area,
    )


@router.get("/province", response_model=StatsResponse)
def get_province_statistics(
    name: str = Query(..., description="Province name (partial match)"),
    period: str = Query(
        default="weekly",
        description="Period type: weekly or monthly",
        regex="^(weekly|monthly)$",
    ),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
):
    """
    Get province-level crop statistics.
    
    Args:
        name: Province name (partial match supported)
        period: Period type (weekly or monthly)
        date: Date within the period
    """
    target_date = parse_date(date)
    
    if period == "weekly":
        period_start, period_end = get_week_range(target_date)
    else:
        period_start, period_end = get_month_range(target_date.year, target_date.month)
    
    stats = get_province_stats(db, name, period_start, period_end)
    
    if not stats:
        return StatsResponse(
            period=period,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            admin_level="province",
            admin_name=name,
            stats=[],
            total_area_ha=0.0,
        )
    
    total_area = sum(s["area_ha"] for s in stats)
    
    return StatsResponse(
        period=period,
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        admin_level="province",
        admin_name=name,
        stats=[
            CropStatItem(
                class_id=s["class_id"],
                code=s["code"],
                name=s["name"],
                area_ha=s["area_ha"],
                pixel_count=s["pixel_count"],
            )
            for s in stats
        ],
        total_area_ha=total_area,
    )


@router.get("/district", response_model=StatsResponse)
def get_district_statistics(
    name: str = Query(..., description="District name"),
    province: Optional[str] = Query(None, description="Province name for disambiguation"),
    period: str = Query(default="weekly"),
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
):
    """
    Get district-level crop statistics.
    
    Args:
        name: District name
        province: Optional province name for disambiguation
        period: Period type
        date: Date within the period
    """
    from app.core.models_sqlalchemy import AdminUnit, AreaStat, CropClass
    
    target_date = parse_date(date)
    
    if period == "weekly":
        period_start, period_end = get_week_range(target_date)
    else:
        period_start, period_end = get_month_range(target_date.year, target_date.month)
    
    # Find district
    query = db.query(AdminUnit).filter(
        AdminUnit.level == 2,
        AdminUnit.name.ilike(f"%{name}%"),
    )
    
    if province:
        # Find parent province first
        parent = db.query(AdminUnit).filter(
            AdminUnit.level == 1,
            AdminUnit.name.ilike(f"%{province}%"),
        ).first()
        if parent:
            query = query.filter(AdminUnit.parent_admin_id == parent.admin_id)
    
    district = query.first()
    
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    
    # Get stats
    stats_query = db.query(
        AreaStat.class_id,
        CropClass.code,
        CropClass.name_en,
        AreaStat.area_ha,
        AreaStat.pixel_count,
    ).join(CropClass).filter(
        AreaStat.admin_id == district.admin_id,
        AreaStat.period_start == period_start,
        AreaStat.period_end == period_end,
    ).order_by(AreaStat.area_ha.desc())
    
    results = stats_query.all()
    
    stats = [
        CropStatItem(
            class_id=r.class_id,
            code=r.code,
            name=r.name_en,
            area_ha=r.area_ha,
            pixel_count=r.pixel_count,
        )
        for r in results
    ]
    
    total_area = sum(s.area_ha for s in stats)
    
    return StatsResponse(
        period=period,
        period_start=period_start.isoformat(),
        period_end=period_end.isoformat(),
        admin_level="district",
        admin_name=district.name,
        stats=stats,
        total_area_ha=total_area,
    )
