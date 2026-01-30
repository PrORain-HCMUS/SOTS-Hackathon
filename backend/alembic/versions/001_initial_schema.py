"""Initial schema with PostGIS tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-01-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis')
    
    # Create tiles table
    op.create_table(
        'tiles',
        sa.Column('tile_id', sa.String(10), primary_key=True),
        sa.Column('geom', geoalchemy2.Geometry('POLYGON', srid=4326), nullable=False),
        sa.Column('last_seen_sensing_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_tiles_geom', 'tiles', ['geom'], postgresql_using='gist')
    
    # Create scenes table
    op.create_table(
        'scenes',
        sa.Column('scene_id', sa.String(255), primary_key=True),
        sa.Column('provider', sa.String(50), nullable=False, server_default='sentinel-hub'),
        sa.Column('collection', sa.String(50), nullable=False, server_default='sentinel-2-l2a'),
        sa.Column('tile_id', sa.String(10), sa.ForeignKey('tiles.tile_id'), nullable=True),
        sa.Column('sensing_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cloud_cover', sa.Float, nullable=True),
        sa.Column('footprint', geoalchemy2.Geometry('POLYGON', srid=4326), nullable=True),
        sa.Column('source_url', sa.Text, nullable=True),
        sa.Column('ingested_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('status', sa.String(50), server_default='discovered'),
    )
    op.create_index('idx_scenes_footprint', 'scenes', ['footprint'], postgresql_using='gist')
    op.create_index('idx_scenes_sensing_time', 'scenes', ['sensing_time'])
    op.create_index('idx_scenes_tile_id', 'scenes', ['tile_id'])
    
    # Create assets table
    op.create_table(
        'assets',
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_type', sa.String(100), nullable=False),
        sa.Column('scene_id', sa.String(255), sa.ForeignKey('scenes.scene_id'), nullable=True),
        sa.Column('tile_id', sa.String(10), sa.ForeignKey('tiles.tile_id'), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sensing_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_m', sa.Integer, nullable=True),
        sa.Column('bands', postgresql.JSONB, nullable=True),
        sa.Column('crs', sa.String(50), nullable=True),
        sa.Column('bbox', postgresql.JSONB, nullable=True),
        sa.Column('s3_bucket', sa.String(255), nullable=False),
        sa.Column('s3_key', sa.String(1024), nullable=False),
        sa.Column('etag', sa.String(255), nullable=True),
        sa.Column('size_bytes', sa.BigInteger, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_assets_tile_id', 'assets', ['tile_id'])
    op.create_index('idx_assets_asset_type', 'assets', ['asset_type'])
    op.create_unique_constraint(
        'uq_asset_type_tile_period', 'assets',
        ['asset_type', 'tile_id', 'period_start', 'period_end']
    )
    
    # Create models table
    op.create_table(
        'models',
        sa.Column('model_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('task', sa.String(100), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('weights_s3_key', sa.String(1024), nullable=False),
        sa.Column('input_spec', postgresql.JSONB, nullable=True),
        sa.Column('output_spec', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint('uq_model_name_version', 'models', ['name', 'version'])
    
    # Create inference_runs table
    op.create_table(
        'inference_runs',
        sa.Column('run_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('models.model_id'), nullable=False),
        sa.Column('input_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.asset_id'), nullable=True),
        sa.Column('output_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.asset_id'), nullable=True),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metrics', postgresql.JSONB, nullable=True),
    )
    
    # Create crop_classes table
    op.create_table(
        'crop_classes',
        sa.Column('class_id', sa.SmallInteger, primary_key=True),
        sa.Column('code', sa.String(50), unique=True, nullable=False),
        sa.Column('name_vi', sa.String(255), nullable=True),
        sa.Column('name_en', sa.String(255), nullable=True),
        sa.Column('is_food_crop', sa.Boolean, server_default='false'),
        sa.Column('color_hex', sa.String(7), nullable=True),
    )
    
    # Create admin_units table
    op.create_table(
        'admin_units',
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('level', sa.SmallInteger, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('code', sa.String(50), nullable=True),
        sa.Column('parent_admin_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('admin_units.admin_id'), nullable=True),
        sa.Column('geom', geoalchemy2.Geometry('MULTIPOLYGON', srid=4326), nullable=True),
    )
    op.create_index('idx_admin_units_geom', 'admin_units', ['geom'], postgresql_using='gist')
    op.create_index('idx_admin_units_level', 'admin_units', ['level'])
    
    # Create area_stats table
    op.create_table(
        'area_stats',
        sa.Column('stat_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('admin_units.admin_id'), nullable=False),
        sa.Column('class_id', sa.SmallInteger, sa.ForeignKey('crop_classes.class_id'), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('area_ha', sa.Float, nullable=False),
        sa.Column('pixel_count', sa.BigInteger, nullable=False),
        sa.Column('confidence_low', sa.Float, nullable=True),
        sa.Column('confidence_high', sa.Float, nullable=True),
        sa.Column('source_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.asset_id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_unique_constraint(
        'uq_area_stats_admin_class_period', 'area_stats',
        ['admin_id', 'class_id', 'period_start', 'period_end']
    )
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('alert_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('alert_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.SmallInteger, nullable=False),
        sa.Column('admin_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('admin_units.admin_id'), nullable=True),
        sa.Column('geom', geoalchemy2.Geometry('GEOMETRY', srid=4326), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('evidence', postgresql.JSONB, nullable=True),
        sa.Column('message', sa.Text, nullable=True),
        sa.Column('source_asset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assets.asset_id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_alerts_geom', 'alerts', ['geom'], postgresql_using='gist')
    op.create_index('idx_alerts_created_at', 'alerts', ['created_at'])
    
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('job_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('job_type', sa.String(100), nullable=False),
        sa.Column('tile_id', sa.String(10), sa.ForeignKey('tiles.tile_id'), nullable=True),
        sa.Column('scene_id', sa.String(255), sa.ForeignKey('scenes.scene_id'), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('payload', postgresql.JSONB, nullable=True),
        sa.Column('log', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_jobs_status', 'jobs', ['status'])
    op.create_index('idx_jobs_job_type', 'jobs', ['job_type'])
    
    # Insert default crop classes
    op.execute("""
        INSERT INTO crop_classes (class_id, code, name_vi, name_en, is_food_crop, color_hex) VALUES
        (0, 'unknown', 'Không xác định', 'Unknown', false, '#808080'),
        (1, 'rice', 'Lúa', 'Rice', true, '#FFD700'),
        (2, 'maize', 'Ngô', 'Maize', true, '#FFA500'),
        (3, 'cassava', 'Sắn', 'Cassava', true, '#8B4513'),
        (4, 'sugarcane', 'Mía', 'Sugarcane', true, '#32CD32'),
        (5, 'vegetables', 'Rau màu', 'Vegetables', true, '#228B22'),
        (6, 'fruit_trees', 'Cây ăn quả', 'Fruit Trees', true, '#FF6347'),
        (7, 'coffee', 'Cà phê', 'Coffee', false, '#8B0000'),
        (8, 'rubber', 'Cao su', 'Rubber', false, '#2F4F4F'),
        (9, 'forest', 'Rừng', 'Forest', false, '#006400'),
        (10, 'water', 'Mặt nước', 'Water', false, '#0000FF'),
        (11, 'urban', 'Đô thị', 'Urban', false, '#A9A9A9'),
        (12, 'barren', 'Đất trống', 'Barren', false, '#D2B48C')
    """)


def downgrade() -> None:
    op.drop_table('jobs')
    op.drop_table('alerts')
    op.drop_table('area_stats')
    op.drop_table('admin_units')
    op.drop_table('crop_classes')
    op.drop_table('inference_runs')
    op.drop_table('models')
    op.drop_table('assets')
    op.drop_table('scenes')
    op.drop_table('tiles')
    op.execute('DROP EXTENSION IF EXISTS postgis')
