# check_checkpoint.py
import torch
import json

checkpoint = torch.load(
    "models/multi_temporal_crop_classification_Prithvi_100M.pth",
    map_location="cpu",
    weights_only=False
)

print("Checkpoint keys:", checkpoint.keys() if isinstance(checkpoint, dict) else "Not a dict")
print()

if isinstance(checkpoint, dict):
    # Check for config
    if 'config' in checkpoint:
        print("Found config:")
        print(json.dumps(checkpoint['config'], indent=2))
    elif 'model_config' in checkpoint:
        print("Found model_config:")
        print(json.dumps(checkpoint['model_config'], indent=2))
    elif 'hparams' in checkpoint:
        print("Found hparams:")
        print(json.dumps(checkpoint['hparams'], indent=2))
    else:
        print("No config found. Inspecting state_dict structure:")
        state_dict = checkpoint.get('model', checkpoint.get('state_dict', checkpoint))
        
        # Print first 20 layers
        print(f"\nTotal layers: {len(state_dict)}")
        print("\nFirst 20 layers:")
        for key in list(state_dict.keys())[:20]:
            print(f"  {key}: {state_dict[key].shape}")
else:
    print("Checkpoint is direct state_dict")
    print(f"Total layers: {len(checkpoint)}")
    print("\nFirst 20 layers:")
    for key in list(checkpoint.keys())[:20]:
        print(f"  {key}: {checkpoint[key].shape}")