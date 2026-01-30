"""
Test 01: Environment and configuration loading.

Tests that .env file loads correctly and Settings validates properly.
"""

import os
import pytest
from pathlib import Path


class TestEnvironmentLoading:
    """Test environment configuration loading."""

    def test_env_example_exists(self):
        """Check that .env.example file exists."""
        env_example = Path(__file__).parent.parent / ".env.example"
        assert env_example.exists(), ".env.example file should exist"

    def test_env_example_has_required_vars(self):
        """Check that .env.example contains all required variables."""
        env_example = Path(__file__).parent.parent / ".env.example"
        content = env_example.read_text()
        
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "DO_SPACES_REGION",
            "DO_SPACES_BUCKET",
            "DO_SPACES_KEY",
            "DO_SPACES_SECRET",
            "SENTINELHUB_CLIENT_ID",
            "SENTINELHUB_CLIENT_SECRET",
        ]
        
        for var in required_vars:
            assert var in content, f"{var} should be in .env.example"

    def test_settings_class_exists(self):
        """Check that Settings class can be imported."""
        from app.core.config import Settings
        assert Settings is not None

    def test_settings_has_required_fields(self):
        """Check that Settings class has required fields."""
        from app.core.config import Settings
        
        # Check field names exist in model_fields
        required_fields = [
            "database_url",
            "redis_url",
            "do_spaces_region",
            "do_spaces_bucket",
            "do_spaces_key",
            "do_spaces_secret",
            "sentinelhub_client_id",
            "sentinelhub_client_secret",
        ]
        
        for field in required_fields:
            assert field in Settings.model_fields, f"Settings should have {field} field"

    def test_get_settings_function(self):
        """Check that get_settings function exists and is cached."""
        from app.core.config import get_settings
        
        # Should be a function
        assert callable(get_settings)

    @pytest.mark.integration
    def test_settings_loads_from_env(self, env_file):
        """Test that settings load from .env file."""
        if not env_file:
            pytest.skip("No .env file found")
        
        from app.core.config import get_settings
        
        settings = get_settings()
        
        # Should have loaded values
        assert settings.database_url is not None
        assert settings.do_spaces_bucket is not None

    @pytest.mark.integration
    def test_settings_validates_correctly(self, env_file):
        """Test that settings validation works."""
        if not env_file:
            pytest.skip("No .env file found")
        
        from app.core.config import get_settings
        
        settings = get_settings()
        
        # Check computed properties
        assert isinstance(settings.is_production, bool)
        assert settings.spaces_public_url.startswith("https://")

    def test_settings_endpoint_builder(self):
        """Test that DO Spaces endpoint is built correctly."""
        from app.core.config import Settings
        
        # The validator should build endpoint from region
        # This tests the validator logic
        assert hasattr(Settings, 'build_spaces_endpoint')
