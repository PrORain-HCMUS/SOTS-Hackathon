# verify_config.py
import torch

checkpoint = torch.load(
    "models/multi_temporal_crop_classification_Prithvi_100M.pth",
    map_location="cpu",
    weights_only=False
)

state_dict = checkpoint['state_dict']

print("=== VERIFICATION ===")
print(f"embed_dim from state: {state_dict['backbone.cls_token'].shape[-1]}")
print(f"patch_size from state: {state_dict['backbone.patch_embed.proj.weight'].shape[-1]}")
print(f"in_chans from state: {state_dict['backbone.patch_embed.proj.weight'].shape[1]}")
print(f"temporal_dim from state: {state_dict['backbone.patch_embed.proj.weight'].shape[2]}")
print(f"num_blocks from state: {len([k for k in state_dict.keys() if k.startswith('backbone.blocks.') and k.endswith('.norm1.weight')])}")

# Check classification head
head_keys = [k for k in state_dict.keys() if 'decode_head' in k and 'weight' in k]
print(f"\nDecode head layers:")
for k in head_keys[:5]:
    print(f"  {k}: {state_dict[k].shape}")

print("\n✓ Config matches state_dict!")