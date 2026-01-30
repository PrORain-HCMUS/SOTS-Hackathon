"""
Anomaly detection and alerts module.

Detects anomalies in vegetation indices (NDVI, NDWI, MSI) using
rule-based thresholds and rolling baseline comparison.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.models_sqlalchemy import Alert, AdminUnit, Asset
from app.core.time_utils import get_utc_now

logger = logging.getLogger(__name__)

# Alert severity levels
SEVERITY_LOW = 1
SEVERITY_MEDIUM = 2
SEVERITY_HIGH = 3

# Thresholds for anomaly detection
NDVI_THRESHOLD_LOW = 0.2  # Below this is concerning
NDVI_DROP_THRESHOLD = 0.15  # Drop from baseline
NDWI_THRESHOLD_HIGH = 0.3  # High water stress
MSI_THRESHOLD_HIGH = 1.5  # High moisture stress

# Rolling baseline window (weeks)
BASELINE_WINDOW_WEEKS = 8


def calculate_ndvi(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """
    Calculate Normalized Difference Vegetation Index.
    NDVI = (NIR - RED) / (NIR + RED)
    
    Args:
        nir: NIR band (B08) array
        red: RED band (B04) array
        
    Returns:
        NDVI array
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        ndvi = (nir - red) / (nir + red)
        ndvi = np.nan_to_num(ndvi, nan=0.0, posinf=0.0, neginf=0.0)
    return ndvi


