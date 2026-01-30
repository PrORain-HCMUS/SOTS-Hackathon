use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fmt;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Alert {
    pub id: i64,
    pub farm_id: i64,
    pub severity: AlertSeverity,
    pub message: String,
    pub metadata: Option<serde_json::Value>,
    pub detected_at: DateTime<Utc>,
    pub acknowledged: bool,
    pub acknowledged_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AlertSeverity {
    Low,
    Medium,
    High,
    Critical,
}

impl AlertSeverity {
    pub fn as_str(&self) -> &str {
        match self {
            AlertSeverity::Low => "low",
            AlertSeverity::Medium => "medium",
            AlertSeverity::High => "high",
            AlertSeverity::Critical => "critical",
        }
    }
}

impl fmt::Display for AlertSeverity {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.as_str())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SalinityLog {
    pub id: i64,
    pub farm_id: i64,
    pub ndsi_value: f64,
    pub source: String,
    pub recorded_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntrusionVector {
    pub id: i64,
    pub farm_id: i64,
    pub direction: String,
    pub angle_degrees: f64,
    pub magnitude_km: f64,
    pub calculated_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct AnalysisRequest {
    pub farm_id: i64,
    #[serde(default)]
    pub image_base64: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AnalysisResult {
    pub farm_id: i64,
    pub current_ndsi: f64,
    pub alert: Option<Alert>,
    pub intrusion_vector: Option<IntrusionVector>,
    pub water_coverage_percent: f64,
}

#[derive(Debug, Serialize)]
pub struct FarmStatus {
    pub farm_id: i64,
    pub latest_ndsi: Option<f64>,
    pub recent_alerts: Vec<Alert>,
    pub latest_intrusion_vector: Option<IntrusionVector>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateAlert {
    pub farm_id: i64,
    pub severity: AlertSeverity,
    pub message: String,
    pub metadata: Option<serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateSalinityLog {
    pub farm_id: i64,
    pub ndsi_value: f64,
    pub source: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateIntrusionVector {
    pub farm_id: i64,
    pub direction: String,
    pub angle_degrees: f64,
    pub magnitude_km: f64,
}