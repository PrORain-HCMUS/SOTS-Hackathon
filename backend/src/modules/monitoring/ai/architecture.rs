use serde::Deserialize;

#[derive(Debug, Deserialize, Clone)]
#[allow(dead_code)]
pub struct ModelConfig {
    pub model_type: String,
    pub architecture: String,
    pub img_size: usize,
    pub patch_size: usize,
    pub in_chans: usize,
    pub num_frames: usize,
    pub tubelet_size: usize,
    pub embed_dim: usize,
    pub depth: usize,
    pub num_heads: usize,
    pub mlp_ratio: f64,
    pub qkv_bias: bool,
    pub drop_rate: f64,
    pub attn_drop_rate: f64,
    pub drop_path_rate: f64,
    pub norm_layer: String,
    pub layer_norm_eps: f64,
    pub norm_pix_loss: bool,
    pub num_patches: usize,
    pub use_cls_token: bool,
    pub num_classes: usize,
    pub classes: Vec<String>,
    pub output_embed_dim: usize,
    pub neck: NeckConfig,
    pub decode_head: DecodeHeadConfig,
    pub img_norm_cfg: NormConfig,
    pub pretrained: String,
    pub task: String,
}

#[derive(Debug, Deserialize, Clone)]
#[allow(dead_code)]
pub struct NeckConfig {
    #[serde(rename = "type")]
    pub neck_type: String,
    pub embed_dim: usize,
    pub drop_cls_token: bool,
    #[serde(rename = "Hp")]
    pub hp: usize,
    #[serde(rename = "Wp")]
    pub wp: usize,
}

#[derive(Debug, Deserialize, Clone)]
#[allow(dead_code)]
pub struct DecodeHeadConfig {
    #[serde(rename = "type")]
    pub head_type: String,
    pub in_channels: usize,
    pub channels: usize,
    pub num_convs: usize,
    pub dropout_ratio: f64,
}

#[derive(Debug, Deserialize, Clone)]
pub struct NormConfig {
    pub means: Vec<f64>,
    pub stds: Vec<f64>,
}

impl ModelConfig {
    pub fn from_file(path: &str) -> anyhow::Result<Self> {
        let content = std::fs::read_to_string(path)?;
        let config: ModelConfig = serde_json::from_str(&content)?;
        Ok(config)
    }
}