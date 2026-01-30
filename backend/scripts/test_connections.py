#!/usr/bin/env python
"""
Test connections to external services.

Usage:
    python scripts/test_connections.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()


def test_env_loading():
    """Test environment variables loading."""
    print("\n" + "=" * 60)
    print("1. TESTING ENVIRONMENT LOADING")
    print("=" * 60)
    
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        print(f"✓ Settings loaded successfully")
        print(f"  - APP_ENV: {settings.app_env}")
        print(f"  - DO_SPACES_REGION: {settings.do_spaces_region}")
        print(f"  - DO_SPACES_BUCKET: {settings.do_spaces_bucket}")
        print(f"  - SENTINELHUB_CLIENT_ID: {'***' + settings.sentinelhub_client_id[-4:] if settings.sentinelhub_client_id else 'NOT SET'}")
        print(f"  - SENTINELHUB_CLIENT_SECRET: {'***' if settings.sentinelhub_client_secret else 'NOT SET'}")
        return True
    except Exception as e:
        print(f"✗ Failed to load settings: {e}")
        return False


def test_sentinelhub_connection():
    """Test Sentinel Hub API connection."""
    print("\n" + "=" * 60)
    print("2. TESTING SENTINEL HUB CONNECTION")
    print("=" * 60)
    
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        if not settings.sentinelhub_client_id or not settings.sentinelhub_client_secret:
            print("✗ Sentinel Hub credentials not configured in .env")
            print("  Please set SENTINELHUB_CLIENT_ID and SENTINELHUB_CLIENT_SECRET")
            return False
        
        from sentinelhub import SHConfig, SentinelHubCatalog, DataCollection, BBox, CRS
        from datetime import datetime, timedelta
        
        # Configure Sentinel Hub
        config = SHConfig()
        config.sh_client_id = settings.sentinelhub_client_id
        config.sh_client_secret = settings.sentinelhub_client_secret
        config.sh_base_url = settings.sentinelhub_base_url
        
        print(f"  - Base URL: {config.sh_base_url}")
        print(f"  - Client ID: ***{settings.sentinelhub_client_id[-4:]}")
        
        # Test catalog search
        print("\n  Testing Catalog API...")
        catalog = SentinelHubCatalog(config=config)
        
        # Search for scenes in Mekong Delta, Vietnam
        bbox = BBox((105.7, 10.0, 105.8, 10.1), crs=CRS.WGS84)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        search_iterator = catalog.search(
            DataCollection.SENTINEL2_L2A,
            bbox=bbox,
            time=(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")),
            filter="eo:cloud_cover < 80",
        )
        
        results = list(search_iterator)
        
        print(f"  ✓ Catalog API working!")
        print(f"  - Found {len(results)} scenes in last 30 days")
        print(f"  - Search area: Mekong Delta, Vietnam (105.7°E, 10.0°N)")
        
        if results:
            first = results[0]
            print(f"\n  First scene:")
            print(f"    - ID: {first['id']}")
            print(f"    - Date: {first['properties']['datetime']}")
            print(f"    - Cloud cover: {first['properties'].get('eo:cloud_cover', 'N/A')}%")
        
        return True
        
    except Exception as e:
        print(f"✗ Sentinel Hub connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sentinelhub_data_fetch():
    """Test fetching actual data from Sentinel Hub."""
    print("\n" + "=" * 60)
    print("3. TESTING SENTINEL HUB DATA FETCH")
    print("=" * 60)
    
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        if not settings.sentinelhub_client_id or not settings.sentinelhub_client_secret:
            print("✗ Sentinel Hub credentials not configured")
            return False
        
        from sentinelhub import (
            SHConfig, SentinelHubRequest, DataCollection, 
            MimeType, BBox, CRS, bbox_to_dimensions
        )
        
        config = SHConfig()
        config.sh_client_id = settings.sentinelhub_client_id
        config.sh_client_secret = settings.sentinelhub_client_secret
        config.sh_base_url = settings.sentinelhub_base_url
        
        # Simple evalscript to get RGB
        evalscript = """
        //VERSION=3
        function setup() {
            return {
                input: ["B04", "B03", "B02"],
                output: { bands: 3, sampleType: "FLOAT32" }
            };
        }
        function evaluatePixel(sample) {
            return [sample.B04, sample.B03, sample.B02];
        }
        """
        
        # Small bbox in Mekong Delta
        bbox = BBox((105.75, 10.05, 105.76, 10.06), crs=CRS.WGS84)
        size = (61, 61)
        
        print(f"  Fetching 61x61 RGB patch...")
        print(f"  - Location: Mekong Delta (105.75°E, 10.05°N)")
        
        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=("2024-01-01", "2024-06-30"),
                    mosaicking_order="leastCC",
                )
            ],
            responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
            bbox=bbox,
            size=size,
            config=config,
        )
        
        data = request.get_data()[0]
        
        print(f"  ✓ Data fetch successful!")
        print(f"  - Shape: {data.shape}")
        print(f"  - Dtype: {data.dtype}")
        print(f"  - Value range: [{data.min():.4f}, {data.max():.4f}]")
        
        return True
        
    except Exception as e:
        print(f"✗ Data fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_connection():
    """Test database connection."""
    print("\n" + "=" * 60)
    print("4. TESTING DATABASE CONNECTION")
    print("=" * 60)
    
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        print(f"  - Database URL: {settings.database_url[:30]}...")
        
        from app.core.db import check_db_connection
        
        if check_db_connection():
            print("  ✓ Database connection successful!")
            return True
        else:
            print("  ✗ Database connection failed")
            return False
            
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def test_spaces_connection():
    """Test DigitalOcean Spaces connection."""
    print("\n" + "=" * 60)
    print("5. TESTING DIGITALOCEAN SPACES CONNECTION")
    print("=" * 60)
    
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        if not settings.do_spaces_key or not settings.do_spaces_secret:
            print("✗ DO Spaces credentials not configured")
            return False
        
        print(f"  - Bucket: {settings.do_spaces_bucket}")
        print(f"  - Region: {settings.do_spaces_region}")
        print(f"  - Endpoint: {settings.do_spaces_endpoint}")
        
        from app.core.spaces import get_spaces_client
        
        spaces = get_spaces_client()
        
        # Try to list objects (may be empty)
        objects = spaces.list_objects(prefix="", max_keys=1)
        
        print(f"  ✓ Spaces connection successful!")
        print(f"  - Objects in bucket: {len(objects)} (showing max 1)")
        
        return True
        
    except Exception as e:
        print(f"✗ Spaces connection failed: {e}")
        return False


def main():
    """Run all connection tests."""
    print("\n" + "=" * 60)
    print("AGRIPULSE CONNECTION TESTS")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Environment
    results["env"] = test_env_loading()
    
    # Test 2: Sentinel Hub Connection
    results["sentinelhub_catalog"] = test_sentinelhub_connection()
    
    # Test 3: Sentinel Hub Data Fetch
    if results["sentinelhub_catalog"]:
        results["sentinelhub_data"] = test_sentinelhub_data_fetch()
    else:
        results["sentinelhub_data"] = False
    
    # Test 4: Database
    results["database"] = test_database_connection()
    
    # Test 5: Spaces
    results["spaces"] = test_spaces_connection()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed."))
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
