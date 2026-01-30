"""
CRUD operations for database models.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.dialects.postgresql import insert

from app.core.models_sqlalchemy import (
    Tile, Scene, Asset, Model, InferenceRun, Job,
    CropClass, AdminUnit, AreaStat, Alert
)
from app.core.time_utils import get_utc_now

logger = logging.getLogger(__name__)


# ============== Tiles ==============

def get_tile(db: Session, tile_id: str) -> Optional[Tile]:
    """Get a tile by ID."""
    return db.query(Tile).filter(Tile.tile_id == tile_id).first()


def get_tiles(db: Session, limit: int = 100) -> List[Tile]:
    """Get all tiles."""
    return db.query(Tile).limit(limit).all()


def create_tile(
    db: Session,
    tile_id: str,
    geom_wkt: str,
) -> Tile:
    """Create a new tile."""
    from geoalchemy2 import WKTElement
    
    tile = Tile(
        tile_id=tile_id,
        geom=WKTElement(geom_wkt, srid=4326),
    )
    db.add(tile)
    db.commit()
    db.refresh(tile)
    return tile


def update_tile_sensing_time(
    db: Session,
    tile_id: str,
    sensing_time: datetime,
) -> Optional[Tile]:
    """Update tile's last seen sensing time."""
    tile = get_tile(db, tile_id)
    if tile:
        tile.last_seen_sensing_time = sensing_time
        db.commit()
        db.refresh(tile)
    return tile


# ============== Scenes ==============

def get_scene(db: Session, scene_id: str) -> Optional[Scene]:
    """Get a scene by ID."""
    return db.query(Scene).filter(Scene.scene_id == scene_id).first()


def scene_exists(db: Session, scene_id: str) -> bool:
    """Check if a scene already exists (idempotent ingestion)."""
    return db.query(Scene).filter(Scene.scene_id == scene_id).first() is not None


def create_scene(
    db: Session,
    scene_id: str,
    sensing_time: datetime,
    tile_id: Optional[str] = None,
    cloud_cover: Optional[float] = None,
    footprint_wkt: Optional[str] = None,
    provider: str = "sentinel-hub",
    collection: str = "sentinel-2-l2a",
    source_url: Optional[str] = None,
    status: str = "discovered",
) -> Scene:
    """Create a new scene record."""
    from geoalchemy2 import WKTElement
    
    scene = Scene(
        scene_id=scene_id,
        provider=provider,
        collection=collection,
        tile_id=tile_id,
        sensing_time=sensing_time,
        cloud_cover=cloud_cover,
        footprint=WKTElement(footprint_wkt, srid=4326) if footprint_wkt else None,
        source_url=source_url,
        status=status,
    )
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return scene


def upsert_scene(
    db: Session,
    scene_id: str,
    sensing_time: datetime,
    **kwargs,
) -> Tuple[Scene, bool]:
    """
    Insert or update a scene (idempotent).
    
    Returns:
        Tuple of (scene, created) where created is True if new record
    """
    existing = get_scene(db, scene_id)
    if existing:
        # Update existing
        for key, value in kwargs.items():
            if hasattr(existing, key) and value is not None:
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing, False
    else:
        scene = create_scene(db, scene_id, sensing_time, **kwargs)
        return scene, True


# ============== Assets ==============

def get_asset(db: Session, asset_id: UUID) -> Optional[Asset]:
    """Get an asset by ID."""
    return db.query(Asset).filter(Asset.asset_id == asset_id).first()


def get_asset_by_type_tile_period(
    db: Session,
    asset_type: str,
    tile_id: str,
    period_start: datetime,
    period_end: datetime,
) -> Optional[Asset]:
    """Get asset by unique constraint fields."""
    return db.query(Asset).filter(
        Asset.asset_type == asset_type,
        Asset.tile_id == tile_id,
        Asset.period_start == period_start,
        Asset.period_end == period_end,
    ).first()


def asset_exists(
    db: Session,
    asset_type: str,
    tile_id: str,
    period_start: datetime,
    period_end: datetime,
) -> bool:
    """Check if asset already exists (idempotent)."""
    return get_asset_by_type_tile_period(
        db, asset_type, tile_id, period_start, period_end
    ) is not None


