"""
Sentinel Hub API client for fetching Sentinel-2 data.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

import numpy as np
from sentinelhub import (
    SHConfig,
    SentinelHubCatalog,
    SentinelHubRequest,
    DataCollection,
    MimeType,
    CRS,
    BBox,
    bbox_to_dimensions,
    Geometry,
)

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def get_sh_config() -> SHConfig:
    """Get Sentinel Hub configuration from settings."""
    settings = get_settings()
    config = SHConfig()
    config.sh_client_id = settings.sentinelhub_client_id
    config.sh_client_secret = settings.sentinelhub_client_secret
    config.sh_base_url = settings.sentinelhub_base_url
    return config


# Evalscript for fetching B02, B03, B04, B08 with SCL cloud masking
EVALSCRIPT_MONTHLY_COMPOSITE = """
//VERSION=3
function setup() {
    return {
        input: [{
            bands: ["B02", "B03", "B04", "B08", "SCL"],
            units: "DN"
        }],
        output: {
            bands: 4,
            sampleType: "FLOAT32"
        },
        mosaicking: "ORBIT"
    };
}

function isCloudOrShadow(scl) {
    // SCL classes: 3=cloud shadow, 8=cloud medium, 9=cloud high, 10=thin cirrus
    return scl === 3 || scl === 8 || scl === 9 || scl === 10;
}

function evaluatePixel(samples) {
    // Find first clear observation
    for (let i = 0; i < samples.length; i++) {
        if (!isCloudOrShadow(samples[i].SCL)) {
            return [
                samples[i].B02 / 10000.0,
                samples[i].B03 / 10000.0,
                samples[i].B04 / 10000.0,
                samples[i].B08 / 10000.0
            ];
        }
    }
    // If all cloudy, return zeros (masked)
    return [0, 0, 0, 0];
}
"""


class SentinelHubClient:
    """Client for Sentinel Hub API operations."""

    def __init__(self):
        self.config = get_sh_config()
        self.catalog = SentinelHubCatalog(config=self.config)

    def search_scenes(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 80.0,
        collection: str = "sentinel-2-l2a",
    ) -> List[dict]:
        """
        Search for Sentinel-2 scenes in the given bbox and time range.
        
        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            start_date: Start of time range
            end_date: End of time range
            max_cloud_cover: Maximum cloud cover percentage
            collection: Data collection name
            
        Returns:
            List of scene metadata dictionaries
        """
        time_interval = (
            start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        search_iterator = self.catalog.search(
            DataCollection.SENTINEL2_L2A,
            bbox=BBox(bbox, crs=CRS.WGS84),
            time=time_interval,
            filter=f"eo:cloud_cover < {max_cloud_cover}",
        )

        scenes = []
        for result in search_iterator:
            scene_id = result.get("id", "")
            properties = result.get("properties", {})
            geometry = result.get("geometry", {})

            scenes.append({
                "scene_id": scene_id,
                "sensing_time": properties.get("datetime"),
                "cloud_cover": properties.get("eo:cloud_cover"),
                "footprint": geometry,
                "collection": collection,
                "provider": "sentinel-hub",
            })

        logger.info(f"Found {len(scenes)} scenes for bbox {bbox}")
        return scenes

    def fetch_monthly_composite(
        self,
        bbox: Tuple[float, float, float, float],
        year: int,
        month: int,
        size: Tuple[int, int] = (61, 61),
    ) -> np.ndarray:
        """
        Fetch a monthly cloud-masked composite for the given bbox.
        
        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            year: Year
            month: Month (1-12)
            size: Output size (width, height)
            
        Returns:
            numpy array of shape (4, H, W) with bands B02, B03, B04, B08
        """
        # Calculate time range for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)

        sh_bbox = BBox(bbox, crs=CRS.WGS84)

        request = SentinelHubRequest(
            evalscript=EVALSCRIPT_MONTHLY_COMPOSITE,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=(
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                    ),
                    mosaicking_order="leastCC",
                )
            ],
            responses=[
                SentinelHubRequest.output_response("default", MimeType.TIFF),
            ],
            bbox=sh_bbox,
            size=size,
            config=self.config,
        )

        logger.info(
            f"Fetching monthly composite for {year}-{month:02d}, bbox={bbox}, size={size}"
        )
        data = request.get_data()[0]

        # data shape is (H, W, 4), transpose to (4, H, W)
        if data.ndim == 3:
            data = np.transpose(data, (2, 0, 1))

        return data.astype(np.float32)

    def fetch_monthly_stack(
        self,
        bbox: Tuple[float, float, float, float],
        end_year: int,
        end_month: int,
        window_len: int = 6,
        size: Tuple[int, int] = (61, 61),
    ) -> np.ndarray:
        """
        Fetch a stack of monthly composites for S4A model input.
        
        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)
            end_year: End year
            end_month: End month
            window_len: Number of months to fetch
            size: Output size (width, height)
            
        Returns:
            numpy array of shape (1, T, C, H, W) where T=window_len, C=4
        """
        composites = []

        for i in range(window_len - 1, -1, -1):
            # Calculate year/month going backwards
            month_offset = end_month - 1 - i
            year = end_year + (month_offset // 12)
            month = (month_offset % 12) + 1

            composite = self.fetch_monthly_composite(bbox, year, month, size)
            composites.append(composite)

        # Stack: (T, C, H, W)
        stack = np.stack(composites, axis=0)
        # Add batch dimension: (1, T, C, H, W)
        stack = np.expand_dims(stack, axis=0)

        logger.info(f"Created monthly stack with shape {stack.shape}")
        return stack


_sh_client: Optional[SentinelHubClient] = None


def get_sentinelhub_client() -> SentinelHubClient:
    """Get singleton Sentinel Hub client instance."""
    global _sh_client
    if _sh_client is None:
        _sh_client = SentinelHubClient()
    return _sh_client
