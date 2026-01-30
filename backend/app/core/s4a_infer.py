"""
S4A ConvLSTM model inference for crop classification.

This module provides functions to:
- Load pretrained S4A ConvLSTM model from checkpoint
- Fetch monthly stack from Sentinel Hub
- Apply normalization
- Run inference to get pixel-wise classification map
- Calculate area statistics from prediction map
"""

import logging
import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import numpy as np

from app.core.config import get_settings
from app.core.spaces import get_spaces_client
from app.core.sentinelhub_client import get_sentinelhub_client
from app.core.raster_utils import calculate_pixel_area_ha

logger = logging.getLogger(__name__)

# Default crop class mapping (should match crop_classes table)
DEFAULT_CLASS_NAMES = {
    0: "unknown",
    1: "rice",
    2: "maize",
    3: "cassava",
    4: "sugarcane",
    5: "vegetables",
    6: "fruit_trees",
    7: "coffee",
    8: "rubber",
    9: "forest",
    10: "water",
    11: "urban",
    12: "barren",
}


class S4AModelNotFoundError(Exception):
    """Raised when S4A model or vendor code is not available."""
    pass


def _get_model_cache_path(weights_s3_key: str) -> Path:
    """Get local cache path for model weights."""
    settings = get_settings()
    cache_dir = Path(settings.model_cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Use the s3 key filename as cache filename
    filename = Path(weights_s3_key).name
    return cache_dir / filename


def load_s4a_model(
    checkpoint_path: str,
    device: str = "cpu",
) -> Any:
    """
    Load S4A ConvLSTM model from checkpoint.
    
    Args:
        checkpoint_path: Path to model checkpoint file
        device: Device to load model on ('cpu' or 'cuda')
        
    Returns:
        Loaded model instance
        
    Raises:
        S4AModelNotFoundError: If S4A vendor code is not available
    """
    try:
        # Try to import S4A vendor model
        from ml.s4a_vendor.models import ConvLSTM
    except ImportError as e:
        logger.error(
            "S4A vendor code not found. Please copy S4A model code to ml/s4a_vendor/. "
            f"Import error: {e}"
        )
        raise S4AModelNotFoundError(
            "S4A vendor code not available. "
            "Please copy the S4A ConvLSTM model code to ml/s4a_vendor/"
        ) from e

    logger.info(f"Loading S4A model from {checkpoint_path}")
    
    try:
        import torch
        model = ConvLSTM.load_from_checkpoint(
            checkpoint_path,
            map_location=device,
        )
        model.eval()
        model.to(device)
        return model
    except Exception as e:
        logger.error(f"Failed to load S4A model: {e}")
        raise


def download_model_weights(weights_s3_key: str) -> Path:
    """
    Download model weights from Spaces to local cache.
    
    Args:
        weights_s3_key: S3 key for model weights
        
    Returns:
        Path to local cached weights file
    """
    cache_path = _get_model_cache_path(weights_s3_key)
    
    if cache_path.exists():
        logger.info(f"Using cached model weights at {cache_path}")
        return cache_path
    
    logger.info(f"Downloading model weights from s3://{weights_s3_key}")
    spaces = get_spaces_client()
    spaces.download_file(weights_s3_key, cache_path)
    
    return cache_path


def fetch_monthly_stack_sentinelhub(
    bbox: Tuple[float, float, float, float],
    end_year: int,
    end_month: int,
    window_len: int = 6,
    size: Tuple[int, int] = (61, 61),
) -> np.ndarray:
    """
    Fetch monthly composite stack from Sentinel Hub for S4A input.
    
    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat)
        end_year: End year
        end_month: End month (1-12)
        window_len: Number of months (default 6)
        size: Output size (width, height)
        
    Returns:
        numpy array of shape (1, T, C, H, W) where T=window_len, C=4
        Bands are B02, B03, B04, B08
    """
    sh_client = get_sentinelhub_client()
    return sh_client.fetch_monthly_stack(
        bbox=bbox,
        end_year=end_year,
        end_month=end_month,
        window_len=window_len,
        size=size,
    )


def load_norm_stats(run_path: Optional[str] = None) -> Optional[Dict[str, np.ndarray]]:
    """
    Load normalization statistics from run path.
    
    Args:
        run_path: Path to training run directory containing norm_stats.npz
        
    Returns:
        Dict with 'mean' and 'std' arrays, or None if not found
    """
    if run_path is None:
        logger.warning("No run_path provided for normalization stats")
        return None
    
    norm_path = Path(run_path) / "norm_stats.npz"
    
    if not norm_path.exists():
        logger.warning(f"Normalization stats not found at {norm_path}")
        return None
    
    try:
        data = np.load(norm_path)
        return {
            "mean": data["mean"],
            "std": data["std"],
        }
    except Exception as e:
        logger.warning(f"Failed to load norm stats: {e}")
        return None


def apply_norm(
    data: np.ndarray,
    norm_stats: Optional[Dict[str, np.ndarray]] = None,
) -> np.ndarray:
    """
    Apply normalization to input data.
    
    Args:
        data: Input array of shape (1, T, C, H, W)
        norm_stats: Dict with 'mean' and 'std' arrays
        
    Returns:
        Normalized array of same shape
    """
    if norm_stats is None:
        logger.warning("No normalization stats provided, returning unnormalized data")
        return data
    
    mean = norm_stats["mean"]
    std = norm_stats["std"]
    
    # Reshape for broadcasting: (1, 1, C, 1, 1)
    if mean.ndim == 1:
        mean = mean.reshape(1, 1, -1, 1, 1)
        std = std.reshape(1, 1, -1, 1, 1)
    
    # Avoid division by zero
    std = np.where(std == 0, 1, std)
    
    normalized = (data - mean) / std
    return normalized.astype(np.float32)


def infer_pixel_map(
    model: Any,
    input_tensor: np.ndarray,
    device: str = "cpu",
) -> np.ndarray:
    """
    Run inference to get pixel-wise classification map.
    
    Args:
        model: Loaded S4A model
        input_tensor: Input array of shape (1, T, C, H, W)
        device: Device for inference
        
    Returns:
        Prediction map of shape (H, W) with class indices (uint16)
    """
    try:
        import torch
    except ImportError:
        raise S4AModelNotFoundError("PyTorch not available for inference")
    
    logger.info(f"Running inference on input shape {input_tensor.shape}")
    
    # Convert to torch tensor
    x = torch.from_numpy(input_tensor).float().to(device)
    
    with torch.no_grad():
        # Model output shape: (1, num_classes, H, W)
        logits = model(x)
        
        # Get class predictions via argmax
        pred = torch.argmax(logits, dim=1)  # (1, H, W)
        pred_map = pred.squeeze(0).cpu().numpy()  # (H, W)
    
    return pred_map.astype(np.uint16)


def area_stats_from_map(
    pred_map: np.ndarray,
    bbox: Tuple[float, float, float, float],
    class_names: Optional[Dict[int, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Calculate area statistics from prediction map.
    
    Args:
        pred_map: Prediction map of shape (H, W) with class indices
        bbox: (min_lon, min_lat, max_lon, max_lat)
        class_names: Optional mapping of class_id to class_name
        
    Returns:
        List of dicts with class_id, class_name, pixel_count, area_ha
    """
    if class_names is None:
        class_names = DEFAULT_CLASS_NAMES
    
    height, width = pred_map.shape
    pixel_area_ha = calculate_pixel_area_ha(bbox, width, height)
    
    # Count pixels per class
    unique_classes, counts = np.unique(pred_map, return_counts=True)
    
    stats = []
    for class_id, pixel_count in zip(unique_classes, counts):
        class_id = int(class_id)
        pixel_count = int(pixel_count)
        area_ha = pixel_count * pixel_area_ha
        
        stats.append({
            "class_id": class_id,
            "class_name": class_names.get(class_id, f"class_{class_id}"),
            "pixel_count": pixel_count,
            "area_ha": round(area_ha, 4),
        })
    
    # Sort by area descending
    stats.sort(key=lambda x: x["area_ha"], reverse=True)
    
    return stats


def run_s4a_on_bbox(
    bbox: Tuple[float, float, float, float],
    end_year: int,
    end_month: int,
    weights_s3_key: str,
    window_len: int = 6,
    size: Tuple[int, int] = (61, 61),
    norm_run_path: Optional[str] = None,
    device: str = "cpu",
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Run complete S4A inference pipeline on a bbox.
    
    Args:
        bbox: (min_lon, min_lat, max_lon, max_lat)
        end_year: End year for monthly stack
        end_month: End month for monthly stack
        weights_s3_key: S3 key for model weights
        window_len: Number of months (default 6)
        size: Output size (width, height)
        norm_run_path: Optional path to normalization stats
        device: Device for inference
        
    Returns:
        Tuple of (pred_map, stats_list)
        - pred_map: numpy array of shape (H, W) with class indices
        - stats_list: List of area statistics dicts
    """
    logger.info(
        f"Running S4A pipeline: bbox={bbox}, end={end_year}-{end_month:02d}, "
        f"window_len={window_len}, size={size}"
    )
    
    # Step 1: Download model weights
    local_weights = download_model_weights(weights_s3_key)
    
    # Step 2: Load model
    model = load_s4a_model(str(local_weights), device=device)
    
    # Step 3: Fetch monthly stack from Sentinel Hub
    input_stack = fetch_monthly_stack_sentinelhub(
        bbox=bbox,
        end_year=end_year,
        end_month=end_month,
        window_len=window_len,
        size=size,
    )
    
    # Step 4: Apply normalization
    norm_stats = load_norm_stats(norm_run_path)
    normalized_stack = apply_norm(input_stack, norm_stats)
    
    # Step 5: Run inference
    pred_map = infer_pixel_map(model, normalized_stack, device=device)
    
    # Step 6: Calculate area statistics
    stats = area_stats_from_map(pred_map, bbox)
    
    logger.info(f"S4A inference complete. Pred map shape: {pred_map.shape}")
    
    return pred_map, stats
