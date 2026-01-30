#!/usr/bin/env python
"""
Scan entire Europe with Sentinel-2 data for crop classification inference.

This script downloads Sentinel-2 data covering all of Europe in a grid pattern,
processes it for the Prithvi multi-temporal crop classification model, and
stores results in a structured format for mapping.

Europe bounding box (approximate):
- West: -25° (Atlantic/Portugal)
- East: 45° (Ural Mountains/Russia border)
- South: 34° (Mediterranean/Morocco border)
- North: 72° (Arctic/Norway)

Grid system:
- Each tile is 224x224 pixels at 30m resolution = 6.72km x 6.72km
- Tiles are stored with their center coordinates for reconstruction

Input requirements (from hls-foundation-os config):
- Shape: (18, 224, 224) = 6 bands × 3 time frames
- Bands: Blue (B02), Green (B03), Red (B04), NIR (B8A), SWIR1 (B11), SWIR2 (B12)
- num_frames: 3 (temporal frames)
- Resolution: 30m

Usage:
    python scan_europe_sentinel2.py --output /path/to/data
    python scan_europe_sentinel2.py --output /path/to/data --region france
    python scan_europe_sentinel2.py --output /path/to/data --test  # Small test area
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import rasterio
from rasterio.crs import CRS
import requests

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


# ============================================================================
# Configuration from environment
# ============================================================================
SENTINELHUB_CLIENT_ID = os.environ.get('SENTINELHUB_CLIENT_ID')
SENTINELHUB_CLIENT_SECRET = os.environ.get('SENTINELHUB_CLIENT_SECRET')
SENTINELHUB_BASE_URL = os.environ.get('SENTINELHUB_BASE_URL', 'https://services.sentinel-hub.com')

if not SENTINELHUB_CLIENT_ID or not SENTINELHUB_CLIENT_SECRET:
    print("ERROR: SENTINELHUB_CLIENT_ID and SENTINELHUB_CLIENT_SECRET must be set in .env file")
    print("Copy .env.example to .env and fill in your credentials")
    sys.exit(1)


# ============================================================================
# Model input requirements (from hls-foundation-os config)
# ============================================================================
NUM_FRAMES = 3  # Number of temporal frames
NUM_BANDS = 6   # Blue, Green, Red, NIR, SWIR1, SWIR2
TILE_SIZE = 224  # pixels
RESOLUTION = 30  # meters
TILE_SIZE_METERS = TILE_SIZE * RESOLUTION  # 6720m = 6.72km


# ============================================================================
# Europe regions and grid configuration
# ============================================================================
EUROPE_BOUNDS = {
    'west': -25.0,
    'east': 45.0,
    'south': 34.0,
    'north': 72.0,
}

# Predefined regions for targeted scanning
REGIONS = {
    'europe': EUROPE_BOUNDS,
    'western_europe': {'west': -10.0, 'east': 15.0, 'south': 36.0, 'north': 60.0},
    'central_europe': {'west': 5.0, 'east': 25.0, 'south': 45.0, 'north': 55.0},
    'eastern_europe': {'west': 20.0, 'east': 45.0, 'south': 40.0, 'north': 60.0},
    'northern_europe': {'west': 5.0, 'east': 30.0, 'south': 55.0, 'north': 72.0},
    'southern_europe': {'west': -10.0, 'east': 30.0, 'south': 34.0, 'north': 45.0},
    'france': {'west': -5.0, 'east': 10.0, 'south': 41.0, 'north': 51.5},
    'germany': {'west': 5.5, 'east': 15.5, 'south': 47.0, 'north': 55.5},
    'spain': {'west': -10.0, 'east': 5.0, 'south': 35.5, 'north': 44.0},
    'italy': {'west': 6.5, 'east': 19.0, 'south': 36.5, 'north': 47.5},
    'poland': {'west': 14.0, 'east': 24.5, 'south': 49.0, 'north': 55.0},
    'ukraine': {'west': 22.0, 'east': 40.5, 'south': 44.0, 'north': 52.5},
    'uk': {'west': -8.5, 'east': 2.0, 'south': 49.5, 'north': 61.0},
    'netherlands': {'west': 3.0, 'east': 7.5, 'south': 50.5, 'north': 53.7},
    'france_sample': {'west': 2.0, 'east': 3.0, 'south': 48.5, 'north': 49.5},  # Paris area sample
    'test': {'west': 4.0, 'east': 5.0, 'south': 51.0, 'north': 52.0},  # Small test area
    # Vietnam regions
    'mekong_delta': {'west': 104.5, 'east': 107.0, 'south': 8.5, 'north': 11.5},  # Đồng bằng sông Cửu Long
    'vietnam': {'west': 102.0, 'east': 110.0, 'south': 8.0, 'north': 23.5},  # Full Vietnam
}


# ============================================================================
# Sentinel Hub API functions
# ============================================================================
_token_cache = {'token': None, 'expires': None}


def get_sentinelhub_token():
    """Get OAuth2 token from Sentinel Hub with caching."""
    global _token_cache
    
    # Check if cached token is still valid
    if _token_cache['token'] and _token_cache['expires']:
        if datetime.now() < _token_cache['expires']:
            return _token_cache['token']
    
    token_url = f"{SENTINELHUB_BASE_URL}/oauth/token"
    
    data = {
        'grant_type': 'client_credentials',
        'client_id': SENTINELHUB_CLIENT_ID,
        'client_secret': SENTINELHUB_CLIENT_SECRET,
    }
    
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        
        _token_cache['token'] = token_data.get('access_token')
        # Token expires in 1 hour, refresh 5 minutes early
        _token_cache['expires'] = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600) - 300)
        
        return _token_cache['token']
    except Exception as e:
        print(f"Error getting Sentinel Hub token: {e}")
        return None


def search_sentinel2_scenes(bbox, start_date, end_date, max_cloud=30, token=None):
    """Search for Sentinel-2 scenes in a bounding box."""
    catalog_url = f"{SENTINELHUB_BASE_URL}/api/v1/catalog/1.0.0/search"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    payload = {
        "bbox": bbox,
        "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
        "collections": ["sentinel-2-l2a"],
        "limit": 100,
        "filter": f"eo:cloud_cover < {max_cloud}",
        "filter-lang": "cql2-text",
    }
    
    try:
        response = requests.post(catalog_url, json=payload, headers=headers)
        response.raise_for_status()
        results = response.json()
        
        items = []
        for feature in results.get('features', []):
            props = feature.get('properties', {})
            items.append({
                'id': feature['id'],
                'datetime': props.get('datetime'),
                'cloud_cover': props.get('eo:cloud_cover', 100),
            })
        
        items.sort(key=lambda x: x['datetime'])
        return items
        
    except Exception as e:
        return []


def download_tile(center_lon, center_lat, dates, token, tile_size=224):
    """
    Download a single tile with multiple temporal frames.
    
    Returns numpy array of shape (18, 224, 224) or None if failed.
    """
    process_url = f"{SENTINELHUB_BASE_URL}/api/v1/process"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    # Calculate bbox
    meters_per_deg_lat = 111000
    meters_per_deg_lon = 111000 * np.cos(np.radians(center_lat))
    
    half_size_m = (tile_size * RESOLUTION) / 2
    half_size_lat = half_size_m / meters_per_deg_lat
    half_size_lon = half_size_m / meters_per_deg_lon
    
    bbox = [
        center_lon - half_size_lon,
        center_lat - half_size_lat,
        center_lon + half_size_lon,
        center_lat + half_size_lat,
    ]
    
    # Evalscript for 6 bands
    evalscript = """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["B02", "B03", "B04", "B8A", "B11", "B12"],
                units: "DN"
            }],
            output: {
                bands: 6,
                sampleType: "INT16"
            }
        };
    }
    
    function evaluatePixel(sample) {
        return [sample.B02, sample.B03, sample.B04, sample.B8A, sample.B11, sample.B12];
    }
    """
    
    all_frames = []
    
    for date_str in dates:
        date = datetime.strptime(date_str[:10], '%Y-%m-%d')
        from_time = date.strftime('%Y-%m-%dT00:00:00Z')
        to_time = date.strftime('%Y-%m-%dT23:59:59Z')
        
        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {"from": from_time, "to": to_time},
                        "maxCloudCoverage": 50
                    }
                }]
            },
            "output": {
                "width": tile_size,
                "height": tile_size,
                "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]
            },
            "evalscript": evalscript
        }
        
        try:
            response = requests.post(process_url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Read TIFF from response
            import io
            with rasterio.open(io.BytesIO(response.content)) as src:
                frame_data = src.read()  # (6, H, W)
                all_frames.append(frame_data)
                
        except Exception as e:
            return None
    
    if len(all_frames) != NUM_FRAMES:
        return None
    
    # Stack all frames: (18, H, W)
    stacked = np.concatenate(all_frames, axis=0)
    return stacked.astype(np.int16)


def save_tile(data, center_lon, center_lat, output_dir, tile_id):
    """Save a tile as GeoTIFF with metadata."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate transform
    meters_per_deg_lat = 111000
    meters_per_deg_lon = 111000 * np.cos(np.radians(center_lat))
    
    half_size_m = (TILE_SIZE * RESOLUTION) / 2
    half_size_lat = half_size_m / meters_per_deg_lat
    half_size_lon = half_size_m / meters_per_deg_lon
    
    transform = rasterio.transform.from_bounds(
        center_lon - half_size_lon,
        center_lat - half_size_lat,
        center_lon + half_size_lon,
        center_lat + half_size_lat,
        TILE_SIZE,
        TILE_SIZE,
    )
    
    profile = {
        'driver': 'GTiff',
        'dtype': 'int16',
        'width': TILE_SIZE,
        'height': TILE_SIZE,
        'count': data.shape[0],
        'crs': CRS.from_epsg(4326),
        'transform': transform,
        'nodata': -9999,
        'compress': 'lzw',
    }
    
    output_path = output_dir / f"tile_{tile_id}.tif"
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(data)
    
    return output_path