def calculate_ndwi(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Calculate Normalized Difference Water Index.
    NDWI = (GREEN - NIR) / (GREEN + NIR)
    
    Args:
        green: GREEN band (B03) array
        nir: NIR band (B08) array
        
    Returns:
        NDWI array
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        ndwi = (green - nir) / (green + nir)
        ndwi = np.nan_to_num(ndwi, nan=0.0, posinf=0.0, neginf=0.0)
    return ndwi


def calculate_msi(swir: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Calculate Moisture Stress Index.
    MSI = SWIR / NIR
    
    Note: This requires SWIR band which may not be in our standard 4-band stack.
    For MVP, we'll use a simplified version or skip if SWIR not available.
    
    Args:
        swir: SWIR band array
        nir: NIR band (B08) array
        
    Returns:
        MSI array
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        msi = swir / nir
        msi = np.nan_to_num(msi, nan=0.0, posinf=0.0, neginf=0.0)
    return msi


def compute_mean_ndvi_from_stack(
    monthly_stack: np.ndarray,
) -> float:
    """
    Compute mean NDVI from a monthly stack.
    
    Args:
        monthly_stack: Array of shape (1, T, C, H, W) or (T, C, H, W)
                      where C=4 (B02, B03, B04, B08)
        
    Returns:
        Mean NDVI value
    """
    if monthly_stack.ndim == 5:
        monthly_stack = monthly_stack[0]  # Remove batch dim
    
    # Use last month for current NDVI
    last_month = monthly_stack[-1]  # (C, H, W)
    
    # B04 (RED) is index 2, B08 (NIR) is index 3
    red = last_month[2]
    nir = last_month[3]
    
    ndvi = calculate_ndvi(nir, red)
    return float(np.mean(ndvi))


def compute_rolling_baseline(
    db: Session,
    admin_id: UUID,
    current_date: datetime,
    window_weeks: int = BASELINE_WINDOW_WEEKS,
) -> Optional[Dict[str, float]]:
    """
    Compute rolling baseline statistics for an admin unit.
    
    This is a placeholder that would query historical index values.
    For MVP, returns None if no historical data.
    
    Args:
        db: Database session
        admin_id: Admin unit ID
        current_date: Current date
        window_weeks: Number of weeks for baseline
        
    Returns:
        Dict with baseline statistics or None
    """
    # Query historical alerts/stats for baseline
    start_date = current_date - timedelta(weeks=window_weeks)
    
    # For MVP, we don't have historical index storage
    # This would need an indices table or time-series storage
    logger.debug(f"Rolling baseline not implemented for admin {admin_id}")
    return None


def detect_ndvi_anomaly(
    current_ndvi: float,
    baseline_ndvi: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """
    Detect NDVI anomaly based on thresholds and baseline.
    
    Args:
        current_ndvi: Current NDVI value
        baseline_ndvi: Historical baseline NDVI (optional)
        
    Returns:
        Alert dict if anomaly detected, None otherwise
    """
    # Check absolute threshold
    if current_ndvi < NDVI_THRESHOLD_LOW:
        return {
            "alert_type": "low_ndvi",
            "severity": SEVERITY_HIGH if current_ndvi < 0.1 else SEVERITY_MEDIUM,
            "message": f"Low vegetation index detected: NDVI = {current_ndvi:.3f}",
            "evidence": {
                "current_ndvi": current_ndvi,
                "threshold": NDVI_THRESHOLD_LOW,
            },
        }
    
    # Check drop from baseline
    if baseline_ndvi is not None:
        drop = baseline_ndvi - current_ndvi
        if drop > NDVI_DROP_THRESHOLD:
            return {
                "alert_type": "ndvi_drop",
                "severity": SEVERITY_HIGH if drop > 0.25 else SEVERITY_MEDIUM,
                "message": f"Significant vegetation decline: NDVI dropped by {drop:.3f}",
                "evidence": {
                    "current_ndvi": current_ndvi,
                    "baseline_ndvi": baseline_ndvi,
                    "drop": drop,
                    "threshold": NDVI_DROP_THRESHOLD,
                },
            }
    
    return None


def detect_ndwi_anomaly(
    current_ndwi: float,
    baseline_ndwi: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """
    Detect NDWI anomaly (water stress).
    
    Args:
        current_ndwi: Current NDWI value
        baseline_ndwi: Historical baseline NDWI (optional)
        
    Returns:
        Alert dict if anomaly detected, None otherwise
    """
    # High NDWI might indicate flooding
    if current_ndwi > NDWI_THRESHOLD_HIGH:
        return {
            "alert_type": "high_ndwi",
            "severity": SEVERITY_MEDIUM,
            "message": f"High water index detected: NDWI = {current_ndwi:.3f}",
            "evidence": {
                "current_ndwi": current_ndwi,
                "threshold": NDWI_THRESHOLD_HIGH,
            },
        }
    
    return None


def create_alert(
    db: Session,
    alert_type: str,
    severity: int,
    message: str,
    evidence: Dict[str, Any],
    admin_id: Optional[UUID] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    source_asset_id: Optional[UUID] = None,
) -> Alert:
    """
    Create an alert record in the database.
    
    Args:
        db: Database session
        alert_type: Type of alert
        severity: Severity level (1-3)
        message: Human-readable message
        evidence: JSON evidence data
        admin_id: Optional admin unit ID
        period_start: Period start
        period_end: Period end
        source_asset_id: Source asset ID
        
    Returns:
        Created Alert record
    """
    alert = Alert(
        alert_type=alert_type,
        severity=severity,
        admin_id=admin_id,
        period_start=period_start,
        period_end=period_end,
        evidence=evidence,
        message=message,
        source_asset_id=source_asset_id,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    logger.info(f"Created alert {alert.alert_id}: {alert_type} (severity={severity})")
    return alert


def run_anomaly_detection(
    db: Session,
    monthly_stack: np.ndarray,
    admin_id: Optional[UUID] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    source_asset_id: Optional[UUID] = None,
) -> List[Alert]:
    """
    Run anomaly detection on a monthly stack and create alerts.
    
    Args:
        db: Database session
        monthly_stack: Input array of shape (1, T, C, H, W)
        admin_id: Optional admin unit ID
        period_start: Period start
        period_end: Period end
        source_asset_id: Source asset ID
        
    Returns:
        List of created Alert records
    """
    alerts = []
    
    # Compute current indices
    current_ndvi = compute_mean_ndvi_from_stack(monthly_stack)
    
    # Get baseline (if available)
    baseline = None
    if admin_id:
        baseline = compute_rolling_baseline(
            db, admin_id, period_end or get_utc_now()
        )
    
    baseline_ndvi = baseline.get("ndvi") if baseline else None
    
    # Check for NDVI anomaly
    ndvi_anomaly = detect_ndvi_anomaly(current_ndvi, baseline_ndvi)
    if ndvi_anomaly:
        alert = create_alert(
            db=db,
            alert_type=ndvi_anomaly["alert_type"],
            severity=ndvi_anomaly["severity"],
            message=ndvi_anomaly["message"],
            evidence=ndvi_anomaly["evidence"],
            admin_id=admin_id,
            period_start=period_start,
            period_end=period_end,
            source_asset_id=source_asset_id,
        )
        alerts.append(alert)
    
    # Compute NDWI from last month
    if monthly_stack.ndim == 5:
        last_month = monthly_stack[0, -1]
    else:
        last_month = monthly_stack[-1]
    
    green = last_month[1]  # B03
    nir = last_month[3]    # B08
    current_ndwi = float(np.mean(calculate_ndwi(green, nir)))
    
    # Check for NDWI anomaly
    ndwi_anomaly = detect_ndwi_anomaly(current_ndwi)
    if ndwi_anomaly:
        alert = create_alert(
            db=db,
            alert_type=ndwi_anomaly["alert_type"],
            severity=ndwi_anomaly["severity"],
            message=ndwi_anomaly["message"],
            evidence=ndwi_anomaly["evidence"],
            admin_id=admin_id,
            period_start=period_start,
            period_end=period_end,
            source_asset_id=source_asset_id,
        )
        alerts.append(alert)
    
    logger.info(f"Anomaly detection complete: {len(alerts)} alerts created")
    return alerts


def get_alerts(
    db: Session,
    admin_name: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    alert_type: Optional[str] = None,
    severity: Optional[int] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Query alerts with optional filters.
    
    Args:
        db: Database session
        admin_name: Filter by admin unit name (partial match)
        from_date: Filter alerts created after this date
        to_date: Filter alerts created before this date
        alert_type: Filter by alert type
        severity: Filter by severity level
        limit: Maximum number of results
        
    Returns:
        List of alert dictionaries
    """
    query = db.query(Alert)
    
    if admin_name:
        # Join with admin_units to filter by name
        admin = db.query(AdminUnit).filter(
            AdminUnit.name.ilike(f"%{admin_name}%")
        ).first()
        if admin:
            query = query.filter(Alert.admin_id == admin.admin_id)
    
    if from_date:
        query = query.filter(Alert.created_at >= from_date)
    
    if to_date:
        query = query.filter(Alert.created_at <= to_date)
    
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    query = query.order_by(Alert.created_at.desc()).limit(limit)
    
    alerts = query.all()
    
    return [
        {
            "alert_id": str(alert.alert_id),
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "evidence": alert.evidence,
            "period_start": alert.period_start.isoformat() if alert.period_start else None,
            "period_end": alert.period_end.isoformat() if alert.period_end else None,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        }
        for alert in alerts
    ]
