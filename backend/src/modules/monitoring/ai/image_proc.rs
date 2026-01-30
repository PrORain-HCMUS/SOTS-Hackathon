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

    let img_rgb = img.to_rgb8();
    let (width, height) = (config.img_size, config.img_size);
    
    let total_size = config.num_frames * config.in_chans * height * width;
    let mut pixel_data = Vec::with_capacity(total_size);

    for _ in 0..config.num_frames {
        for c in 0..config.in_chans {
            let channel_idx = c % 3;
            for y in 0..height {
                for x in 0..width {
                    let value = img_rgb.get_pixel(x as u32, y as u32)[channel_idx] as f32;
                    pixel_data.push(value);
                }
            }
        }
    }

    let tensor = Tensor::from_vec(
        pixel_data,
        (1, config.num_frames, config.in_chans, height, width),
        device,
    ).map_err(|e| AppError::AiEngine(format!("Failed to create tensor: {}", e)))?;

    normalize_tensor(&tensor, config)
}

fn normalize_tensor(tensor: &Tensor, config: &ModelConfig) -> AppResult<Tensor> {
    let means = &config.img_norm_cfg.means;
    let stds = &config.img_norm_cfg.stds;
    let num_channels = config.num_frames * config.in_chans;
    
    if means.len() != num_channels || stds.len() != num_channels {
        return Err(AppError::AiEngine(format!(
            "Normalization parameters mismatch: expected {}, got means={}, stds={}",
            num_channels, means.len(), stds.len()
        )));
    }

    let shape = tensor.dims();
    let (batch, frames, channels, height, width) = 
        (shape[0], shape[1], shape[2], shape[3], shape[4]);

    let tensor_data = tensor
        .flatten_all()
        .map_err(|e| AppError::AiEngine(format!("Flatten failed: {}", e)))?
        .to_vec1::<f32>()
        .map_err(|e| AppError::AiEngine(format!("Vec conversion failed: {}", e)))?;

    let mut normalized_data = Vec::with_capacity(tensor_data.len());

    for b in 0..batch {
        for f in 0..frames {
            for c in 0..channels {
                let idx = f * channels + c;
                let (mean, std) = (means[idx] as f32, stds[idx] as f32);

                for h in 0..height {
                    for w in 0..width {
                        let data_idx = (((b * frames + f) * channels + c) * height + h) * width + w;
                        normalized_data.push((tensor_data[data_idx] - mean) / std);
                    }
                }
            }
        }
    }

    Tensor::from_vec(normalized_data, shape, tensor.device())
        .map_err(|e| AppError::AiEngine(format!("Tensor creation failed: {}", e)))
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

    Ok(mask_data
        .iter()
        .enumerate()
        .filter_map(|(idx, &class)| {
            if class == water_class_idx as u32 {
                Some(((idx % width) as f64, (idx / width) as f64))
            } else {
                None
            }
        })
        .collect())
}