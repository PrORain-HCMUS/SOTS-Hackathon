"""
SQLAlchemy ORM models for AgriPulse database.
"""

import uuid
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    BigInteger,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.db import Base


class Tile(Base):
    """Sentinel-2 tile grid for Vietnam."""

    __tablename__ = "tiles"

    tile_id = Column(String(10), primary_key=True)
    geom = Column(Geometry("POLYGON", srid=4326), nullable=False)
    last_seen_sensing_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    scenes = relationship("Scene", back_populates="tile")
    assets = relationship("Asset", back_populates="tile")

    __table_args__ = (
        Index("idx_tiles_geom", "geom", postgresql_using="gist"),
    )


class Scene(Base):
    """Discovered Sentinel-2 scenes."""

    __tablename__ = "scenes"

    scene_id = Column(String(255), primary_key=True)
    provider = Column(String(50), nullable=False, default="sentinel-hub")
    collection = Column(String(50), nullable=False, default="sentinel-2-l2a")
    tile_id = Column(String(10), ForeignKey("tiles.tile_id"), nullable=True)
    sensing_time = Column(DateTime(timezone=True), nullable=False)
    cloud_cover = Column(Float, nullable=True)
    footprint = Column(Geometry("POLYGON", srid=4326), nullable=True)
    source_url = Column(Text, nullable=True)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="discovered")

    tile = relationship("Tile", back_populates="scenes")

    __table_args__ = (
        Index("idx_scenes_footprint", "footprint", postgresql_using="gist"),
        Index("idx_scenes_sensing_time", "sensing_time"),
        Index("idx_scenes_tile_id", "tile_id"),
    )


class Asset(Base):
    """Stored assets (raw, processed, predictions) in Spaces."""

    __tablename__ = "assets"

    asset_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    asset_type = Column(String(100), nullable=False)
    scene_id = Column(String(255), ForeignKey("scenes.scene_id"), nullable=True)
    tile_id = Column(String(10), ForeignKey("tiles.tile_id"), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    sensing_time = Column(DateTime(timezone=True), nullable=True)
    resolution_m = Column(Integer, nullable=True)
    bands = Column(JSONB, nullable=True)
    crs = Column(String(50), nullable=True)
    bbox = Column(JSONB, nullable=True)
    s3_bucket = Column(String(255), nullable=False)
    s3_key = Column(String(1024), nullable=False)
    etag = Column(String(255), nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tile = relationship("Tile", back_populates="assets")

    __table_args__ = (
        UniqueConstraint(
            "asset_type", "tile_id", "period_start", "period_end",
            name="uq_asset_type_tile_period"
        ),
        Index("idx_assets_tile_id", "tile_id"),
        Index("idx_assets_asset_type", "asset_type"),
    )


class Model(Base):
    """Registered ML models."""

    __tablename__ = "models"

    model_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name = Column(String(255), nullable=False)
    task = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    weights_s3_key = Column(String(1024), nullable=False)
    input_spec = Column(JSONB, nullable=True)
    output_spec = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    inference_runs = relationship("InferenceRun", back_populates="model")

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_name_version"),
    )


class InferenceRun(Base):
    """Inference run records."""

    __tablename__ = "inference_runs"

    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(
        UUID(as_uuid=True), ForeignKey("models.model_id"), nullable=False
    )
    input_asset_id = Column(
        UUID(as_uuid=True), ForeignKey("assets.asset_id"), nullable=True
    )
    output_asset_id = Column(
        UUID(as_uuid=True), ForeignKey("assets.asset_id"), nullable=True
    )
    status = Column(String(50), default="pending")
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    metrics = Column(JSONB, nullable=True)

    model = relationship("Model", back_populates="inference_runs")


class CropClass(Base):
    """Crop classification classes."""

    __tablename__ = "crop_classes"

    class_id = Column(SmallInteger, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name_vi = Column(String(255), nullable=True)
    name_en = Column(String(255), nullable=True)
    is_food_crop = Column(Boolean, default=False)
    color_hex = Column(String(7), nullable=True)

    area_stats = relationship("AreaStat", back_populates="crop_class")


class AdminUnit(Base):
    """Administrative units (country, province, district)."""

    __tablename__ = "admin_units"

    admin_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(SmallInteger, nullable=False)  # 0=country, 1=province, 2=district
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    parent_admin_id = Column(
        UUID(as_uuid=True), ForeignKey("admin_units.admin_id"), nullable=True
    )
    geom = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)

    parent = relationship("AdminUnit", remote_side=[admin_id], backref="children")
    area_stats = relationship("AreaStat", back_populates="admin_unit")
    alerts = relationship("Alert", back_populates="admin_unit")

    __table_args__ = (
        Index("idx_admin_units_geom", "geom", postgresql_using="gist"),
        Index("idx_admin_units_level", "level"),
    )


class AreaStat(Base):
    """Aggregated crop area statistics by admin unit."""

    __tablename__ = "area_stats"

    stat_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = Column(
        UUID(as_uuid=True), ForeignKey("admin_units.admin_id"), nullable=False
    )
    class_id = Column(
        SmallInteger, ForeignKey("crop_classes.class_id"), nullable=False
    )
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    area_ha = Column(Float, nullable=False)
    pixel_count = Column(BigInteger, nullable=False)
    confidence_low = Column(Float, nullable=True)
    confidence_high = Column(Float, nullable=True)
    source_asset_id = Column(
        UUID(as_uuid=True), ForeignKey("assets.asset_id"), nullable=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin_unit = relationship("AdminUnit", back_populates="area_stats")
    crop_class = relationship("CropClass", back_populates="area_stats")

    __table_args__ = (
        UniqueConstraint(
            "admin_id", "class_id", "period_start", "period_end",
            name="uq_area_stats_admin_class_period"
        ),
    )


class Alert(Base):
    """Anomaly alerts."""

    __tablename__ = "alerts"

    alert_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(String(100), nullable=False)
    severity = Column(SmallInteger, nullable=False)  # 1=low, 2=medium, 3=high
    admin_id = Column(
        UUID(as_uuid=True), ForeignKey("admin_units.admin_id"), nullable=True
    )
    geom = Column(Geometry("GEOMETRY", srid=4326), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    evidence = Column(JSONB, nullable=True)
    message = Column(Text, nullable=True)
    source_asset_id = Column(
        UUID(as_uuid=True), ForeignKey("assets.asset_id"), nullable=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin_unit = relationship("AdminUnit", back_populates="alerts")

    __table_args__ = (
        Index("idx_alerts_geom", "geom", postgresql_using="gist"),
        Index("idx_alerts_created_at", "created_at"),
    )


class Job(Base):
    """Background job tracking."""

    __tablename__ = "jobs"

    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(100), nullable=False)
    tile_id = Column(String(10), ForeignKey("tiles.tile_id"), nullable=True)
    scene_id = Column(String(255), ForeignKey("scenes.scene_id"), nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="pending")
    payload = Column(JSONB, nullable=True)
    log = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_job_type", "job_type"),
    )
