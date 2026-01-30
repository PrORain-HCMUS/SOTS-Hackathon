from huggingface_hub import hf_hub_download

# Thông tin từ link của bạn
repo_id = "ibm-nasa-geospatial/Prithvi-EO-1.0-100M-multi-temporal-crop-classification"
filename = "multi_temporal_crop_classification_Prithvi_100M.pth"

# Tải file về (mặc định sẽ lưu vào cache hoặc bạn chọn local_dir)
file_path = hf_hub_download(
    repo_id=repo_id, 
    filename=filename,
    local_dir=".", # Tải về ngay thư mục hiện tại
    local_dir_use_symlinks=False
)

print(f"Đã tải xong tại: {file_path}")