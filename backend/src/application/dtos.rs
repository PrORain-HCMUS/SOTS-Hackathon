use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::domain::{AlertSeverity, AlertType, GeoPolygon, IntrusionVector};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessImageRequest {
    pub image_id: Uuid,
    pub farm_ids: Option<Vec<Uuid>>,
    pub force_reprocess: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProcessImageResult {
    pub image_id: Uuid,
    pub processed_farms: Vec<FarmProcessingResult>,
    pub alerts_generated: Vec<AlertDto>,
    pub processing_time_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FarmProcessingResult {
    pub farm_id: Uuid,
    pub ndvi: f32,
    pub ndsi: f32,
    pub srvi: f32,
    pub red_edge_index: f32,
    pub anomaly_detected: bool,
    pub trend: TrendDto,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TrendDto {
    pub direction: String,
    pub change_percentage: f32,
    pub confidence: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AlertDto {
    pub id: Uuid,
    pub farm_id: Uuid,
    pub alert_type: AlertType,
    pub severity: AlertSeverity,
    pub title: String,
    pub description: String,
    pub detected_at: DateTime<Utc>,
    pub intrusion_vector: Option<IntrusionVector>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SalinityStatusDto {
    pub farm_id: Uuid,
    pub current_ndsi: f32,
    pub baseline_ndsi: f32,
    pub deviation_percentage: f32,
    pub trend: SalinityTrendDto,
    pub risk_level: RiskLevelDto,
    pub last_updated: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SalinityTrendDto {
    Increasing,
    Decreasing,
    Stable,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum RiskLevelDto {
    Low,
    Medium,
    High,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntrusionPredictionDto {
    pub farm_id: Uuid,
    pub current_vector: Option<IntrusionVector>,
    pub predicted_arrival_days: Option<f32>,
    pub predicted_direction: Option<String>,
    pub risk_level: RiskLevelDto,
    pub recommended_actions: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatRequestDto {
    pub user_id: Uuid,
    pub message: String,
    pub farm_context: Option<FarmContextDto>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FarmContextDto {
    pub farm_id: Uuid,
    pub geometry: GeoPolygon,
    pub crop_type: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatResponseDto {
    pub message: String,
    pub function_calls: Vec<FunctionCallDto>,
    pub data: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FunctionCallDto {
    pub function_name: String,
    pub arguments: serde_json::Value,
    pub result: Option<serde_json::Value>,
    pub success: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReportRequestDto {
    pub user_id: Uuid,
    pub farm_id: Uuid,
    pub start_date: DateTime<Utc>,
    pub end_date: DateTime<Utc>,
    pub include_predictions: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReportDto {
    pub id: Uuid,
    pub title: String,
    pub summary: String,
    pub sections: Vec<ReportSectionDto>,
    pub generated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReportSectionDto {
    pub title: String,
    pub content: String,
    pub data: Option<serde_json::Value>,
}
