"""
Pytest configuration and fixtures.
"""

import os
import pytest
from pathlib import Path

# Set test environment
os.environ.setdefault("APP_ENV", "test")


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external services)"
    )


@pytest.fixture(scope="session")
def env_file():
    """Check if .env file exists."""
    env_path = Path(__file__).parent.parent / ".env"
    return env_path.exists()


@pytest.fixture(scope="session")
def has_db_credentials(env_file):
    """Check if database credentials are available."""
    if not env_file:
        return False
    try:
        from app.core.config import get_settings
        settings = get_settings()
        return bool(settings.database_url)
    except Exception:
        return False


@pytest.fixture(scope="session")
def has_spaces_credentials(env_file):
    """Check if DigitalOcean Spaces credentials are available."""
    if not env_file:
        return False
    try:
        from app.core.config import get_settings
        settings = get_settings()
        return all([
            settings.do_spaces_bucket,
            settings.do_spaces_key,
            settings.do_spaces_secret,
        ])
    except Exception:
        return False


@pytest.fixture(scope="session")
def has_sentinelhub_credentials(env_file):
    """Check if Sentinel Hub credentials are available."""
    if not env_file:
        return False
    try:
        from app.core.config import get_settings
        settings = get_settings()
        return all([
            settings.sentinelhub_client_id,
            settings.sentinelhub_client_secret,
        ])
    except Exception:
        return False


@pytest.fixture
def sample_bbox():
    """Sample bounding box in Mekong Delta, Vietnam."""
    # Small area near Can Tho
    return (105.7, 10.0, 105.8, 10.1)


@pytest.fixture
def sample_tile_id():
    """Sample tile ID."""
    return "48PWN"


@pytest.fixture
def sample_monthly_stack():
    """Create a sample monthly stack for testing."""
    import numpy as np
    
    # Shape: (1, 6, 4, 61, 61) - batch, time, channels, height, width
    np.random.seed(42)
    stack = np.random.rand(1, 6, 4, 61, 61).astype(np.float32)
    
    # Simulate realistic reflectance values (0-1 range)
    stack = stack * 0.3 + 0.1
    
    return stack


@pytest.fixture
def sample_pred_map():
    """Create a sample prediction map for testing."""
    import numpy as np
    
    np.random.seed(42)
    # 61x61 map with class values 0-12
    pred_map = np.random.randint(0, 13, size=(61, 61), dtype=np.uint16)
    
    return pred_map
