"""
Test 07: Area statistics calculation.

Tests aggregation of prediction maps to area statistics.
"""

import pytest
import numpy as np
from datetime import datetime, timezone


class TestAreaStatistics:
    """Test area statistics calculation."""

    def test_aggregation_module_imports(self):
        """Check that aggregation module can be imported."""
        from app.core.aggregation import (
            get_crop_classes,
            compute_zonal_stats_simple,
            compute_zonal_stats_by_admin,
            upsert_area_stats,
            aggregate_crop_map_to_stats,
            get_country_stats,
            get_province_stats,
        )
        
        assert callable(get_crop_classes)
        assert callable(compute_zonal_stats_simple)
        assert callable(compute_zonal_stats_by_admin)
        assert callable(upsert_area_stats)
        assert callable(aggregate_crop_map_to_stats)
        assert callable(get_country_stats)
        assert callable(get_province_stats)

    def test_compute_zonal_stats_simple(self, sample_pred_map, sample_bbox):
        """Test simple zonal statistics computation."""
        from app.core.aggregation import compute_zonal_stats_simple
        
        stats = compute_zonal_stats_simple(sample_pred_map, sample_bbox)
        
        # Should return a list
        assert isinstance(stats, list)
        assert len(stats) > 0
        
        # Check structure
        for stat in stats:
            assert "class_id" in stat
            assert "pixel_count" in stat
            assert "area_ha" in stat
            
            assert isinstance(stat["class_id"], int)
            assert isinstance(stat["pixel_count"], int)
            assert isinstance(stat["area_ha"], float)
        
        # Total pixels should match map size
        total_pixels = sum(s["pixel_count"] for s in stats)
        assert total_pixels == sample_pred_map.size

    def test_area_ha_calculation(self, sample_bbox):
        """Test that area_ha is calculated correctly."""
        from app.core.aggregation import compute_zonal_stats_simple
        from app.core.raster_utils import calculate_pixel_area_ha
        
        # Create a uniform prediction map (all class 1)
        pred_map = np.ones((61, 61), dtype=np.uint16)
        
        stats = compute_zonal_stats_simple(pred_map, sample_bbox)
        
        # Should have exactly one class
        assert len(stats) == 1
        assert stats[0]["class_id"] == 1
        assert stats[0]["pixel_count"] == 61 * 61
        
        # Calculate expected area
        pixel_area = calculate_pixel_area_ha(sample_bbox, 61, 61)
        expected_area = pixel_area * 61 * 61
        
        assert stats[0]["area_ha"] == pytest.approx(expected_area, rel=0.01)

    def test_multiple_classes(self, sample_bbox):
        """Test statistics with multiple classes."""
        from app.core.aggregation import compute_zonal_stats_simple
        
        # Create a map with known class distribution
        pred_map = np.zeros((61, 61), dtype=np.uint16)
        pred_map[:30, :] = 1  # Rice: 30 * 61 = 1830 pixels
        pred_map[30:50, :] = 2  # Maize: 20 * 61 = 1220 pixels
        pred_map[50:, :] = 3  # Cassava: 11 * 61 = 671 pixels
        
        stats = compute_zonal_stats_simple(pred_map, sample_bbox)
        
        # Should have 3 classes
        assert len(stats) == 3
        
        # Check pixel counts
        class_counts = {s["class_id"]: s["pixel_count"] for s in stats}
        assert class_counts[1] == 30 * 61
        assert class_counts[2] == 20 * 61
        assert class_counts[3] == 11 * 61
        
        # Total should match
        total = sum(s["pixel_count"] for s in stats)
        assert total == 61 * 61

    def test_area_proportional_to_pixels(self, sample_bbox):
        """Test that area is proportional to pixel count."""
        from app.core.aggregation import compute_zonal_stats_simple
        
        # Create a map with 50/50 split
        pred_map = np.zeros((61, 61), dtype=np.uint16)
        pred_map[:, :30] = 1
        pred_map[:, 30:] = 2
        
        stats = compute_zonal_stats_simple(pred_map, sample_bbox)
        
        # Get stats by class
        stats_dict = {s["class_id"]: s for s in stats}
        
        # Area ratio should match pixel ratio
        pixel_ratio = stats_dict[1]["pixel_count"] / stats_dict[2]["pixel_count"]
        area_ratio = stats_dict[1]["area_ha"] / stats_dict[2]["area_ha"]
        
        assert pixel_ratio == pytest.approx(area_ratio, rel=0.01)

    @pytest.mark.integration
    def test_upsert_area_stats(self, has_db_credentials):
        """Test upserting area statistics to database."""
        if not has_db_credentials:
            pytest.skip("Database credentials not available")
        
        from app.core.db import get_db_context
        from app.core.aggregation import upsert_area_stats
        from app.core.models_sqlalchemy import AdminUnit, AreaStat
        from uuid import uuid4
        
        with get_db_context() as db:
            # Create a test admin unit
            from app.core.crud import create_admin_unit
            
            admin = create_admin_unit(
                db=db,
                name=f"Test Province {uuid4().hex[:6]}",
                level=1,
                code=f"TP{uuid4().hex[:4].upper()}",
            )
            
            try:
                period_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
                period_end = datetime(2024, 1, 31, tzinfo=timezone.utc)
                
                # Insert
                stat1 = upsert_area_stats(
                    db=db,
                    admin_id=admin.admin_id,
                    class_id=1,
                    period_start=period_start,
                    period_end=period_end,
                    area_ha=1000.0,
                    pixel_count=5000,
                )
                
                assert stat1 is not None
                assert stat1.area_ha == 1000.0
                assert stat1.pixel_count == 5000
                
                # Update (upsert)
                stat2 = upsert_area_stats(
                    db=db,
                    admin_id=admin.admin_id,
                    class_id=1,
                    period_start=period_start,
                    period_end=period_end,
                    area_ha=1500.0,
                    pixel_count=7500,
                )
                
                # Should be same record, updated
                assert stat2.stat_id == stat1.stat_id
                assert stat2.area_ha == 1500.0
                assert stat2.pixel_count == 7500
                
            finally:
                # Cleanup
                db.query(AreaStat).filter(
                    AreaStat.admin_id == admin.admin_id
                ).delete()
                db.delete(admin)
                db.commit()

    @pytest.mark.integration
    def test_get_country_stats(self, has_db_credentials):
        """Test getting country-level statistics."""
        if not has_db_credentials:
            pytest.skip("Database credentials not available")
        
        from app.core.db import get_db_context
        from app.core.aggregation import get_country_stats
        
        with get_db_context() as db:
            period_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
            period_end = datetime(2024, 1, 31, tzinfo=timezone.utc)
            
            # May return empty list if no data
            stats = get_country_stats(db, period_start, period_end)
            
            assert isinstance(stats, list)

    @pytest.mark.integration
    def test_get_province_stats(self, has_db_credentials):
        """Test getting province-level statistics."""
        if not has_db_credentials:
            pytest.skip("Database credentials not available")
        
        from app.core.db import get_db_context
        from app.core.aggregation import get_province_stats
        
        with get_db_context() as db:
            period_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
            period_end = datetime(2024, 1, 31, tzinfo=timezone.utc)
            
            # Query for a province (may not exist)
            stats = get_province_stats(db, "Hanoi", period_start, period_end)
            
            assert isinstance(stats, list)

    def test_edge_case_empty_map(self, sample_bbox):
        """Test with empty/zero prediction map."""
        from app.core.aggregation import compute_zonal_stats_simple
        
        # All zeros (class 0 = unknown)
        pred_map = np.zeros((61, 61), dtype=np.uint16)
        
        stats = compute_zonal_stats_simple(pred_map, sample_bbox)
        
        assert len(stats) == 1
        assert stats[0]["class_id"] == 0
        assert stats[0]["pixel_count"] == 61 * 61

    def test_edge_case_single_pixel(self, sample_bbox):
        """Test with single pixel map."""
        from app.core.aggregation import compute_zonal_stats_simple
        
        pred_map = np.array([[5]], dtype=np.uint16)
        
        stats = compute_zonal_stats_simple(pred_map, sample_bbox)
        
        assert len(stats) == 1
        assert stats[0]["class_id"] == 5
        assert stats[0]["pixel_count"] == 1
