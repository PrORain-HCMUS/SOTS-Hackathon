"""
Test 06: GeoTIFF writing and reading.

Tests raster I/O utilities for creating tiled GeoTIFFs with overviews.
"""

import pytest
import tempfile
from pathlib import Path
import numpy as np


class TestGeoTIFFOperations:
    """Test GeoTIFF read/write operations."""

    def test_raster_utils_imports(self):
        """Check that raster utilities can be imported."""
        from app.core.raster_utils import (
            write_geotiff,
            write_cog,
            read_geotiff,
            calculate_pixel_area_ha,
        )
        
        assert callable(write_geotiff)
        assert callable(write_cog)
        assert callable(read_geotiff)
        assert callable(calculate_pixel_area_ha)

    def test_write_geotiff_2d(self, sample_bbox):
        """Test writing a 2D array as GeoTIFF."""
        from app.core.raster_utils import write_geotiff, read_geotiff
        
        # Create test data
        data = np.random.rand(61, 61).astype(np.float32)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_2d.tif"
            
            # Write
            result_path = write_geotiff(
                data=data,
                output_path=output_path,
                bbox=sample_bbox,
                crs="EPSG:4326",
            )
            
            assert result_path.exists()
            assert result_path.stat().st_size > 0
            
            # Read back
            read_data, metadata = read_geotiff(result_path)
            
            # Check shape (should be 3D with 1 band)
            assert read_data.shape == (1, 61, 61)
            
            # Check values match
            np.testing.assert_array_almost_equal(read_data[0], data, decimal=5)
            
            # Check metadata
            assert metadata["crs"] == "EPSG:4326"
            assert metadata["width"] == 61
            assert metadata["height"] == 61
            assert metadata["count"] == 1

    def test_write_geotiff_3d(self, sample_bbox):
        """Test writing a 3D array as GeoTIFF."""
        from app.core.raster_utils import write_geotiff, read_geotiff
        
        # Create test data with 4 bands
        data = np.random.rand(4, 61, 61).astype(np.float32)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_3d.tif"
            
            # Write
            result_path = write_geotiff(
                data=data,
                output_path=output_path,
                bbox=sample_bbox,
                crs="EPSG:4326",
            )
            
            assert result_path.exists()
            
            # Read back
            read_data, metadata = read_geotiff(result_path)
            
            # Check shape
            assert read_data.shape == (4, 61, 61)
            
            # Check values match
            np.testing.assert_array_almost_equal(read_data, data, decimal=5)
            
            # Check metadata
            assert metadata["count"] == 4

    def test_write_geotiff_uint16(self, sample_bbox, sample_pred_map):
        """Test writing uint16 prediction map as GeoTIFF."""
        from app.core.raster_utils import write_geotiff, read_geotiff
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_pred.tif"
            
            # Write
            result_path = write_geotiff(
                data=sample_pred_map,
                output_path=output_path,
                bbox=sample_bbox,
                crs="EPSG:4326",
                dtype="uint16",
            )
            
            assert result_path.exists()
            
            # Read back
            read_data, metadata = read_geotiff(result_path)
            
            # Check shape
            assert read_data.shape == (1, 61, 61)
            
            # Check values match
            np.testing.assert_array_equal(read_data[0], sample_pred_map)
            
            # Check dtype
            assert metadata["dtype"] == "uint16"

    def test_write_cog(self, sample_bbox):
        """Test writing a Cloud-Optimized GeoTIFF."""
        from app.core.raster_utils import write_cog, read_geotiff
        
        # Create test data
        data = np.random.rand(61, 61).astype(np.float32)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_cog.tif"
            
            # Write COG
            result_path = write_cog(
                data=data,
                output_path=output_path,
                bbox=sample_bbox,
                crs="EPSG:4326",
            )
            
            assert result_path.exists()
            assert result_path.stat().st_size > 0
            
            # Read back and verify
            read_data, metadata = read_geotiff(result_path)
            
            assert read_data.shape == (1, 61, 61)
            np.testing.assert_array_almost_equal(read_data[0], data, decimal=4)

    def test_geotiff_bbox_transform(self, sample_bbox):
        """Test that GeoTIFF has correct geotransform."""
        from app.core.raster_utils import write_geotiff
        import rasterio
        
        data = np.random.rand(61, 61).astype(np.float32)
        min_lon, min_lat, max_lon, max_lat = sample_bbox
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_transform.tif"
            
            write_geotiff(
                data=data,
                output_path=output_path,
                bbox=sample_bbox,
                crs="EPSG:4326",
            )
            
            # Check with rasterio
            with rasterio.open(output_path) as src:
                bounds = src.bounds
                
                # Check bounds match bbox
                assert bounds.left == pytest.approx(min_lon, rel=0.001)
                assert bounds.bottom == pytest.approx(min_lat, rel=0.001)
                assert bounds.right == pytest.approx(max_lon, rel=0.001)
                assert bounds.top == pytest.approx(max_lat, rel=0.001)

    def test_geotiff_tiled(self, sample_bbox):
        """Test that GeoTIFF is tiled."""
        from app.core.raster_utils import write_geotiff
        import rasterio
        
        data = np.random.rand(61, 61).astype(np.float32)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_tiled.tif"
            
            write_geotiff(
                data=data,
                output_path=output_path,
                bbox=sample_bbox,
                crs="EPSG:4326",
                tiled=True,
                blocksize=256,
            )
            
            with rasterio.open(output_path) as src:
                # Check tiling
                assert src.profile.get("tiled") is True

    def test_geotiff_nodata(self, sample_bbox):
        """Test GeoTIFF with nodata value."""
        from app.core.raster_utils import write_geotiff, read_geotiff
        
        data = np.random.rand(61, 61).astype(np.float32)
        data[0, 0] = -9999.0  # Set nodata
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_nodata.tif"
            
            write_geotiff(
                data=data,
                output_path=output_path,
                bbox=sample_bbox,
                crs="EPSG:4326",
                nodata=-9999.0,
            )
            
            read_data, metadata = read_geotiff(output_path)
            
            assert metadata["nodata"] == -9999.0

    def test_calculate_pixel_area_equator(self):
        """Test pixel area calculation near equator."""
        from app.core.raster_utils import calculate_pixel_area_ha
        
        # 1 degree x 1 degree at equator
        bbox = (0.0, 0.0, 1.0, 1.0)
        
        # 100x100 pixels
        area = calculate_pixel_area_ha(bbox, 100, 100)
        
        # At equator, 1 degree ≈ 111 km
        # 1 degree² ≈ 12,321 km² = 1,232,100 ha
        # Per pixel (100x100): ≈ 123.21 ha
        assert 100 < area < 150

    def test_calculate_pixel_area_vietnam(self, sample_bbox):
        """Test pixel area calculation at Vietnam latitude."""
        from app.core.raster_utils import calculate_pixel_area_ha
        
        # Sample bbox is at ~10°N
        area = calculate_pixel_area_ha(sample_bbox, 61, 61)
        
        # Should be positive and reasonable
        assert area > 0
        assert area < 100  # Less than 100 ha per pixel for this small bbox
