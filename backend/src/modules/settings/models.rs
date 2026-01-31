use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct UserPreferences {
    pub id: i64,
    pub user_id: i64,
    pub auto_refresh: bool,
    pub refresh_interval_minutes: i32,
    pub notifications_enabled: bool,
    pub email_alerts_enabled: bool,
    pub data_retention_days: i32,
    pub theme: String,
    pub language: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PreferencesResponse {
    pub auto_refresh: bool,
    pub refresh_interval_minutes: i32,
    pub notifications_enabled: bool,
    pub email_alerts_enabled: bool,
    pub data_retention_days: i32,
    pub theme: String,
    pub language: String,
}

impl From<UserPreferences> for PreferencesResponse {
    fn from(p: UserPreferences) -> Self {
        PreferencesResponse {
            auto_refresh: p.auto_refresh,
            refresh_interval_minutes: p.refresh_interval_minutes,
            notifications_enabled: p.notifications_enabled,
            email_alerts_enabled: p.email_alerts_enabled,
            data_retention_days: p.data_retention_days,
            theme: p.theme,
            language: p.language,
        }
    }
}

#[derive(Debug, Deserialize)]
pub struct UpdatePreferencesRequest {
    pub auto_refresh: Option<bool>,
    pub refresh_interval_minutes: Option<i32>,
    pub notifications_enabled: Option<bool>,
    pub email_alerts_enabled: Option<bool>,
    pub data_retention_days: Option<i32>,
    pub theme: Option<String>,
    pub language: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, sqlx::FromRow)]
pub struct Integration {
    pub id: i64,
    pub name: String,
    pub integration_type: String,
    pub status: String,
    pub api_endpoint: Option<String>,
    pub last_sync_at: Option<DateTime<Utc>>,
    pub config: Option<serde_json::Value>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Serialize)]
pub struct IntegrationResponse {
    pub id: i64,
    pub name: String,
    pub integration_type: String,
    pub status: String,
    pub last_sync_at: Option<DateTime<Utc>>,
    pub connected: bool,
}

impl From<Integration> for IntegrationResponse {
    fn from(i: Integration) -> Self {
        let connected = matches!(i.status.as_str(), "connected" | "active");
        IntegrationResponse {
            id: i.id,
            name: i.name,
            integration_type: i.integration_type,
            status: i.status,
            last_sync_at: i.last_sync_at,
            connected,
        }
    }
}

#[derive(Debug, Serialize)]
pub struct DataExportResponse {
    pub success: bool,
    pub message: String,
    pub download_url: Option<String>,
    pub expires_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Serialize)]
pub struct CachePurgeResponse {
    pub success: bool,
    pub message: String,
    pub purged_items: i64,
}