# ============================================================================
# Grid generation
# ============================================================================
def generate_grid(bounds, tile_size_deg):
    """
    Generate a grid of tile centers covering the given bounds.
    
    Returns list of (lon, lat, tile_id) tuples.
    """
    tiles = []
    
    # Start from southwest corner
    lat = bounds['south'] + tile_size_deg / 2
    row = 0
    
    while lat < bounds['north']:
        # Adjust longitude step based on latitude (Mercator-like)
        lon_step = tile_size_deg / np.cos(np.radians(lat))
        lon = bounds['west'] + lon_step / 2
        col = 0
        
        while lon < bounds['east']:
            tile_id = f"r{row:04d}_c{col:04d}"
            tiles.append((lon, lat, tile_id))
            lon += lon_step
            col += 1
        
        lat += tile_size_deg
        row += 1
    
    return tiles


def estimate_grid_size(bounds):
    """Estimate the number of tiles needed to cover the bounds."""
    # Average tile size in degrees (at 45° latitude)
    avg_lat = (bounds['south'] + bounds['north']) / 2
    tile_size_deg = TILE_SIZE_METERS / (111000 * np.cos(np.radians(avg_lat)))
    
    width_deg = bounds['east'] - bounds['west']
    height_deg = bounds['north'] - bounds['south']
    
    cols = int(np.ceil(width_deg / tile_size_deg))
    rows = int(np.ceil(height_deg / (TILE_SIZE_METERS / 111000)))
    
    return rows * cols, rows, cols


