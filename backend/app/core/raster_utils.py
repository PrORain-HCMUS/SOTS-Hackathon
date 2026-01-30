"""
Raster I/O utilities for GeoTIFF processing.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_bounds
from rasterio.enums import Resampling

logger = logging.getLogger(__name__)


def write_geotiff(
    data: np.ndarray,
    output_path: Union[str, Path],
    bbox: Tuple[float, float, float, float],
    crs: str = "EPSG:4326",
    nodata: Optional[float] = None,
    dtype: Optional[str] = None,
    tiled: bool = True,
    blocksize: int = 256,
    compress: str = "deflate",
) -> Path:
    """
    Write a numpy array to a GeoTIFF file.
    
    Args:
        data: Array of shape (C, H, W) or (H, W)
        output_path: Output file path
        bbox: (min_lon, min_lat, max_lon, max_lat)
        crs: Coordinate reference system
        nodata: NoData value
        dtype: Output data type (auto-detected if None)
        tiled: Whether to create tiled TIFF
        blocksize: Tile size
        compress: Compression method
        
    Returns:
        Path to output file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Handle 2D arrays
    if data.ndim == 2:
        data = np.expand_dims(data, axis=0)

    count, height, width = data.shape
    min_lon, min_lat, max_lon, max_lat = bbox

    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)

    if dtype is None:
        dtype = str(data.dtype)

    profile = {
        "driver": "GTiff",
        "dtype": dtype,
        "width": width,
        "height": height,
        "count": count,
        "crs": CRS.from_string(crs),
        "transform": transform,
        "tiled": tiled,
        "blockxsize": blocksize if tiled else None,
        "blockysize": blocksize if tiled else None,
        "compress": compress,
    }

    if nodata is not None:
        profile["nodata"] = nodata

    # Remove None values
    profile = {k: v for k, v in profile.items() if v is not None}

    logger.info(f"Writing GeoTIFF to {output_path}, shape={data.shape}")
    with rasterio.open(output_path, "w", **profile) as dst:
        for i in range(count):
            dst.write(data[i], i + 1)

    return output_path


def write_cog(
    data: np.ndarray,
    output_path: Union[str, Path],
    bbox: Tuple[float, float, float, float],
    crs: str = "EPSG:4326",
    nodata: Optional[float] = None,
    dtype: Optional[str] = None,
    overview_levels: Optional[list] = None,
) -> Path:
    """
    Write a numpy array to a Cloud-Optimized GeoTIFF (COG).
    
    Args:
        data: Array of shape (C, H, W) or (H, W)
        output_path: Output file path
        bbox: (min_lon, min_lat, max_lon, max_lat)
        crs: Coordinate reference system
        nodata: NoData value
        dtype: Output data type
        overview_levels: Overview levels (default: [2, 4, 8, 16])
        
    Returns:
        Path to output file
    """
    output_path = Path(output_path)
    
    if overview_levels is None:
        overview_levels = [2, 4, 8, 16]

    # First write to temp file
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    write_geotiff(
        data=data,
        output_path=tmp_path,
        bbox=bbox,
        crs=crs,
        nodata=nodata,
        dtype=dtype,
        tiled=True,
    )

    # Add overviews and convert to COG
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(tmp_path, "r+") as src:
        # Build overviews
        src.build_overviews(overview_levels, Resampling.nearest)
        src.update_tags(ns="rio_overview", resampling="nearest")

    # Copy to final location with COG profile
    with rasterio.open(tmp_path) as src:
        profile = src.profile.copy()
        profile.update(
            driver="GTiff",
            tiled=True,
            blockxsize=256,
            blockysize=256,
            compress="deflate",
            interleave="band",
        )

        with rasterio.open(output_path, "w", **profile) as dst:
            for i in range(1, src.count + 1):
                dst.write(src.read(i), i)
            
            # Copy overviews
            if src.overviews(1):
                dst.build_overviews(overview_levels, Resampling.nearest)

    # Cleanup temp file
    tmp_path.unlink(missing_ok=True)

    logger.info(f"Created COG at {output_path}")
    return output_path


def read_geotiff(
    input_path: Union[str, Path],
) -> Tuple[np.ndarray, dict]:
    """
    Read a GeoTIFF file.
    
    Args:
        input_path: Path to GeoTIFF file
        
    Returns:
        Tuple of (data array, metadata dict)
    """
    input_path = Path(input_path)

    with rasterio.open(input_path) as src:
        data = src.read()
        bounds = src.bounds
        metadata = {
            "crs": str(src.crs),
            "bbox": [bounds.left, bounds.bottom, bounds.right, bounds.top],
            "width": src.width,
            "height": src.height,
            "count": src.count,
            "dtype": str(src.dtypes[0]),
            "transform": list(src.transform),
            "nodata": src.nodata,
        }

    return data, metadata


def calculate_pixel_area_ha(
    bbox: Tuple[float, float, float, float],
    width: int,
    height: int,
) -> float:
    """
    Calculate approximate pixel area in hectares for a given bbox and resolution.
    
    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat) in degrees
        width: Number of pixels in x direction
        height: Number of pixels in y direction
        
    Returns:
        Pixel area in hectares
    """
    import math

    min_lon, min_lat, max_lon, max_lat = bbox

    # Approximate conversion at center latitude
    center_lat = (min_lat + max_lat) / 2
    lat_rad = math.radians(center_lat)

    # Meters per degree
    meters_per_deg_lat = 111320  # approximately constant
    meters_per_deg_lon = 111320 * math.cos(lat_rad)

    # Total extent in meters
    extent_x_m = (max_lon - min_lon) * meters_per_deg_lon
    extent_y_m = (max_lat - min_lat) * meters_per_deg_lat

    # Pixel size in meters
    pixel_x_m = extent_x_m / width
    pixel_y_m = extent_y_m / height

    # Pixel area in square meters, then convert to hectares
    pixel_area_m2 = pixel_x_m * pixel_y_m
    pixel_area_ha = pixel_area_m2 / 10000.0

    return pixel_area_ha
