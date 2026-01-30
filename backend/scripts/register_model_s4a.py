#!/usr/bin/env python
"""
Register S4A ConvLSTM model in the database.

This script registers the S4A model metadata. The actual model weights
should be uploaded to DigitalOcean Spaces before running this script.

Usage:
    python scripts/register_model_s4a.py

Environment variables required:
    - DO_SPACES_BUCKET
    - Model weights should be at: models/s4a/convlstm_v1.ckpt
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.db import get_db_context
from app.core.crud import get_model_by_name_version, create_model
from app.core.config import get_settings

# S4A Model configuration
S4A_MODEL_CONFIG = {
    "name": "S4A-ConvLSTM",
    "task": "crop_classification",
    "version": "1.0.0",
    "weights_s3_key": "models/s4a/convlstm_v1.ckpt",
    "input_spec": {
        "shape": [1, 6, 4, 61, 61],  # (batch, time, channels, height, width)
        "bands": ["B02", "B03", "B04", "B08"],
        "window_len": 6,
        "group_freq": "1MS",  # Monthly
        "resolution_m": 10,
    },
    "output_spec": {
        "shape": [61, 61],  # (height, width)
        "num_classes": 13,
        "class_mapping": {
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
        },
    },
}


def main():
    """Register S4A model."""
    print("Registering S4A ConvLSTM model...")
    print("=" * 50)
    
    settings = get_settings()
    
    with get_db_context() as db:
        # Check if model already exists
        existing = get_model_by_name_version(
            db,
            name=S4A_MODEL_CONFIG["name"],
            version=S4A_MODEL_CONFIG["version"],
        )
        
        if existing:
            print(f"Model already registered: {existing.name} v{existing.version}")
            print(f"  model_id: {existing.model_id}")
            print(f"  weights_s3_key: {existing.weights_s3_key}")
            return
        
        # Create model record
        model = create_model(
            db=db,
            name=S4A_MODEL_CONFIG["name"],
            task=S4A_MODEL_CONFIG["task"],
            version=S4A_MODEL_CONFIG["version"],
            weights_s3_key=S4A_MODEL_CONFIG["weights_s3_key"],
            input_spec=S4A_MODEL_CONFIG["input_spec"],
            output_spec=S4A_MODEL_CONFIG["output_spec"],
        )
        
        print(f"Model registered successfully!")
        print(f"  model_id: {model.model_id}")
        print(f"  name: {model.name}")
        print(f"  version: {model.version}")
        print(f"  task: {model.task}")
        print(f"  weights_s3_key: {model.weights_s3_key}")
    
    print("\n" + "=" * 50)
    print("IMPORTANT: Make sure to upload model weights to Spaces:")
    print(f"  Bucket: {settings.do_spaces_bucket}")
    print(f"  Key: {S4A_MODEL_CONFIG['weights_s3_key']}")
    print("\nExample upload command:")
    print(f"  aws s3 cp convlstm_v1.ckpt s3://{settings.do_spaces_bucket}/{S4A_MODEL_CONFIG['weights_s3_key']} --endpoint-url {settings.do_spaces_endpoint}")


if __name__ == "__main__":
    main()
