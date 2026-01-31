use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Report {
    pub id: i64,
    pub user_id: i64,
    pub title: String,
    pub report_type: String,
    pub status: String,
    pub progress: Option<i32>,
    pub file_path: Option<String>,
    pub file_size_bytes: Option<i64>,
    pub parameters: Option<serde_json::Value>,
    pub generated_at: Option<DateTime<Utc>>,
    pub scheduled_for: Option<DateTime<Utc>>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ReportResponse {
    pub id: String,
    pub title: String,
    pub date: String,
    pub report_type: String,
    pub status: String,
    pub size: String,
    pub progress: Option<i32>,
}

impl From<Report> for ReportResponse {
    fn from(r: Report) -> Self {
        let size = r.file_size_bytes
            .map(|s| {
                if s >= 1_000_000 {
                    format!("{:.1} MB", s as f64 / 1_000_000.0)
                } else if s >= 1_000 {
                    format!("{:.1} KB", s as f64 / 1_000.0)
                } else {
                    format!("{} B", s)
                }
            })
            .unwrap_or_else(|| "-".to_string());
        
        ReportResponse {
            id: r.id.to_string(),
            title: r.title,
            date: r.scheduled_for
                .or(r.generated_at)
                .unwrap_or(r.created_at)
                .format("%Y-%m-%d")
                .to_string(),
            report_type: format_report_type(&r.report_type),
            status: r.status,
            size,
            progress: r.progress,
        }
    }
}

fn format_report_type(t: &str) -> String {
    match t {
        "performance" => "Performance",
        "risk_assessment" => "Risk Assessment",
        "resource_audit" => "Resource Audit",
        "quarterly" => "Quarterly",
        "weekly" => "Weekly",
        "seasonal" => "Seasonal",
        "custom" => "Custom",
        _ => t,
    }.to_string()
}

#[derive(Debug, Deserialize)]
pub struct CreateReportRequest {
    pub title: String,
    pub report_type: String,
    pub scheduled_for: Option<DateTime<Utc>>,
    pub parameters: Option<serde_json::Value>,
}

#[derive(Debug, Deserialize)]
pub struct GenerateReportRequest {
    pub report_type: String,
    pub title: Option<String>,
    pub parameters: Option<serde_json::Value>,
}

#[derive(Debug, Deserialize)]
pub struct ExportRequest {
    pub data_type: String, // "farms", "alerts", "analytics", "all"
    pub time_range: Option<String>,
    pub region: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct ExportResponse {
    pub format: String,
    pub data: serde_json::Value,
    pub generated_at: DateTime<Utc>,
    pub record_count: i64,
}

#[derive(Debug, Serialize)]
pub struct ReportTemplate {
    pub id: String,
    pub title: String,
    pub description: String,
    pub report_type: String,
    pub icon: String,
    pub color: String,
}

#[derive(Debug, Deserialize)]
pub struct ReportListQuery {
    pub status: Option<String>,
    pub report_type: Option<String>,
    pub limit: Option<i64>,
    pub offset: Option<i64>,
}
