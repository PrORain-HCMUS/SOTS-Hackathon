"""
Health check API routes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db, check_db_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """
    Health check endpoint.
    
    Returns:
        Basic health status
    """
    return {
        "status": "ok",
        "service": "agripulse-backend",
    }


@router.get("/health/db")
def health_check_db(db: Session = Depends(get_db)):
    """
    Database health check.
    
    Returns:
        Database connection status
    """
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "database": "connected",
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e),
        }


@router.get("/health/full")
def health_check_full(db: Session = Depends(get_db)):
    """
    Full health check including all services.
    
    Returns:
        Status of all services
    """
    from app.core.config import get_settings
    
    settings = get_settings()
    
    # Check database
    db_ok = check_db_connection()
    
    # Check Redis
    redis_ok = False
    try:
        import redis
        r = redis.from_url(settings.redis_url)
        r.ping()
        redis_ok = True
    except Exception:
        pass
    
    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "services": {
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
        },
    }
