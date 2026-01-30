use candle_core::{Device, Tensor};
use crate::shared::error::{AppError, AppResult};
use super::architecture::ModelConfig;

pub fn preprocess_image(
    image_bytes: &[u8],
    config: &ModelConfig,
    device: &Device,
) -> AppResult<Tensor> {
    let img = image::load_from_memory(image_bytes)
        .map_err(|e| AppError::AiEngine(format!("Failed to load image: {}", e)))?
        .resize_exact(
            config.img_size as u32,
            config.img_size as u32,
            image::imageops::FilterType::Lanczos3,
        );

    let width = img.width() as usize;
    let height = img.height() as usize;
    let raw_pixels = img.into_rgb8().into_raw();
    
    // Convert to f32 and create tensor (H, W, 3)
    let data_f32: Vec<f32> = raw_pixels.into_iter().map(|v| v as f32).collect();
    let tensor = Tensor::from_vec(
        data_f32,
        (height, width, 3),
        device,
    ).map_err(|e| AppError::AiEngine(format!("Failed to create tensor: {}", e)))?;

    // Permute to (3, H, W)
    let tensor = tensor
        .permute((2, 0, 1))
        .map_err(|e| AppError::AiEngine(format!("Permute failed: {}", e)))?;

    // Reshape to (1, 1, 3, H, W) and repeat to (1, Frames, 3, H, W)
    let tensor = tensor
        .unsqueeze(0)
        .map_err(|e| AppError::AiEngine(format!("Unsqueeze failed: {}", e)))?
        .unsqueeze(0)
        .map_err(|e| AppError::AiEngine(format!("Unsqueeze failed: {}", e)))?
        .repeat((1, config.num_frames, 1, 1, 1))
        .map_err(|e| AppError::AiEngine(format!("Repeat failed: {}", e)))?;

    normalize_tensor(&tensor, config)
}

fn normalize_tensor(tensor: &Tensor, config: &ModelConfig) -> AppResult<Tensor> {
    let means_val: Vec<f32> = config.img_norm_cfg.means.iter().map(|&x| x as f32).collect();
    let stds_val: Vec<f32> = config.img_norm_cfg.stds.iter().map(|&x| x as f32).collect();
    
    let num_channels = config.num_frames * config.in_chans;
    
    if means_val.len() != num_channels || stds_val.len() != num_channels {
        return Err(AppError::AiEngine(format!(
            "Normalization parameters mismatch: expected {}, got means={}, stds={}",
            num_channels, means_val.len(), stds_val.len()
        )));
    }

    // Reshape means/stds for broadcasting: (1, Frames, Channels, 1, 1)
    // NOTE: config.in_chans should be 3 for RGB. 
    // The previous code assumed flattening: idx = f * channels + c
    // So distinct params per frame/channel.
    
    let stats_shape = (1, config.num_frames, config.in_chans, 1, 1);
    
    let means = Tensor::from_vec(means_val, stats_shape, tensor.device())
        .map_err(|e| AppError::AiEngine(format!("Means tensor failed: {}", e)))?;
        
    let stds = Tensor::from_vec(stds_val, stats_shape, tensor.device())
        .map_err(|e| AppError::AiEngine(format!("Stds tensor failed: {}", e)))?;

    tensor
        .broadcast_sub(&means)
        .and_then(|t| t.broadcast_div(&stds))
        .map_err(|e| AppError::AiEngine(format!("Normalization failed: {}", e)))
}

pub fn postprocess_segmentation(
    output: &Tensor,
    water_class_idx: usize,
) -> AppResult<Vec<(f64, f64)>> {
    let (batch, _num_classes, _height, width) = output
        .dims4()
        .map_err(|e| AppError::AiEngine(format!("Invalid output shape: {}", e)))?;

    if batch != 1 {
        return Err(AppError::AiEngine(format!("Expected batch size 1, got {}", batch)));
    }

    let mask_data = output
        .argmax(1)
        .and_then(|t| t.flatten_all())
        .and_then(|t| t.to_vec1::<u32>())
        .map_err(|e| AppError::AiEngine(format!("Postprocess failed: {}", e)))?;

    let water_class = water_class_idx as u32;
    // let width_f64 = width as f64; // Removed unused variable
    
    Ok(mask_data
        .iter()
        .enumerate()
        .filter_map(|(idx, &class)| {
            (class == water_class).then(|| {
                let x = (idx % width) as f64;
                let y = (idx / width) as f64;
                (x, y)
            })
        })
        .collect())
}