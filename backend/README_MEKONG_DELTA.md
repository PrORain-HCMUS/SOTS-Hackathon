# Hướng dẫn Crop Classification cho Đồng bằng Sông Cửu Long

Tài liệu hướng dẫn đầy đủ về cách tải model weights, trích xuất dữ liệu Sentinel-2, và chạy inference cho vùng Đồng bằng Sông Cửu Long (Mekong Delta).

## Tổng quan

| Thành phần | Mô tả |
|------------|-------|
| **Model** | Prithvi 100M - Multi-temporal Crop Classification |
| **Input** | Sentinel-2 L2A (6 bands × 3 temporal frames) |
| **Output** | Crop classification map (13 classes) |
| **Vùng** | Đồng bằng Sông Cửu Long (104.5°E - 107°E, 8.5°N - 11.5°N) |
| **Tiles** | ~2,046 tiles (224×224 pixels, 30m resolution) |

---

## 1. Cài đặt môi trường

### 1.1 Activate conda environment
```bash
conda activate sots
```

### 1.2 Cài đặt dependencies
```bash
cd /root/Desktop/SOTS-Hackathon/backend
pip install python-dotenv rasterio numpy requests pyproj
```

### 1.3 Cấu hình credentials
```bash
# Copy file .env.example thành .env
cp .env.example .env
```

File `.env` cần có các biến sau:
```env
# Sentinel Hub API
SENTINELHUB_CLIENT_ID=81105a4d-5756-4f7c-b6da-87abeb288de5
SENTINELHUB_CLIENT_SECRET=M7ea7lyT4nHaRTQvG6N4bvlzwb573Bmz
SENTINELHUB_BASE_URL=https://services.sentinel-hub.com
```

---

## 2. Model Weights

### 2.1 Vị trí model weights
```
/root/Desktop/SOTS-Hackathon/backend/ml/weights/multi_temporal_crop_classification_Prithvi_100M.pth
```

### 2.2 Model configuration
```
/root/Desktop/SOTS-Hackathon/backend/ml/hls-foundation-os/configs/multi_temporal_crop_classification.py
```

### 2.3 Thông số model
| Parameter | Value |
|-----------|-------|
| `num_frames` | 3 (temporal frames) |
| `img_size` | 224 pixels |
| `num_bands` | 6 (Blue, Green, Red, NIR, SWIR1, SWIR2) |
| `num_classes` | 13 |
| `patch_size` | 16 |
| `embed_dim` | 768 |

### 2.4 Classes (13 loại)
```
0: Natural Vegetation
1: Forest
2: Corn
3: Soybeans
4: Wetlands
5: Developed/Barren
6: Open Water
7: Winter Wheat
8: Alfalfa
9: Fallow/Idle Cropland
10: Cotton
11: Sorghum
12: Other
```

---

## 3. Trích xuất dữ liệu Sentinel-2 cho Đồng bằng SCL

### 3.1 Estimate số tiles
```bash
cd /root/Desktop/SOTS-Hackathon/backend/scripts

python scan_europe_sentinel2.py --region mekong_delta --estimate
```

Output:
```
Region: mekong_delta
Bounds: W=104.5, E=107.0, S=8.5, N=11.5
Estimated grid: 50 rows × 41 cols = 2050 tiles
```

### 3.2 Chạy trích xuất dữ liệu
```bash
python scan_europe_sentinel2.py \
    --region mekong_delta \
    --output /root/Desktop/SOTS-Hackathon/backend/data
```

### 3.3 Tùy chọn nâng cao
```bash
# Chỉ định khoảng thời gian
python scan_europe_sentinel2.py \
    --region mekong_delta \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --output /root/Desktop/SOTS-Hackathon/backend/data

# Giảm cloud cover threshold
python scan_europe_sentinel2.py \
    --region mekong_delta \
    --max-cloud 20 \
    --output /root/Desktop/SOTS-Hackathon/backend/data

# Bắt đầu lại từ đầu (không resume)
python scan_europe_sentinel2.py \
    --region mekong_delta \
    --no-resume \
    --output /root/Desktop/SOTS-Hackathon/backend/data
```

### 3.4 Cấu trúc dữ liệu output
```
/root/Desktop/SOTS-Hackathon/backend/data/mekong_delta/
├── tiles/
│   ├── tile_r0000_c0000.tif    # Shape: (18, 224, 224)
│   ├── tile_r0000_c0001.tif    # 6 bands × 3 temporal frames
│   ├── tile_r0000_c0002.tif
│   └── ... (~2046 files)
├── tile_index.json              # Mapping tile_id → coordinates
├── metadata.json                # Scan configuration
└── scan_progress.json           # Resume state
```

