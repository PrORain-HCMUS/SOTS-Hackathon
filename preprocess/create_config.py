# create_config.py
import json

# Extract từ training config
config = {
    "model_type": "prithvi_vit_temporal",
    "architecture": "TemporalViTEncoder",
    
    # Image specifications (from training config)
    "img_size": 224,
    "patch_size": 16,
    "in_chans": 6,  # len(bands)
    "num_frames": 3,
    "tubelet_size": 1,
    
    # ViT architecture - Prithvi temporal model
    "embed_dim": 768,
    "depth": 6,  # num_layers in config
    "num_heads": 8,  # NOT 12!
    "mlp_ratio": 4.0,
    "qkv_bias": True,
    
    # Dropout
    "drop_rate": 0.0,
    "attn_drop_rate": 0.0,
    "drop_path_rate": 0.0,
    
    # Normalization
    "norm_layer": "LayerNorm",
    "layer_norm_eps": 1e-6,
    "norm_pix_loss": False,
    
    # Position embedding
    "num_patches": 196,  # (224/16)^2 = 14*14
    "use_cls_token": True,
    
    # Classification head
    "num_classes": 13,  # len(CLASSES)
    "classes": [
        "Natural Vegetation",
        "Forest", 
        "Corn",
        "Soybeans",
        "Wetlands",
        "Developed/Barren",
        "Open Water",
        "Winter Wheat",
        "Alfalfa",
        "Fallow/Idle Cropland",
        "Cotton",
        "Sorghum",
        "Other"
    ],
    
    # Neck config
    "output_embed_dim": 2304,  # embed_dim * num_frames = 768 * 3
    "neck": {
        "type": "ConvTransformerTokensToEmbeddingNeck",
        "embed_dim": 2304,
        "drop_cls_token": True,
        "Hp": 14,
        "Wp": 14
    },
    
    # Decode head config
    "decode_head": {
        "type": "FCNHead",
        "in_channels": 2304,
        "channels": 256,
        "num_convs": 1,
        "dropout_ratio": 0.1
    },
    
    # Data normalization (for inference)
    "img_norm_cfg": {
        "means": [
            494.905781, 815.239594, 924.335066, 2968.881459, 2634.621962, 1739.579917,
            494.905781, 815.239594, 924.335066, 2968.881459, 2634.621962, 1739.579917,
            494.905781, 815.239594, 924.335066, 2968.881459, 2634.621962, 1739.579917
        ],
        "stds": [
            284.925432, 357.84876, 575.566823, 896.601013, 951.900334, 921.407808,
            284.925432, 357.84876, 575.566823, 896.601013, 951.900334, 921.407808,
            284.925432, 357.84876, 575.566823, 896.601013, 951.900334, 921.407808
        ]
    },
    
    # Metadata
    "pretrained": "prithvi_100M",
    "task": "multi_temporal_crop_classification"
}

with open("models/config.json", "w") as f:
    json.dump(config, indent=2, fp=f)

print("✓ Created config.json from training configuration")
print(json.dumps(config, indent=2))