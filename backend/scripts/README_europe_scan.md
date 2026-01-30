# Europe Sentinel-2 Scanner for Crop Classification

Script để download dữ liệu Sentinel-2 phủ toàn bộ châu Âu (hoặc từng vùng) và chuẩn bị input cho model Prithvi crop classification.

## Yêu cầu

### Environment
```bash
conda activate sots
pip install python-dotenv rasterio numpy requests
```

### Credentials
Copy `.env.example` thành `.env` và điền credentials:
```bash
cp /root/Desktop/SOTS-Hackathon/backend/.env.example /root/Desktop/SOTS-Hackathon/backend/.env
```

File `.env` cần có:
```
SENTINELHUB_CLIENT_ID=81105a4d-5756-4f7c-b6da-87abeb288de5
SENTINELHUB_CLIENT_SECRET=M7ea7lyT4nHaRTQvG6N4bvlzwb573Bmz
SENTINELHUB_BASE_URL=https://services.sentinel-hub.com
```

## Cách sử dụng

### 1. Estimate số tiles
```bash
python scan_europe_sentinel2.py --region france --estimate
```

### 2. Scan một vùng
```bash
# France sample (vùng Paris, ~187 tiles - để test)
python scan_europe_sentinel2.py --region france_sample --output /root/Desktop/SOTS-Hackathon/backend/data

# France đầy đủ (~30,000 tiles)
python scan_europe_sentinel2.py --region france --output /root/Desktop/SOTS-Hackathon/backend/data

# Các vùng khác
python scan_europe_sentinel2.py --region germany --output /root/Desktop/SOTS-Hackathon/backend/data
python scan_europe_sentinel2.py --region spain --output /root/Desktop/SOTS-Hackathon/backend/data
```

### 3. Tùy chọn
```bash
# Chỉ định thời gian
python scan_europe_sentinel2.py --region france_sample \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --output /root/Desktop/SOTS-Hackathon/backend/data

# Thay đổi max cloud cover
python scan_europe_sentinel2.py --region france_sample --max-cloud 20

# Bắt đầu lại từ đầu (không resume)
python scan_europe_sentinel2.py --region france_sample --no-resume
```

## Các vùng có sẵn

| Region | Bounds | Est. Tiles |
|--------|--------|------------|
| `europe` | Full Europe | ~150,000+ |
| `western_europe` | W. Europe | ~40,000 |
| `central_europe` | C. Europe | ~15,000 |
| `france` | France | ~30,000 |
| `germany` | Germany | ~8,000 |
| `spain` | Spain | ~12,000 |
| `italy` | Italy | ~10,000 |
| `uk` | United Kingdom | ~12,000 |
| `poland` | Poland | ~6,000 |
| `ukraine` | Ukraine | ~15,000 |
| `netherlands` | Netherlands | ~3,000 |
| `france_sample` | Paris area | ~187 |
| `test` | Small test | ~170 |

## Cấu trúc Output

```
/root/Desktop/SOTS-Hackathon/backend/data/
└── {region}/
    ├── tiles/
    │   ├── tile_r0000_c0000.tif   # Shape: (18, 224, 224)
    │   ├── tile_r0000_c0001.tif   # 6 bands × 3 temporal frames
    │   └── ...
    ├── tile_index.json            # Mapping tile_id → coordinates
    ├── metadata.json              # Scan configuration
    └── scan_progress.json         # Resume state
```

### tile_index.json format
```json
{
  "r0000_c0000": {
    "tile_id": "r0000_c0000",
    "center_lon": 2.05,
    "center_lat": 48.53,
    "dates": ["2024-03-15", "2024-07-20", "2024-11-10"],
    "shape": [18, 224, 224]
  },
  ...
}
```

## Input format cho Model

Mỗi tile có:
- **Shape**: `(18, 224, 224)` = 6 bands × 3 temporal frames
- **Bands per frame**: Blue (B02), Green (B03), Red (B04), NIR (B8A), SWIR1 (B11), SWIR2 (B12)
- **Dtype**: int16
- **Resolution**: 30m
- **Tile size**: 224×224 pixels = 6.72km × 6.72km

## Chạy Inference

Sau khi download xong, chạy inference trên từng tile:

```bash
cd /root/Desktop/SOTS-Hackathon/backend/ml/hls-foundation-os

python model_inference.py \
    -config configs/multi_temporal_crop_classification.py \
    -ckpt /root/Desktop/SOTS-Hackathon/backend/ml/weights/multi_temporal_crop_classification_Prithvi_100M.pth \
    -input /root/Desktop/SOTS-Hackathon/backend/data/france_sample/tiles \
    -output /root/Desktop/SOTS-Hackathon/backend/data/france_sample/predictions \
    -input_type tif \
    -bands 0 1 2 3 4 5 \
    -device cpu
```

## Reconstruct Map

Sử dụng `tile_index.json` để ghép các tiles lại thành bản đồ hoàn chỉnh:

```python
import json
import rasterio
import numpy as np

# Load tile index
with open('data/france_sample/tile_index.json') as f:
    tile_index = json.load(f)

# Get bounds
lons = [t['center_lon'] for t in tile_index.values()]
lats = [t['center_lat'] for t in tile_index.values()]
print(f"Coverage: {min(lons):.2f}°E to {max(lons):.2f}°E, {min(lats):.2f}°N to {max(lats):.2f}°N")
```

## Tốc độ và Thời gian

- **Rate**: ~0.1-0.2 tiles/s (do API rate limiting)
- **France sample (187 tiles)**: ~15-30 phút
- **France full (30,000 tiles)**: ~40-80 giờ
- **Europe full (150,000+ tiles)**: ~200+ giờ

**Tip**: Chạy nhiều regions song song trên các terminals khác nhau.

## Resume

Script tự động lưu progress. Nếu bị gián đoạn, chỉ cần chạy lại command và nó sẽ tiếp tục từ chỗ dừng.

```bash
# Kiểm tra progress
cat /root/Desktop/SOTS-Hackathon/backend/data/france_sample/scan_progress.json
```