### 3.5 Format của tile_index.json
```json
{
  "r0000_c0000": {
    "tile_id": "r0000_c0000",
    "center_lon": 104.53,
    "center_lat": 8.53,
    "dates": ["2024-03-15T...", "2024-07-20T...", "2024-11-10T..."],
    "shape": [18, 224, 224]
  },
  "r0000_c0001": {
    "tile_id": "r0000_c0001",
    "center_lon": 104.59,
    "center_lat": 8.53,
    "dates": ["2024-03-15T...", "2024-07-20T...", "2024-11-10T..."],
    "shape": [18, 224, 224]
  }
}
```

### 3.6 Thời gian ước tính
| Số tiles | Thời gian |
|----------|-----------|
| 100 tiles | ~10-15 phút |
| 500 tiles | ~50-75 phút |
| 2046 tiles (full) | ~3-5 giờ |

**Lưu ý**: Script tự động lưu progress. Nếu bị gián đoạn, chạy lại command và nó sẽ tiếp tục từ chỗ dừng.

---

## 4. Chạy Inference

### 4.1 Inference trên toàn bộ tiles
```bash
cd /root/Desktop/SOTS-Hackathon/backend/ml/hls-foundation-os

python model_inference.py \
    -config configs/multi_temporal_crop_classification.py \
    -ckpt /root/Desktop/SOTS-Hackathon/backend/ml/weights/multi_temporal_crop_classification_Prithvi_100M.pth \
    -input /root/Desktop/SOTS-Hackathon/backend/data/mekong_delta/tiles \
    -output /root/Desktop/SOTS-Hackathon/backend/data/mekong_delta/predictions \
    -input_type tif \
    -bands 0 1 2 3 4 5 \
    -device cpu
```

### 4.2 Inference với GPU (nếu có)
```bash
python model_inference.py \
    -config configs/multi_temporal_crop_classification.py \
    -ckpt /root/Desktop/SOTS-Hackathon/backend/ml/weights/multi_temporal_crop_classification_Prithvi_100M.pth \
    -input /root/Desktop/SOTS-Hackathon/backend/data/mekong_delta/tiles \
    -output /root/Desktop/SOTS-Hackathon/backend/data/mekong_delta/predictions \
    -input_type tif \
    -bands 0 1 2 3 4 5 \
    -device cuda
```

### 4.3 Output của inference
```
/root/Desktop/SOTS-Hackathon/backend/data/mekong_delta/predictions/
├── tile_r0000_c0000_pred.tif    # Shape: (224, 224), dtype: int16
├── tile_r0000_c0001_pred.tif
└── ...
```

Mỗi pixel trong prediction có giá trị 0-12 tương ứng với 13 classes.

---

## 5. Visualize kết quả

### 5.1 Sử dụng script visualize
```bash
cd /root/Desktop/SOTS-Hackathon/backend/ml/hls-foundation-os

python visualize_prediction.py \
    -pred /root/Desktop/SOTS-Hackathon/backend/data/mekong_delta/predictions/tile_r0000_c0000_pred.tif \
    -input /root/Desktop/SOTS-Hackathon/backend/data/mekong_delta/tiles/tile_r0000_c0000.tif \
    -output_dir /root/Desktop/SOTS-Hackathon/backend/data/mekong_delta/visualizations
```

### 5.2 Python code để visualize
```python
import numpy as np
import rasterio
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# Color map cho 13 classes
CLASS_COLORS = {
    0: [34, 139, 34],    # Natural Vegetation
    1: [0, 100, 0],      # Forest
    2: [255, 215, 0],    # Corn
    3: [144, 238, 144],  # Soybeans
    4: [0, 206, 209],    # Wetlands
    5: [128, 128, 128],  # Developed/Barren
    6: [0, 0, 255],      # Open Water
    7: [210, 180, 140],  # Winter Wheat
    8: [186, 85, 211],   # Alfalfa
    9: [245, 222, 179],  # Fallow/Idle Cropland
    10: [255, 255, 255], # Cotton
    11: [255, 140, 0],   # Sorghum
    12: [169, 169, 169], # Other
}

CLASS_NAMES = [
    "Natural Vegetation", "Forest", "Corn", "Soybeans", "Wetlands",
    "Developed/Barren", "Open Water", "Winter Wheat", "Alfalfa",
    "Fallow/Idle Cropland", "Cotton", "Sorghum", "Other"
]

# Load prediction
with rasterio.open('predictions/tile_r0000_c0000_pred.tif') as src:
    pred = src.read(1)

# Convert to RGB
h, w = pred.shape
rgb = np.zeros((h, w, 3), dtype=np.uint8)
for class_id, color in CLASS_COLORS.items():
    rgb[pred == class_id] = color

# Plot
plt.figure(figsize=(10, 10))
plt.imshow(rgb)
plt.axis('off')
plt.title('Crop Classification - Mekong Delta')
plt.savefig('visualization.png', dpi=150, bbox_inches='tight')
plt.show()
```

