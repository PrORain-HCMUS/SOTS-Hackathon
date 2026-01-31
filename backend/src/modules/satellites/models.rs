use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct CropClass {
    pub id: i32,
    pub name: String,
    pub color: String,
    pub description: Option<String>,
    #[serde(skip_serializing)]
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, sqlx::FromRow)]
pub struct SatelliteTile {
    pub id: i32,
    pub tile_id: i32,
    pub tile_name: String,
    pub prediction_file: String,
    pub visualization_file: String,
    pub bounds: serde_json::Value,
    pub center_lat: f64,
    pub center_lon: f64,
    pub bbox: serde_json::Value,
    pub captured_at: Option<DateTime<Utc>>,
    pub processed_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TileCropStat {
    pub id: i32,
    pub tile_id: i32,
    pub crop_class_id: i32,
    pub crop_name: String,
    pub crop_color: String,
    pub pixel_count: i32,
    pub area_hectares: Option<f64>,
    pub percentage: Option<f64>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CoverageArea {
    pub total_tiles: i64,
    pub total_area_hectares: f64,
    pub bounds: Bounds,
    pub crop_distribution: Vec<CropDistribution>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Bounds {
    pub west: f64,
    pub south: f64,
    pub east: f64,
    pub north: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct CropDistribution {
    pub crop_id: i32,
    pub crop_name: String,
    pub crop_color: String,
    pub total_area_hectares: f64,
    pub percentage: f64,
}
