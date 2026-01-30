# convert.py
import torch
from safetensors.torch import save_file

# Disable weights_only cho trusted model
checkpoint = torch.load(
    "models/multi_temporal_crop_classification_Prithvi_100M.pth",
    map_location="cpu",
    weights_only=False
)

# Extract state_dict
if isinstance(checkpoint, dict):
    state_dict = checkpoint.get('model', checkpoint.get('state_dict', checkpoint))
else:
    state_dict = checkpoint

# Convert to safetensors
save_file(state_dict, "models/multi_temporal_crop_classification_Prithvi_100M.safetensors")
print(f"✓ Converted {len(state_dict)} tensors to safetensors")