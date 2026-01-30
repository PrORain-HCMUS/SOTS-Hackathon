"""
Test 04: Sentinel Hub data fetching.

Tests Sentinel Hub API integration for fetching Sentinel-2 data.
"""

import pytest
from datetime import datetime


class TestSentinelHubClient:
    """Test Sentinel Hub client."""

    def test_sentinelhub_module_imports(self):
        """Check that Sentinel Hub module can be imported."""
        from app.core.sentinelhub_client import (
            SentinelHubClient,
            get_sentinelhub_client,
            get_sh_config,
            EVALSCRIPT_MONTHLY_COMPOSITE,
        )
        
        assert SentinelHubClient is not None
        assert callable(get_sentinelhub_client)
        assert callable(get_sh_config)
        assert EVALSCRIPT_MONTHLY_COMPOSITE is not None

    def test_sentinelhub_client_methods(self):
        """Check that SentinelHubClient has required methods."""
        from app.core.sentinelhub_client import SentinelHubClient
        
        required_methods = [
            "search_scenes",
            "fetch_monthly_composite",
            "fetch_monthly_stack",
        ]
        
        for method in required_methods:
            assert hasattr(SentinelHubClient, method), f"SentinelHubClient should have {method} method"

    def test_evalscript_structure(self):
        """Check that evalscript has correct structure."""
        from app.core.sentinelhub_client import EVALSCRIPT_MONTHLY_COMPOSITE
        
        # Should contain required elements
        assert "//VERSION=3" in EVALSCRIPT_MONTHLY_COMPOSITE
        assert "function setup()" in EVALSCRIPT_MONTHLY_COMPOSITE
        assert "function evaluatePixel" in EVALSCRIPT_MONTHLY_COMPOSITE
        assert "B02" in EVALSCRIPT_MONTHLY_COMPOSITE
        assert "B03" in EVALSCRIPT_MONTHLY_COMPOSITE
        assert "B04" in EVALSCRIPT_MONTHLY_COMPOSITE
        assert "B08" in EVALSCRIPT_MONTHLY_COMPOSITE
        assert "SCL" in EVALSCRIPT_MONTHLY_COMPOSITE

    @pytest.mark.integration
    def test_sentinelhub_config(self, has_sentinelhub_credentials):
        """Test Sentinel Hub configuration."""
        if not has_sentinelhub_credentials:
            pytest.skip("Sentinel Hub credentials not available")
        
        from app.core.sentinelhub_client import get_sh_config
        
        config = get_sh_config()
        
        assert config.sh_client_id is not None
        assert config.sh_client_secret is not None
        assert config.sh_base_url is not None

    @pytest.mark.integration
    def test_fetch_monthly_composite(self, has_sentinelhub_credentials, sample_bbox):
        """Test fetching a monthly composite from Sentinel Hub."""
        if not has_sentinelhub_credentials:
            pytest.skip("Sentinel Hub credentials not available")
        
        from app.core.sentinelhub_client import get_sentinelhub_client
        import numpy as np
        
        sh_client = get_sentinelhub_client()
        
        # Fetch composite for a recent month
        year = 2024
        month = 6
        size = (61, 61)
        
        composite = sh_client.fetch_monthly_composite(
            bbox=sample_bbox,
            year=year,
            month=month,
            size=size,
        )
        
        # Check shape: (4, 61, 61) for 4 bands
        assert composite.shape == (4, 61, 61), f"Expected (4, 61, 61), got {composite.shape}"
        
        # Check data type
        assert composite.dtype == np.float32
        
        # Check value range (reflectance should be 0-1 or masked as 0)
        assert composite.min() >= 0.0
        assert composite.max() <= 1.0 or composite.max() == 0.0
        
        print(f"Composite shape: {composite.shape}")
        print(f"Value range: [{composite.min():.4f}, {composite.max():.4f}]")

    @pytest.mark.integration
    def test_fetch_monthly_stack(self, has_sentinelhub_credentials, sample_bbox):
        """Test fetching a monthly stack for S4A input."""
        if not has_sentinelhub_credentials:
            pytest.skip("Sentinel Hub credentials not available")
        
        from app.core.sentinelhub_client import get_sentinelhub_client
        import numpy as np
        
        sh_client = get_sentinelhub_client()
        
        # Fetch 6-month stack
        end_year = 2024
        end_month = 6
        window_len = 6
        size = (61, 61)
        
        stack = sh_client.fetch_monthly_stack(
            bbox=sample_bbox,
            end_year=end_year,
            end_month=end_month,
            window_len=window_len,
            size=size,
        )
        
        # Check shape: (1, 6, 4, 61, 61)
        expected_shape = (1, window_len, 4, 61, 61)
        assert stack.shape == expected_shape, f"Expected {expected_shape}, got {stack.shape}"
        
        # Check data type
        assert stack.dtype == np.float32
        
        print(f"Stack shape: {stack.shape}")
        print(f"Value range: [{stack.min():.4f}, {stack.max():.4f}]")

    @pytest.mark.integration
    def test_search_scenes(self, has_sentinelhub_credentials, sample_bbox):
        """Test searching for scenes in Sentinel Hub catalog."""
        if not has_sentinelhub_credentials:
            pytest.skip("Sentinel Hub credentials not available")
        
        from app.core.sentinelhub_client import get_sentinelhub_client
        from datetime import timedelta
        
        sh_client = get_sentinelhub_client()
        
        # Search for scenes in the last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        scenes = sh_client.search_scenes(
            bbox=sample_bbox,
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=80.0,
        )
        
        # Should return a list
        assert isinstance(scenes, list)
        
        if scenes:
            # Check scene structure
            scene = scenes[0]
            assert "scene_id" in scene
            assert "sensing_time" in scene
            assert "cloud_cover" in scene
            
            print(f"Found {len(scenes)} scenes")
            print(f"First scene: {scene['scene_id']}")
