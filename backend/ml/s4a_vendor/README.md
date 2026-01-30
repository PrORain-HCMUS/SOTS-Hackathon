# S4A Vendor Model Code

This directory should contain the S4A ConvLSTM model implementation.

## Required Files

Copy the following files from the S4A repository:

```
s4a_vendor/
├── __init__.py
├── models.py          # Contains ConvLSTM class
├── layers.py          # Custom layers (if any)
└── utils.py           # Utility functions (if any)
```

## Model Requirements

The `models.py` file must export a `ConvLSTM` class that:

1. **Inherits from `pytorch_lightning.LightningModule`**
2. **Has a `load_from_checkpoint` class method**
3. **Accepts input tensor of shape `(batch, time, channels, height, width)`**
   - batch: 1 (for inference)
   - time: 6 (monthly composites)
   - channels: 4 (B02, B03, B04, B08)
   - height: 61
   - width: 61
4. **Returns logits of shape `(batch, num_classes, height, width)`**

## Example Model Interface

```python
import torch
import pytorch_lightning as pl

class ConvLSTM(pl.LightningModule):
    def __init__(self, input_dim=4, hidden_dim=64, num_classes=13, **kwargs):
        super().__init__()
        # ... model architecture ...
    
    def forward(self, x):
        # x: (batch, time, channels, height, width)
        # returns: (batch, num_classes, height, width)
        pass
    
    @classmethod
    def load_from_checkpoint(cls, checkpoint_path, map_location=None, **kwargs):
        # Load model from checkpoint
        pass
```

## Normalization Statistics

If your model requires input normalization, create a `norm_stats.npz` file with:

```python
import numpy as np

# Mean and std for each band (B02, B03, B04, B08)
mean = np.array([0.1, 0.1, 0.1, 0.2])  # Example values
std = np.array([0.05, 0.05, 0.05, 0.1])  # Example values

np.savez('norm_stats.npz', mean=mean, std=std)
```

## Model Weights

Upload model checkpoint to DigitalOcean Spaces:

```bash
# Using AWS CLI with Spaces endpoint
aws s3 cp convlstm_v1.ckpt s3://YOUR_BUCKET/models/s4a/convlstm_v1.ckpt \
    --endpoint-url https://sgp1.digitaloceanspaces.com
```

Then register the model:

```bash
python scripts/register_model_s4a.py
```

## Testing

After copying the model code, test the import:

```python
from ml.s4a_vendor.models import ConvLSTM

# Should not raise ImportError
print("S4A model imported successfully!")
```

## Notes

- The backend will gracefully handle missing vendor code with clear error messages
- Model inference runs on CPU by default (configurable)
- Predictions are saved as Cloud-Optimized GeoTIFFs (COGs)
