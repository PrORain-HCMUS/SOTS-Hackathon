use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Serialize, Deserialize)]
pub struct DashboardStats {
    pub monitoring_area: StatItem,
    pub avg_yield: StatItem,
    pub risk_alerts: StatItem,
    pub harvest_forecast: StatItem,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct StatItem {
    pub label: String,
    pub value: String,
    pub change: String,
    pub trend: String, // "up", "down", "neutral"
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RecentAlert {
    pub id: i64,
    pub alert_type: String, // "error", "warning", "info"
    pub title: String,
    pub subtitle: String,
    pub time_ago: String,
    pub farm_id: i64,
    pub farm_name: Option<String>,
    pub detected_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SystemStatus {
    pub status: String, // "active", "degraded", "offline"
    pub sensors_count: i64,
    pub sensors_health_percentage: f64,
    pub active_incidents: i64,
    pub last_sync_at: Option<DateTime<Utc>>,
    pub integrations: Vec<IntegrationStatus>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct IntegrationStatus {
    pub name: String,
    pub integration_type: String,
    pub status: String,
    pub last_sync_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Deserialize)]
pub struct StatsQuery {
    pub region: Option<String>,
    pub time_range: Option<String>, // "24h", "7d", "30d", "90d"
}