def create_asset(
    db: Session,
    asset_type: str,
    s3_bucket: str,
    s3_key: str,
    tile_id: Optional[str] = None,
    scene_id: Optional[str] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    sensing_time: Optional[datetime] = None,
    resolution_m: Optional[int] = None,
    bands: Optional[List[str]] = None,
    crs: Optional[str] = None,
    bbox: Optional[List[float]] = None,
    etag: Optional[str] = None,
    size_bytes: Optional[int] = None,
) -> Asset:
    """Create a new asset record."""
    asset = Asset(
        asset_type=asset_type,
        scene_id=scene_id,
        tile_id=tile_id,
        period_start=period_start,
        period_end=period_end,
        sensing_time=sensing_time,
        resolution_m=resolution_m,
        bands=bands,
        crs=crs,
        bbox=bbox,
        s3_bucket=s3_bucket,
        s3_key=s3_key,
        etag=etag,
        size_bytes=size_bytes,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def upsert_asset(
    db: Session,
    asset_type: str,
    tile_id: str,
    period_start: datetime,
    period_end: datetime,
    s3_bucket: str,
    s3_key: str,
    **kwargs,
) -> Tuple[Asset, bool]:
    """
    Insert or update an asset (idempotent).
    
    Returns:
        Tuple of (asset, created) where created is True if new record
    """
    existing = get_asset_by_type_tile_period(
        db, asset_type, tile_id, period_start, period_end
    )
    
    if existing:
        # Update existing
        existing.s3_bucket = s3_bucket
        existing.s3_key = s3_key
        for key, value in kwargs.items():
            if hasattr(existing, key) and value is not None:
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing, False
    else:
        asset = create_asset(
            db=db,
            asset_type=asset_type,
            tile_id=tile_id,
            period_start=period_start,
            period_end=period_end,
            s3_bucket=s3_bucket,
            s3_key=s3_key,
            **kwargs,
        )
        return asset, True


# ============== Models ==============

def get_model(db: Session, model_id: UUID) -> Optional[Model]:
    """Get a model by ID."""
    return db.query(Model).filter(Model.model_id == model_id).first()


def get_model_by_name_version(
    db: Session,
    name: str,
    version: str,
) -> Optional[Model]:
    """Get model by name and version."""
    return db.query(Model).filter(
        Model.name == name,
        Model.version == version,
    ).first()


def get_model_by_task(
    db: Session,
    task: str,
    name: Optional[str] = None,
) -> Optional[Model]:
    """Get latest model for a task."""
    query = db.query(Model).filter(Model.task == task)
    if name:
        query = query.filter(Model.name == name)
    return query.order_by(Model.created_at.desc()).first()


def create_model(
    db: Session,
    name: str,
    task: str,
    version: str,
    weights_s3_key: str,
    input_spec: Optional[Dict] = None,
    output_spec: Optional[Dict] = None,
) -> Model:
    """Create a new model record."""
    model = Model(
        name=name,
        task=task,
        version=version,
        weights_s3_key=weights_s3_key,
        input_spec=input_spec,
        output_spec=output_spec,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


# ============== Inference Runs ==============

def create_inference_run(
    db: Session,
    model_id: UUID,
    input_asset_id: Optional[UUID] = None,
    status: str = "pending",
) -> InferenceRun:
    """Create a new inference run record."""
    run = InferenceRun(
        model_id=model_id,
        input_asset_id=input_asset_id,
        status=status,
        started_at=get_utc_now(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def update_inference_run(
    db: Session,
    run_id: UUID,
    status: Optional[str] = None,
    output_asset_id: Optional[UUID] = None,
    metrics: Optional[Dict] = None,
    finished: bool = False,
) -> Optional[InferenceRun]:
    """Update an inference run."""
    run = db.query(InferenceRun).filter(InferenceRun.run_id == run_id).first()
    if run:
        if status:
            run.status = status
        if output_asset_id:
            run.output_asset_id = output_asset_id
        if metrics:
            run.metrics = metrics
        if finished:
            run.finished_at = get_utc_now()
        db.commit()
        db.refresh(run)
    return run


# ============== Jobs ==============

def get_job(db: Session, job_id: UUID) -> Optional[Job]:
    """Get a job by ID."""
    return db.query(Job).filter(Job.job_id == job_id).first()


def create_job(
    db: Session,
    job_type: str,
    tile_id: Optional[str] = None,
    scene_id: Optional[str] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    payload: Optional[Dict] = None,
    status: str = "pending",
) -> Job:
    """Create a new job record."""
    job = Job(
        job_type=job_type,
        tile_id=tile_id,
        scene_id=scene_id,
        period_start=period_start,
        period_end=period_end,
        payload=payload,
        status=status,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_job(
    db: Session,
    job_id: UUID,
    status: Optional[str] = None,
    log: Optional[str] = None,
    started: bool = False,
    finished: bool = False,
) -> Optional[Job]:
    """Update a job."""
    job = get_job(db, job_id)
    if job:
        if status:
            job.status = status
        if log:
            job.log = (job.log or "") + log + "\n"
        if started:
            job.started_at = get_utc_now()
        if finished:
            job.finished_at = get_utc_now()
        db.commit()
        db.refresh(job)
    return job


def get_pending_jobs(
    db: Session,
    job_type: Optional[str] = None,
    limit: int = 10,
) -> List[Job]:
    """Get pending jobs."""
    query = db.query(Job).filter(Job.status == "pending")
    if job_type:
        query = query.filter(Job.job_type == job_type)
    return query.order_by(Job.created_at).limit(limit).all()


# ============== Admin Units ==============

def get_admin_unit(db: Session, admin_id: UUID) -> Optional[AdminUnit]:
    """Get admin unit by ID."""
    return db.query(AdminUnit).filter(AdminUnit.admin_id == admin_id).first()


def get_admin_units_by_level(db: Session, level: int) -> List[AdminUnit]:
    """Get all admin units at a given level."""
    return db.query(AdminUnit).filter(AdminUnit.level == level).all()


def get_admin_unit_by_name(
    db: Session,
    name: str,
    level: Optional[int] = None,
) -> Optional[AdminUnit]:
    """Get admin unit by name (partial match)."""
    query = db.query(AdminUnit).filter(AdminUnit.name.ilike(f"%{name}%"))
    if level is not None:
        query = query.filter(AdminUnit.level == level)
    return query.first()


def create_admin_unit(
    db: Session,
    name: str,
    level: int,
    code: Optional[str] = None,
    parent_admin_id: Optional[UUID] = None,
    geom_wkt: Optional[str] = None,
) -> AdminUnit:
    """Create a new admin unit."""
    from geoalchemy2 import WKTElement
    
    admin = AdminUnit(
        name=name,
        level=level,
        code=code,
        parent_admin_id=parent_admin_id,
        geom=WKTElement(geom_wkt, srid=4326) if geom_wkt else None,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


# ============== Crop Classes ==============

def get_crop_class(db: Session, class_id: int) -> Optional[CropClass]:
    """Get crop class by ID."""
    return db.query(CropClass).filter(CropClass.class_id == class_id).first()


def get_all_crop_classes(db: Session) -> List[CropClass]:
    """Get all crop classes."""
    return db.query(CropClass).order_by(CropClass.class_id).all()