# ============================================================================
# Main scanning logic
# ============================================================================
def scan_region(bounds, output_dir, start_date=None, end_date=None, max_cloud=30, 
                max_workers=4, resume=True):
    """
    Scan a region and download all tiles.
    
    Args:
        bounds: Dict with west, east, south, north
        output_dir: Output directory
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        max_cloud: Maximum cloud cover percentage
        max_workers: Number of parallel download workers
        resume: Skip already downloaded tiles
    
    Returns:
        Dict with scan statistics
    """
    output_dir = Path(output_dir)
    tiles_dir = output_dir / "tiles"
    tiles_dir.mkdir(parents=True, exist_ok=True)
    
    # Default date range: last 12 months for better temporal coverage
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Calculate tile size in degrees at average latitude
    avg_lat = (bounds['south'] + bounds['north']) / 2
    tile_size_deg = TILE_SIZE_METERS / 111000  # Approximate
    
    # Generate grid
    print(f"Generating grid for region...")
    tiles = generate_grid(bounds, tile_size_deg)
    total_tiles = len(tiles)
    
    print(f"  Total tiles: {total_tiles}")
    print(f"  Date range: {start_date} to {end_date}")
    print(f"  Max cloud cover: {max_cloud}%")
    
    # Load progress if resuming
    progress_file = output_dir / "scan_progress.json"
    completed_tiles = set()
    failed_tiles = set()
    
    if resume and progress_file.exists():
        with open(progress_file, 'r') as f:
            progress = json.load(f)
            completed_tiles = set(progress.get('completed', []))
            failed_tiles = set(progress.get('failed', []))
        print(f"  Resuming: {len(completed_tiles)} completed, {len(failed_tiles)} failed")
    
    # Filter tiles to process
    tiles_to_process = [(lon, lat, tid) for lon, lat, tid in tiles 
                        if tid not in completed_tiles]
    
    print(f"  Tiles to process: {len(tiles_to_process)}")
    
    if not tiles_to_process:
        print("All tiles already processed!")
        return {'total': total_tiles, 'completed': len(completed_tiles), 'failed': len(failed_tiles)}
    
    # Get token
    token = get_sentinelhub_token()
    if not token:
        print("ERROR: Failed to get Sentinel Hub token")
        return None
    
    # Create index file for mapping
    index_file = output_dir / "tile_index.json"
    tile_index = {}
    
    if index_file.exists():
        with open(index_file, 'r') as f:
            tile_index = json.load(f)
    
    # Process tiles
    stats = {'completed': len(completed_tiles), 'failed': len(failed_tiles), 'skipped': 0}
    
    def process_tile(tile_info):
        lon, lat, tile_id = tile_info
        
        try:
            # Refresh token if needed
            token = get_sentinelhub_token()
            
            # Search for scenes
            buffer = 0.1
            bbox = [lon - buffer, lat - buffer, lon + buffer, lat + buffer]
            scenes = search_sentinel2_scenes(bbox, start_date, end_date, max_cloud, token)
            
            if len(scenes) < NUM_FRAMES:
                return (tile_id, 'skipped', f"Only {len(scenes)} scenes available")
            
            # Select evenly spaced frames
            indices = np.linspace(0, len(scenes) - 1, NUM_FRAMES, dtype=int)
            selected_dates = [scenes[i]['datetime'] for i in indices]
            
            # Download tile
            data = download_tile(lon, lat, selected_dates, token)
            
            if data is None:
                return (tile_id, 'failed', "Download failed")
            
            # Save tile
            save_tile(data, lon, lat, tiles_dir, tile_id)
            
            # Return metadata
            metadata = {
                'tile_id': tile_id,
                'center_lon': lon,
                'center_lat': lat,
                'dates': selected_dates,
                'shape': list(data.shape),
            }
            
            return (tile_id, 'completed', metadata)
            
        except Exception as e:
            return (tile_id, 'failed', str(e))
    
    # Process with progress bar
    print(f"\nProcessing tiles...")
    start_time = time.time()
    
    for i, tile_info in enumerate(tiles_to_process):
        result = process_tile(tile_info)
        tile_id, status, info = result
        
        if status == 'completed':
            completed_tiles.add(tile_id)
            tile_index[tile_id] = info
            stats['completed'] += 1
        elif status == 'failed':
            failed_tiles.add(tile_id)
            stats['failed'] += 1
        else:
            stats['skipped'] += 1
        
        # Progress update
        if (i + 1) % 10 == 0 or (i + 1) == len(tiles_to_process):
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (len(tiles_to_process) - i - 1) / rate if rate > 0 else 0
            
            print(f"  [{i+1}/{len(tiles_to_process)}] "
                  f"Completed: {stats['completed']}, Failed: {stats['failed']}, "
                  f"Rate: {rate:.1f} tiles/s, ETA: {eta/60:.1f} min")
        
        # Save progress periodically
        if (i + 1) % 50 == 0:
            with open(progress_file, 'w') as f:
                json.dump({
                    'completed': list(completed_tiles),
                    'failed': list(failed_tiles),
                    'last_update': datetime.now().isoformat(),
                }, f)
            
            with open(index_file, 'w') as f:
                json.dump(tile_index, f, indent=2)
        
        # Rate limiting to avoid API throttling
        time.sleep(0.5)
    
    # Final save
    with open(progress_file, 'w') as f:
        json.dump({
            'completed': list(completed_tiles),
            'failed': list(failed_tiles),
            'last_update': datetime.now().isoformat(),
            'bounds': bounds,
            'start_date': start_date,
            'end_date': end_date,
        }, f, indent=2)
    
    with open(index_file, 'w') as f:
        json.dump(tile_index, f, indent=2)
    
    # Create metadata file
    metadata = {
        'region_bounds': bounds,
        'date_range': {'start': start_date, 'end': end_date},
        'tile_size_pixels': TILE_SIZE,
        'resolution_meters': RESOLUTION,
        'num_frames': NUM_FRAMES,
        'num_bands': NUM_BANDS,
        'total_tiles': total_tiles,
        'completed_tiles': len(completed_tiles),
        'failed_tiles': len(failed_tiles),
        'created_at': datetime.now().isoformat(),
    }
    
    with open(output_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return stats


# ============================================================================
# Main entry point
# ============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Scan Europe with Sentinel-2 data for crop classification"
    )
    parser.add_argument("--output", type=str, default="./data/europe_scan",
                        help="Output directory for tiles")
    parser.add_argument("--region", type=str, default="europe",
                        choices=list(REGIONS.keys()),
                        help="Region to scan")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--max-cloud", type=int, default=30, help="Max cloud cover %%")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers")
    parser.add_argument("--no-resume", action="store_true", help="Start fresh, don't resume")
    parser.add_argument("--test", action="store_true", help="Use small test region")
    parser.add_argument("--estimate", action="store_true", help="Only estimate grid size")
    
    args = parser.parse_args()
    
    # Select region
    if args.test:
        region_name = 'test'
    else:
        region_name = args.region
    
    bounds = REGIONS[region_name]
    
    print("=" * 60)
    print(f"Europe Sentinel-2 Scanner")
    print("=" * 60)
    print(f"Region: {region_name}")
    print(f"Bounds: W={bounds['west']}, E={bounds['east']}, S={bounds['south']}, N={bounds['north']}")
    
    # Estimate grid size
    total_tiles, rows, cols = estimate_grid_size(bounds)
    print(f"Estimated grid: {rows} rows × {cols} cols = {total_tiles} tiles")
    
    if args.estimate:
        print("\nEstimate only mode. Exiting.")
        return
    
    # Resolve output path
    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = Path(__file__).resolve().parents[1] / args.output
    
    output_dir = output_dir / region_name
    print(f"Output directory: {output_dir}")
    
    # Run scan
    print("\n" + "-" * 60)
    stats = scan_region(
        bounds=bounds,
        output_dir=output_dir,
        start_date=args.start_date,
        end_date=args.end_date,
        max_cloud=args.max_cloud,
        max_workers=args.workers,
        resume=not args.no_resume,
    )
    
    if stats:
        print("\n" + "=" * 60)
        print("Scan completed!")
        print(f"  Completed: {stats['completed']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Skipped: {stats.get('skipped', 0)}")
        print(f"  Output: {output_dir}")
        print("=" * 60)


if __name__ == "__main__":
    main()
