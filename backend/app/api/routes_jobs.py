"""
Job management API routes.
"""

from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.crud import create_job, get_job, get_pending_jobs, update_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


class TriggerJobRequest(BaseModel):
    """Request to trigger a pipeline job."""
    
    tile_id: Optional[str] = Field(None, description="Tile ID to process")
    bbox: Optional[List[float]] = Field(
        None,
        description="Bounding box [min_lon, min_lat, max_lon, max_lat]",
        min_length=4,
        max_length=4,
    )
    end_year: int = Field(..., description="End year for processing")
    end_month: int = Field(..., ge=1, le=12, description="End month (1-12)")
    window_len: int = Field(default=6, ge=1, le=12, description="Number of months")
    run_inference: bool = Field(default=True, description="Run S4A inference")
    run_aggregation: bool = Field(default=True, description="Run aggregation")
    run_alerts: bool = Field(default=True, description="Run anomaly detection")


class JobResponse(BaseModel):
    """Job response."""
    
    job_id: str
    job_type: str
    status: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class TriggerJobResponse(BaseModel):
    """Response after triggering a job."""
    
    job_id: str
    status: str
    message: str


@router.post("/trigger", response_model=TriggerJobResponse)
def trigger_pipeline(
    request: TriggerJobRequest,
    db: Session = Depends(get_db),
):
    """
    Trigger a processing pipeline for a tile or bbox.
    
    This will:
    1. Preprocess monthly stack from Sentinel Hub
    2. Run S4A inference (if enabled)
    3. Aggregate statistics (if enabled)
    4. Run anomaly detection (if enabled)
    """
    if not request.tile_id and not request.bbox:
        raise HTTPException(
            status_code=400,
            detail="Either tile_id or bbox must be provided",
        )
    
    # Create job record
    job = create_job(
        db=db,
        job_type="full_pipeline",
        tile_id=request.tile_id,
        payload={
            "tile_id": request.tile_id,
            "bbox": request.bbox,
            "end_year": request.end_year,
            "end_month": request.end_month,
            "window_len": request.window_len,
            "run_inference": request.run_inference,
            "run_aggregation": request.run_aggregation,
            "run_alerts": request.run_alerts,
        },
        status="pending",
    )
    
    # Queue the Celery task
    from app.workers.tasks_preprocess import preprocess_monthly_stack
    from app.workers.tasks_infer import run_s4a_inference
    
    if request.tile_id:
        # Chain tasks: preprocess -> inference -> aggregate -> alerts
        preprocess_monthly_stack.delay(
            tile_id=request.tile_id,
            end_year=request.end_year,
            end_month=request.end_month,
            window_len=request.window_len,
        )
        
        if request.run_inference:
            run_s4a_inference.delay(
                tile_id=request.tile_id,
                end_year=request.end_year,
                end_month=request.end_month,
                window_len=request.window_len,
            )
    elif request.bbox:
        from app.workers.tasks_infer import run_s4a_on_bbox_task
        
        run_s4a_on_bbox_task.delay(
            bbox=tuple(request.bbox),
            end_year=request.end_year,
            end_month=request.end_month,
            window_len=request.window_len,
        )
    
    # Update job status
    update_job(db, job.job_id, status="queued", started=True)
    
    return TriggerJobResponse(
        job_id=str(job.job_id),
        status="queued",
        message="Pipeline job queued successfully",
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
):
    """Get job status by ID."""
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")
    
    job = get_job(db, job_uuid)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(
        job_id=str(job.job_id),
        job_type=job.job_type,
        status=job.status,
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
    )


@router.get("/", response_model=List[JobResponse])
def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """List jobs with optional filters."""
    from app.core.models_sqlalchemy import Job
    
    query = db.query(Job)
    
    if status:
        query = query.filter(Job.status == status)
    if job_type:
        query = query.filter(Job.job_type == job_type)
    
    jobs = query.order_by(Job.created_at.desc()).limit(limit).all()
    
    return [
        JobResponse(
            job_id=str(job.job_id),
            job_type=job.job_type,
            status=job.status,
            created_at=job.created_at.isoformat() if job.created_at else None,
            started_at=job.started_at.isoformat() if job.started_at else None,
            finished_at=job.finished_at.isoformat() if job.finished_at else None,
        )
        for job in jobs
    ]
