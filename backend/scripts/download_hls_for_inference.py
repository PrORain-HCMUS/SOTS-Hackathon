#!/usr/bin/env python
"""
Download Sentinel-2 data via Sentinel Hub API for Prithvi model inference.

This script downloads Sentinel-2 data from Sentinel Hub, processes it to match
the input format required by the multi-temporal crop classification model.

Input requirements:
- Shape: (18, H, W) = 6 bands × 3 time frames stacked
- Bands per frame: Blue, Green, Red, NIR, SWIR1, SWIR2
- Dtype: int16
- Resolution: 30m

Usage:
    python download_hls_for_inference.py --lat 10.5 --lon 106.7 --output /tmp/hls_input
    
Environment:
    Requires Sentinel Hub credentials. Set environment variables:
    - SENTINELHUB_CLIENT_ID
    - SENTINELHUB_CLIENT_SECRET
    
    Or use .env file in backend directory.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.crs import CRS
from rasterio.windows import from_bounds
import requests

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Load .env file if exists
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


# Sentinel-2 band mapping for Prithvi model
# Model expects: Blue, Green, Red, NIR, SWIR1, SWIR2
SENTINEL2_BANDS = {
    'Blue': 'B02',
    'Green': 'B03',
    'Red': 'B04',
    'NIR': 'B8A',
    'SWIR1': 'B11',
    'SWIR2': 'B12',
}

# Target CRS for the model (EPSG:5070 - NAD83 / Conus Albers)
# For global use, we'll use UTM or keep original CRS
TARGET_CRS = CRS.from_epsg(4326)  # WGS84 for global compatibility
TARGET_RESOLUTION = 30  # meters
TILE_SIZE = 224  # pixels

# Sentinel Hub configuration
SENTINELHUB_CLIENT_ID = os.environ.get('SENTINELHUB_CLIENT_ID', '81105a4d-5756-4f7c-b6da-87abeb288de5')
SENTINELHUB_CLIENT_SECRET = os.environ.get('SENTINELHUB_CLIENT_SECRET', 'M7ea7lyT4nHaRTQvG6N4bvlzwb573Bmz')
SENTINELHUB_BASE_URL = os.environ.get('SENTINELHUB_BASE_URL', 'https://services.sentinel-hub.com')


def get_sentinelhub_token():
    """Get OAuth2 token from Sentinel Hub."""
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
        return token_data.get('access_token')
    except Exception as e:
        print(f"Error getting Sentinel Hub token: {e}")
        return None


def search_sentinel2_catalog(bbox, start_date, end_date, max_cloud=30, token=None):
    """Search for Sentinel-2 data using Sentinel Hub Catalog API."""
    catalog_url = f"{SENTINELHUB_BASE_URL}/api/v1/catalog/1.0.0/search"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    # Convert bbox to proper format [west, south, east, north]
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
                'bbox': feature.get('bbox'),
            })
        
        # Sort by date
        items.sort(key=lambda x: x['datetime'])
        return items
        
    except Exception as e:
        print(f"Error searching catalog: {e}")
        return []


def download_sentinel2_data(center_lon, center_lat, dates, output_dir, token, tile_size=224):
    """
    Download Sentinel-2 data for multiple dates using Sentinel Hub Process API.
    
    Returns list of downloaded file paths for each date.
    """
    process_url = f"{SENTINELHUB_BASE_URL}/api/v1/process"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    # Calculate bbox in meters (approximately)
    # 1 degree latitude ≈ 111km, 1 degree longitude varies with latitude
    meters_per_deg_lat = 111000
    meters_per_deg_lon = 111000 * np.cos(np.radians(center_lat))
    
    half_size_m = (tile_size * TARGET_RESOLUTION) / 2
    half_size_lat = half_size_m / meters_per_deg_lat
    half_size_lon = half_size_m / meters_per_deg_lon
    
    bbox = [
        center_lon - half_size_lon,
        center_lat - half_size_lat,
        center_lon + half_size_lon,
        center_lat + half_size_lat,
    ]
    
    # Evalscript to get all 6 bands we need
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
    
    downloaded_files = []
    
    for i, date_str in enumerate(dates):
        # Parse date and create time range (single day)
        date = datetime.strptime(date_str[:10], '%Y-%m-%d')
        from_time = date.strftime('%Y-%m-%dT00:00:00Z')
        to_time = date.strftime('%Y-%m-%dT23:59:59Z')
        
        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    }
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": from_time,
                            "to": to_time
                        },
                        "maxCloudCoverage": 50
                    }
                }]
            },
            "output": {
                "width": tile_size,
                "height": tile_size,
                "responses": [{
                    "identifier": "default",
                    "format": {
                        "type": "image/tiff"
                    }
                }]
            },
            "evalscript": evalscript
        }
        
        try:
            print(f"  Downloading frame {i+1}/{len(dates)} ({date_str[:10]})...")
            response = requests.post(process_url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Save to file
            output_path = output_dir / f"frame_{i}.tif"
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            downloaded_files.append(output_path)
            print(f"    Saved: {output_path}")
            
        except Exception as e:
            print(f"  Error downloading frame {i}: {e}")
            if hasattr(response, 'text'):
                print(f"  Response: {response.text[:500]}")
    
    return downloaded_files


def merge_sentinel2_frames(frame_files, output_path, center_lon, center_lat, tile_size=224):
    """
    Merge multiple Sentinel-2 frames (each with 6 bands) into a single multi-band TIF.
    
    Output shape: (num_bands * num_frames, tile_size, tile_size) = (18, 224, 224)
    """
    all_bands = []
    
    for frame_path in frame_files:
        with rasterio.open(frame_path) as src:
            # Read all 6 bands from this frame
            for band_idx in range(1, src.count + 1):
                data = src.read(band_idx)
                all_bands.append(data.astype(np.int16))
    
    # Stack all bands: (18, H, W)
    stacked = np.stack(all_bands, axis=0)
    
    # Calculate transform
    meters_per_deg_lat = 111000
    meters_per_deg_lon = 111000 * np.cos(np.radians(center_lat))
    
    half_size_m = (tile_size * TARGET_RESOLUTION) / 2
    half_size_lat = half_size_m / meters_per_deg_lat
    half_size_lon = half_size_m / meters_per_deg_lon
    
    transform = rasterio.transform.from_bounds(
        center_lon - half_size_lon,
        center_lat - half_size_lat,
        center_lon + half_size_lon,
        center_lat + half_size_lat,
        tile_size,
        tile_size,
    )
    
    # Write output
    profile = {
        'driver': 'GTiff',
        'dtype': 'int16',
        'width': tile_size,
        'height': tile_size,
        'count': len(all_bands),
        'crs': TARGET_CRS,
        'transform': transform,
        'nodata': -9999,
        'compress': 'lzw',
    }
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(stacked)
    
    print(f"Created merged file: {output_path}")
    print(f"  Shape: {stacked.shape}")
    
    return output_path


def create_sample_data(output_dir, center_lon, center_lat, tile_size=224, num_frames=3):
    """
    Create sample synthetic data for testing when HLS data is not available.
    This generates random data with the correct format.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate synthetic data
    num_bands = 6  # Blue, Green, Red, NIR, SWIR1, SWIR2
    total_bands = num_bands * num_frames
    
    # Create realistic-looking synthetic data
    np.random.seed(42)
    data = np.random.randint(100, 5000, size=(total_bands, tile_size, tile_size), dtype=np.int16)
    
    # Calculate transform
    from pyproj import Transformer
    transformer = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    center_x, center_y = transformer.transform(center_lon, center_lat)
    
    half_size = (tile_size * TARGET_RESOLUTION) / 2
    transform = rasterio.transform.from_bounds(
        center_x - half_size,
        center_y - half_size,
        center_x + half_size,
        center_y + half_size,
        tile_size,
        tile_size,
    )
    
    output_path = output_dir / "sample_merged.tif"
    
    profile = {
        'driver': 'GTiff',
        'dtype': 'int16',
        'width': tile_size,
        'height': tile_size,
        'count': total_bands,
        'crs': TARGET_CRS,
        'transform': transform,
        'nodata': -9999,
        'compress': 'lzw',
    }
    
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(data)
    
    print(f"Created sample data: {output_path}")
    print(f"  Shape: {data.shape}")
    print(f"  Dtype: {data.dtype}")
    print(f"  Center: ({center_lon}, {center_lat})")
    
    return output_path


