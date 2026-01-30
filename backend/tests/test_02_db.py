"""
Test 02: Database connection and PostGIS.

Tests database connectivity, PostGIS extension, and basic CRUD operations.
"""

import pytest
from uuid import uuid4


class TestDatabaseConnection:
    """Test database connection and basic operations."""

    def test_db_module_imports(self):
        """Check that database module can be imported."""
        from app.core.db import (
            engine,
            SessionLocal,
            Base,
            get_db,
            get_db_context,
            check_db_connection,
        )
        
        assert engine is not None
        assert SessionLocal is not None
        assert Base is not None
        assert callable(get_db)
        assert callable(check_db_connection)

    def test_models_import(self):
        """Check that all SQLAlchemy models can be imported."""
        from app.core.models_sqlalchemy import (
            Tile,
            Scene,
            Asset,
            Model,
            InferenceRun,
            CropClass,
            AdminUnit,
            AreaStat,
            Alert,
            Job,
        )
        
        # All models should have __tablename__
        assert Tile.__tablename__ == "tiles"
        assert Scene.__tablename__ == "scenes"
        assert Asset.__tablename__ == "assets"
        assert Model.__tablename__ == "models"
        assert InferenceRun.__tablename__ == "inference_runs"
        assert CropClass.__tablename__ == "crop_classes"
        assert AdminUnit.__tablename__ == "admin_units"
        assert AreaStat.__tablename__ == "area_stats"
        assert Alert.__tablename__ == "alerts"
        assert Job.__tablename__ == "jobs"

    @pytest.mark.integration
    def test_db_connection(self, has_db_credentials):
        """Test database connection."""
        if not has_db_credentials:
            pytest.skip("Database credentials not available")
        
        from app.core.db import check_db_connection
        
        assert check_db_connection() is True

    @pytest.mark.integration
    def test_postgis_extension(self, has_db_credentials):
        """Test that PostGIS extension is available."""
        if not has_db_credentials:
            pytest.skip("Database credentials not available")
        
        from app.core.db import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT PostGIS_Version()"
            ))
            version = result.scalar()
            assert version is not None
            print(f"PostGIS version: {version}")

    @pytest.mark.integration
    def test_simple_insert_select(self, has_db_credentials):
        """Test simple insert and select operations."""
        if not has_db_credentials:
            pytest.skip("Database credentials not available")
        
        from app.core.db import get_db_context
        from app.core.models_sqlalchemy import Job
        from app.core.time_utils import get_utc_now
        
        job_id = uuid4()
        
        with get_db_context() as db:
            # Insert
            job = Job(
                job_id=job_id,
                job_type="test",
                status="pending",
                payload={"test": True},
            )
            db.add(job)
            db.commit()
            
            # Select
            retrieved = db.query(Job).filter(Job.job_id == job_id).first()
            assert retrieved is not None
            assert retrieved.job_type == "test"
            assert retrieved.status == "pending"
            assert retrieved.payload == {"test": True}
            
            # Cleanup
            db.delete(retrieved)
            db.commit()

    @pytest.mark.integration
    def test_geometry_operations(self, has_db_credentials):
        """Test PostGIS geometry operations."""
        if not has_db_credentials:
            pytest.skip("Database credentials not available")
        
        from app.core.db import get_db_context
        from app.core.crud import create_tile, get_tile
        from geoalchemy2.shape import to_shape
        
        tile_id = f"TEST{uuid4().hex[:4].upper()}"
        bbox_wkt = "POLYGON((105.0 10.0, 106.0 10.0, 106.0 11.0, 105.0 11.0, 105.0 10.0))"
        
        with get_db_context() as db:
            # Create tile with geometry
            tile = create_tile(db, tile_id, bbox_wkt)
            assert tile is not None
            assert tile.tile_id == tile_id
            
            # Retrieve and check geometry
            retrieved = get_tile(db, tile_id)
            assert retrieved is not None
            
            # Convert geometry to shapely and check bounds
            geom = to_shape(retrieved.geom)
            bounds = geom.bounds
            assert bounds[0] == pytest.approx(105.0, rel=0.01)
            assert bounds[1] == pytest.approx(10.0, rel=0.01)
            assert bounds[2] == pytest.approx(106.0, rel=0.01)
            assert bounds[3] == pytest.approx(11.0, rel=0.01)
            
            # Cleanup
            db.delete(retrieved)
            db.commit()

    @pytest.mark.integration
    def test_crop_classes_seeded(self, has_db_credentials):
        """Test that crop classes are seeded from migration."""
        if not has_db_credentials:
            pytest.skip("Database credentials not available")
        
        from app.core.db import get_db_context
        from app.core.crud import get_all_crop_classes
        
        with get_db_context() as db:
            classes = get_all_crop_classes(db)
            
            # Should have at least the default classes
            assert len(classes) >= 10
            
            # Check for rice class
            rice = next((c for c in classes if c.code == "rice"), None)
            assert rice is not None
            assert rice.class_id == 1
            assert rice.name_en == "Rice"
            assert rice.is_food_crop is True