---

## 6. Ghép tiles thành bản đồ hoàn chỉnh

### 6.1 Python code để reconstruct map
```python
import json
import numpy as np
import rasterio
from rasterio.merge import merge
from pathlib import Path

# Load tile index
data_dir = Path('/root/Desktop/SOTS-Hackathon/backend/data/mekong_delta')
with open(data_dir / 'tile_index.json') as f:
    tile_index = json.load(f)

# Get all prediction files
pred_dir = data_dir / 'predictions'
pred_files = list(pred_dir.glob('*_pred.tif'))

print(f"Found {len(pred_files)} prediction tiles")

# Get coverage bounds
lons = [t['center_lon'] for t in tile_index.values()]
lats = [t['center_lat'] for t in tile_index.values()]
print(f"Coverage: {min(lons):.2f}°E to {max(lons):.2f}°E")
print(f"          {min(lats):.2f}°N to {max(lats):.2f}°N")

# Merge all tiles (requires enough memory)
src_files = [rasterio.open(f) for f in pred_files]
mosaic, out_transform = merge(src_files)

# Save merged map
out_meta = src_files[0].meta.copy()
out_meta.update({
    "height": mosaic.shape[1],
    "width": mosaic.shape[2],
    "transform": out_transform
})

with rasterio.open(data_dir / 'mekong_delta_full_map.tif', 'w', **out_meta) as dst:
    dst.write(mosaic)

# Close files
for src in src_files:
    src.close()

print(f"Saved full map: {data_dir / 'mekong_delta_full_map.tif'}")
```

---

## 7. Quick Start - Chạy đầy đủ pipeline

```bash
# 1. Activate environment
conda activate sots
cd /root/Desktop/SOTS-Hackathon/backend

# 2. Ensure .env exists
cp .env.example .env

# 3. Download Sentinel-2 data cho Mekong Delta
cd scripts
python scan_europe_sentinel2.py --region mekong_delta --output ../data

# 4. Chạy inference
cd ../ml/hls-foundation-os
python model_inference.py \
    -config configs/multi_temporal_crop_classification.py \
    -ckpt ../weights/multi_temporal_crop_classification_Prithvi_100M.pth \
    -input ../../data/mekong_delta/tiles \
    -output ../../data/mekong_delta/predictions \
    -input_type tif \
    -bands 0 1 2 3 4 5 \
    -device cpu

# 5. Visualize một tile
python visualize_prediction.py \
    -pred ../../data/mekong_delta/predictions/tile_r0000_c0000_pred.tif \
    -output_dir ../../data/mekong_delta/visualizations
```

---

## 8. Troubleshooting

### 8.1 Lỗi "No module named 'rasterio'"
```bash
pip install rasterio
```

### 8.2 Lỗi "SENTINELHUB credentials not set"
```bash
cp .env.example .env
# Kiểm tra file .env có đúng credentials
```

### 8.3 Lỗi "libGL.so.1 not found"
```bash
pip uninstall opencv-python
pip install opencv-python-headless
```

### 8.4 Lỗi "CUDA not available"
Thêm `-device cpu` vào command inference.

### 8.5 Lỗi "numpy version conflict"
```bash
pip install "numpy<2"
```

### 8.6 Resume scan bị gián đoạn
Script tự động resume. Chỉ cần chạy lại command:
```bash
python scan_europe_sentinel2.py --region mekong_delta --output ../data
```

---

## 9. File Structure

```
/root/Desktop/SOTS-Hackathon/backend/
├── .env                          # Credentials (copy từ .env.example)
├── .env.example                  # Template credentials
├── README_MEKONG_DELTA.md        # File này
├── data/
│   └── mekong_delta/
│       ├── tiles/                # Input tiles (18, 224, 224)
│       ├── predictions/          # Output predictions (224, 224)
│       ├── visualizations/       # PNG visualizations
│       ├── tile_index.json       # Tile coordinates mapping
│       ├── metadata.json         # Scan metadata
│       └── scan_progress.json    # Resume state
├── ml/
│   ├── weights/
│   │   └── multi_temporal_crop_classification_Prithvi_100M.pth
│   └── hls-foundation-os/
│       ├── model_inference.py
│       ├── visualize_prediction.py
│       └── configs/
│           └── multi_temporal_crop_classification.py
└── scripts/
    ├── scan_europe_sentinel2.py  # Data extraction script
    └── download_hls_for_inference.py  # Single location download
```

---

## 10. Liên hệ

Nếu có vấn đề, kiểm tra:
1. Credentials trong `.env`
2. Conda environment đã activate
3. Đủ disk space cho data (~5GB cho Mekong Delta)
4. Network connection để download từ Sentinel Hub