def download_sentinel2_for_inference(center_lon, center_lat, output_dir, start_date=None, end_date=None, 
                                      num_frames=3, max_cloud=30):
    """
    Download Sentinel-2 data via Sentinel Hub for a given location and time range.
    
    Args:
        center_lon: Center longitude
        center_lat: Center latitude  
        output_dir: Output directory
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        num_frames: Number of temporal frames (default 3)
        max_cloud: Maximum cloud cover percentage
    
    Returns:
        Path to merged TIF file
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Default date range: last 6 months
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    
    # Create bbox around center point
    buffer = 0.1  # degrees
    bbox = [center_lon - buffer, center_lat - buffer, center_lon + buffer, center_lat + buffer]
    
    print(f"Authenticating with Sentinel Hub...")
    token = get_sentinelhub_token()
    
    if not token:
        print("Failed to authenticate. Creating synthetic sample data...")
        return create_sample_data(output_dir, center_lon, center_lat)
    
    print(f"Searching Sentinel-2 data...")
    print(f"  Location: ({center_lon}, {center_lat})")
    print(f"  Date range: {start_date} to {end_date}")
    print(f"  Max cloud cover: {max_cloud}%")
    
    # Search for available data
    items = search_sentinel2_catalog(bbox, start_date, end_date, max_cloud, token)
    
    if len(items) < num_frames:
        print(f"Warning: Only found {len(items)} scenes, need {num_frames}")
        print("Creating synthetic sample data instead...")
        return create_sample_data(output_dir, center_lon, center_lat)
    
    # Select evenly spaced frames
    indices = np.linspace(0, len(items) - 1, num_frames, dtype=int)
    selected_items = [items[i] for i in indices]
    
    print(f"Selected {num_frames} scenes:")
    for item in selected_items:
        print(f"  - {item['id']} ({item['datetime']}, cloud: {item['cloud_cover']:.1f}%)")
    
    # Download frames
    temp_dir = output_dir / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    dates = [item['datetime'] for item in selected_items]
    frame_files = download_sentinel2_data(center_lon, center_lat, dates, temp_dir, token)
    
    if len(frame_files) < num_frames:
        print(f"Failed to download all frames. Creating synthetic sample data...")
        return create_sample_data(output_dir, center_lon, center_lat)
    
    # Merge all frames into single file
    output_path = output_dir / "sentinel2_merged.tif"
    merge_sentinel2_frames(frame_files, output_path, center_lon, center_lat)
    
    # Cleanup temp files
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    return output_path


def run_inference(input_path, output_dir):
    """Run model inference on the downloaded data."""
    hls_dir = Path(__file__).resolve().parents[1] / "ml" / "hls-foundation-os"
    config_path = hls_dir / "configs" / "multi_temporal_crop_classification.py"
    ckpt_path = Path(__file__).resolve().parents[1] / "ml" / "weights" / "multi_temporal_crop_classification_Prithvi_100M.pth"
    
    input_dir = Path(input_path).parent
    
    cmd = f"""cd {hls_dir} && python model_inference.py \
        -config {config_path} \
        -ckpt {ckpt_path} \
        -input {input_dir} \
        -output {output_dir} \
        -input_type tif \
        -bands 0 1 2 3 4 5 \
        -device cpu"""
    
    print("\nRunning inference...")
    print(f"Command: {cmd}")
    
    import subprocess
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Inference completed successfully!")
        print(result.stdout)
    else:
        print("Inference failed:")
        print(result.stderr)
    
    return result.returncode == 0


def visualize_results(input_path, pred_path, output_dir):
    """Visualize input and prediction."""
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    
    output_dir = Path(output_dir)
    
    # Class colors and names
    CLASS_COLORS = {
        -1: [0, 0, 0],
        0: [34, 139, 34],
        1: [0, 100, 0],
        2: [255, 215, 0],
        3: [144, 238, 144],
        4: [0, 206, 209],
        5: [128, 128, 128],
        6: [0, 0, 255],
        7: [210, 180, 140],
        8: [186, 85, 211],
        9: [245, 222, 179],
        10: [255, 255, 255],
        11: [255, 140, 0],
        12: [169, 169, 169],
    }
    
    CLASS_NAMES = [
        "Natural Vegetation", "Forest", "Corn", "Soybeans", "Wetlands",
        "Developed/Barren", "Open Water", "Winter Wheat", "Alfalfa",
        "Fallow/Idle Cropland", "Cotton", "Sorghum", "Other",
    ]
    
    # Read input (use first 3 bands as RGB)
    with rasterio.open(input_path) as src:
        # Bands 2, 1, 0 (Red, Green, Blue from first frame)
        rgb = np.stack([src.read(3), src.read(2), src.read(1)], axis=-1).astype(np.float32)
    
    # Percentile stretch
    def stretch(img, p_low=2, p_high=98):
        out = np.zeros_like(img, dtype=np.float32)
        for i in range(3):
            lo, hi = np.percentile(img[..., i], (p_low, p_high))
            out[..., i] = np.clip((img[..., i] - lo) / (hi - lo + 1e-6), 0, 1)
        return out
    
    rgb_vis = stretch(rgb)
    
    # Read prediction
    with rasterio.open(pred_path) as src:
        pred = src.read(1)
    
    # Convert prediction to RGB
    h, w = pred.shape
    pred_rgb = np.zeros((h, w, 3), dtype=np.uint8)
    for class_id, color in CLASS_COLORS.items():
        mask = pred == class_id
        pred_rgb[mask] = color
    
    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    axes[0].imshow(rgb_vis)
    axes[0].set_title("Input (RGB)")
    axes[0].axis("off")
    
    axes[1].imshow(pred_rgb)
    axes[1].set_title("Crop Classification")
    axes[1].axis("off")
    
    # Add legend
    legend_elements = [Patch(facecolor=np.array(CLASS_COLORS[i])/255, label=CLASS_NAMES[i]) 
                       for i in range(13)]
    fig.legend(handles=legend_elements, loc='center right', bbox_to_anchor=(1.15, 0.5), fontsize=8)
    
    plt.tight_layout()
    
    output_path = output_dir / "result_visualization.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Saved visualization: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Download HLS data and run crop classification inference")
    parser.add_argument("--lat", type=float, default=40.0, help="Center latitude")
    parser.add_argument("--lon", type=float, default=-100.0, help="Center longitude")
    parser.add_argument("--output", type=str, default="/tmp/hls_inference", help="Output directory")
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--max-cloud", type=int, default=30, help="Max cloud cover %%")
    parser.add_argument("--sample", action="store_true", help="Use synthetic sample data (skip download)")
    parser.add_argument("--skip-inference", action="store_true", help="Skip inference step")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Sentinel-2 Data Download and Inference Pipeline")
    print("=" * 60)
    
    # Step 1: Download or create sample data
    if args.sample:
        print("\nStep 1: Creating synthetic sample data...")
        input_path = create_sample_data(output_dir / "input", args.lon, args.lat)
    else:
        print("\nStep 1: Downloading Sentinel-2 data via Sentinel Hub...")
        input_path = download_sentinel2_for_inference(
            args.lon, args.lat,
            output_dir / "input",
            args.start_date, args.end_date,
            max_cloud=args.max_cloud,
        )
    
    if args.skip_inference:
        print("\nSkipping inference (--skip-inference flag)")
        return
    
    # Step 2: Run inference
    print("\nStep 2: Running model inference...")
    pred_dir = output_dir / "predictions"
    pred_dir.mkdir(exist_ok=True)
    
    success = run_inference(input_path, pred_dir)
    
    if success:
        # Step 3: Visualize results
        print("\nStep 3: Visualizing results...")
        pred_files = list(pred_dir.glob("*_pred.tif"))
        if pred_files:
            visualize_results(input_path, pred_files[0], output_dir)
    
    print("\n" + "=" * 60)
    print("Pipeline completed!")
    print(f"Output directory: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
