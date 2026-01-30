"""
Test 05: S4A model inference.

Tests S4A ConvLSTM model loading and inference pipeline.
"""

import pytest
import numpy as np


class TestS4AInference:
    """Test S4A model inference module."""

    def test_s4a_module_imports(self):
        """Check that S4A inference module can be imported."""
        from app.core.s4a_infer import (
            load_s4a_model,
            download_model_weights,
            fetch_monthly_stack_sentinelhub,
            load_norm_stats,
            apply_norm,
            infer_pixel_map,
            area_stats_from_map,
            run_s4a_on_bbox,
            S4AModelNotFoundError,
            DEFAULT_CLASS_NAMES,
        )
        
        assert callable(load_s4a_model)
        assert callable(download_model_weights)
        assert callable(fetch_monthly_stack_sentinelhub)
        assert callable(load_norm_stats)
        assert callable(apply_norm)
        assert callable(infer_pixel_map)
        assert callable(area_stats_from_map)
        assert callable(run_s4a_on_bbox)
        assert S4AModelNotFoundError is not None
        assert isinstance(DEFAULT_CLASS_NAMES, dict)

    def test_default_class_names(self):
        """Check default class names mapping."""
        from app.core.s4a_infer import DEFAULT_CLASS_NAMES
        
        # Should have at least 13 classes (0-12)
        assert len(DEFAULT_CLASS_NAMES) >= 13
        
        # Check specific classes
        assert DEFAULT_CLASS_NAMES[0] == "unknown"
        assert DEFAULT_CLASS_NAMES[1] == "rice"
        assert DEFAULT_CLASS_NAMES[9] == "forest"
        assert DEFAULT_CLASS_NAMES[10] == "water"

    def test_apply_norm_no_stats(self, sample_monthly_stack):
        """Test apply_norm with no normalization stats."""
        from app.core.s4a_infer import apply_norm
        
        # Should return input unchanged when no stats provided
        result = apply_norm(sample_monthly_stack, norm_stats=None)
        
        assert result.shape == sample_monthly_stack.shape
        np.testing.assert_array_almost_equal(result, sample_monthly_stack)

    def test_apply_norm_with_stats(self, sample_monthly_stack):
        """Test apply_norm with normalization stats."""
        from app.core.s4a_infer import apply_norm
        
        # Create mock norm stats
        norm_stats = {
            "mean": np.array([0.1, 0.1, 0.1, 0.2]),
            "std": np.array([0.05, 0.05, 0.05, 0.1]),
        }
        
        result = apply_norm(sample_monthly_stack, norm_stats=norm_stats)
        
        # Shape should be preserved
        assert result.shape == sample_monthly_stack.shape
        
        # Values should be normalized (different from input)
        assert not np.allclose(result, sample_monthly_stack)
        
        # Check dtype
        assert result.dtype == np.float32

    def test_area_stats_from_map(self, sample_pred_map, sample_bbox):
        """Test area statistics calculation from prediction map."""
        from app.core.s4a_infer import area_stats_from_map
        
        stats = area_stats_from_map(sample_pred_map, sample_bbox)
        
        # Should return a list
        assert isinstance(stats, list)
        assert len(stats) > 0
        
        # Check structure of each stat
        for stat in stats:
            assert "class_id" in stat
            assert "class_name" in stat
            assert "pixel_count" in stat
            assert "area_ha" in stat
            
            assert isinstance(stat["class_id"], int)
            assert isinstance(stat["class_name"], str)
            assert isinstance(stat["pixel_count"], int)
            assert isinstance(stat["area_ha"], float)
            assert stat["pixel_count"] > 0
            assert stat["area_ha"] > 0
        
        # Total pixel count should equal map size
        total_pixels = sum(s["pixel_count"] for s in stats)
        assert total_pixels == 61 * 61

    def test_area_stats_sorted_by_area(self, sample_pred_map, sample_bbox):
        """Test that area stats are sorted by area descending."""
        from app.core.s4a_infer import area_stats_from_map
        
        stats = area_stats_from_map(sample_pred_map, sample_bbox)
        
        # Check sorted descending
        areas = [s["area_ha"] for s in stats]
        assert areas == sorted(areas, reverse=True)

    def test_s4a_model_not_found_error(self):
        """Test that S4AModelNotFoundError is raised when vendor code missing."""
        from app.core.s4a_infer import load_s4a_model, S4AModelNotFoundError
        
        # Should raise error when trying to load without vendor code
        with pytest.raises(S4AModelNotFoundError):
            load_s4a_model("/nonexistent/path.ckpt")

    @pytest.mark.integration
    def test_run_s4a_on_bbox_no_model(self, has_db_credentials, sample_bbox):
        """Test run_s4a_on_bbox fails gracefully without model."""
        if not has_db_credentials:
            pytest.skip("Database credentials not available")
        
        from app.core.s4a_infer import run_s4a_on_bbox, S4AModelNotFoundError
        
        # Should raise error when model not registered or vendor code missing
        with pytest.raises((S4AModelNotFoundError, Exception)):
            run_s4a_on_bbox(
                bbox=sample_bbox,
                end_year=2024,
                end_month=6,
                weights_s3_key="models/s4a/nonexistent.ckpt",
            )

    def test_pixel_area_calculation(self, sample_bbox):
        """Test pixel area calculation in hectares."""
        from app.core.raster_utils import calculate_pixel_area_ha
        
        pixel_area = calculate_pixel_area_ha(sample_bbox, width=61, height=61)
        
        # Should be a positive number
        assert pixel_area > 0
        
        # For a 0.1 x 0.1 degree bbox at ~10°N latitude
        # Total area is roughly 11km x 11km = 121 km² = 12,100 ha
        # With 61x61 = 3721 pixels, each pixel is about 3.25 ha
        # This is approximate due to projection
        assert 0.1 < pixel_area < 100  # Reasonable range
        
        print(f"Pixel area: {pixel_area:.4f} ha")

    def test_load_norm_stats_missing_file(self):
        """Test load_norm_stats with missing file."""
        from app.core.s4a_infer import load_norm_stats
        
        result = load_norm_stats("/nonexistent/path")
        assert result is None

    def test_load_norm_stats_none_path(self):
        """Test load_norm_stats with None path."""
        from app.core.s4a_infer import load_norm_stats
        
        result = load_norm_stats(None)
        assert result is None
