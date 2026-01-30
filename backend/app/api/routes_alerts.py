"""
Alerts API routes.
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.alerts import get_alerts

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertItem(BaseModel):
    """Alert item."""
    
    alert_id: str
    alert_type: str
    severity: int
    severity_label: str
    message: Optional[str] = None
    evidence: Optional[dict] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    created_at: Optional[str] = None


class AlertsResponse(BaseModel):
    """Alerts response."""
    
    count: int
    alerts: List[AlertItem]


def severity_to_label(severity: int) -> str:
    """Convert severity number to label."""
    labels = {1: "low", 2: "medium", 3: "high"}
    return labels.get(severity, "unknown")


@router.get("/", response_model=AlertsResponse)
def list_alerts(
    admin: Optional[str] = Query(None, description="Admin unit name filter"),
    from_date: Optional[str] = Query(None, alias="from", description="From date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, alias="to", description="To date (YYYY-MM-DD)"),
    alert_type: Optional[str] = Query(None, description="Alert type filter"),
    severity: Optional[int] = Query(None, ge=1, le=3, description="Severity filter (1-3)"),
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
):
    """
    Query alerts with optional filters.
    
    Args:
        admin: Filter by admin unit name (partial match)
        from_date: Filter alerts created after this date
        to_date: Filter alerts created before this date
        alert_type: Filter by alert type
        severity: Filter by severity level (1=low, 2=medium, 3=high)
        limit: Maximum number of results
    """
    # Parse dates
    from_dt = None
    to_dt = None
    
    if from_date:
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid from date format")
    
    if to_date:
        try:
            to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid to date format")
    
    # Get alerts
    alerts = get_alerts(
        db=db,
        admin_name=admin,
        from_date=from_dt,
        to_date=to_dt,
        alert_type=alert_type,
        severity=severity,
        limit=limit,
    )
    
    return AlertsResponse(
        count=len(alerts),
        alerts=[
            AlertItem(
                alert_id=a["alert_id"],
                alert_type=a["alert_type"],
                severity=a["severity"],
                severity_label=severity_to_label(a["severity"]),
                message=a["message"],
                evidence=a["evidence"],
                period_start=a["period_start"],
                period_end=a["period_end"],
                created_at=a["created_at"],
            )
            for a in alerts
        ],
    )


@router.get("/summary")
def get_alerts_summary(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to summarize"),
    db: Session = Depends(get_db),
):
    """
    Get summary of alerts for the last N days.
    
    Returns counts by type and severity.
    """
    from datetime import timedelta
    from sqlalchemy import func
    from app.core.models_sqlalchemy import Alert
    from app.core.time_utils import get_utc_now
    
    cutoff = get_utc_now() - timedelta(days=days)
    
    # Count by type
    type_counts = db.query(
        Alert.alert_type,
        func.count(Alert.alert_id).label("count"),
    ).filter(
        Alert.created_at >= cutoff
    ).group_by(Alert.alert_type).all()
    
    # Count by severity
    severity_counts = db.query(
        Alert.severity,
        func.count(Alert.alert_id).label("count"),
    ).filter(
        Alert.created_at >= cutoff
    ).group_by(Alert.severity).all()
    
    # Total count
    total = db.query(func.count(Alert.alert_id)).filter(
        Alert.created_at >= cutoff
    ).scalar()
    
    return {
        "period_days": days,
        "total_alerts": total or 0,
        "by_type": {t: c for t, c in type_counts},
        "by_severity": {
            severity_to_label(s): c for s, c in severity_counts
        },
    }


@router.get("/{alert_id}")
def get_alert_detail(
    alert_id: str,
    db: Session = Depends(get_db),
):
    """Get detailed information about a specific alert."""
    from uuid import UUID
    from app.core.models_sqlalchemy import Alert, AdminUnit
    
    try:
        alert_uuid = UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert ID format")
    
    alert = db.query(Alert).filter(Alert.alert_id == alert_uuid).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Get admin unit name if available
    admin_name = None
    if alert.admin_id:
        admin = db.query(AdminUnit).filter(
            AdminUnit.admin_id == alert.admin_id
        ).first()
        if admin:
            admin_name = admin.name
    
    return {
        "alert_id": str(alert.alert_id),
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "severity_label": severity_to_label(alert.severity),
        "message": alert.message,
        "evidence": alert.evidence,
        "admin_name": admin_name,
        "period_start": alert.period_start.isoformat() if alert.period_start else None,
        "period_end": alert.period_end.isoformat() if alert.period_end else None,
        "source_asset_id": str(alert.source_asset_id) if alert.source_asset_id else None,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }
