use axum::{extract::State, http::StatusCode, Json};
use serde::Serialize;
use std::sync::Arc;

use crate::api::routes::AppState;

#[derive(Serialize)]
pub struct HealthResponse {
    pub status: String,
    pub version: String,
    pub timestamp: String,
}

#[derive(Serialize)]
pub struct ReadinessResponse {
    pub status: String,
    pub database: String,
    pub timestamp: String,
}

pub async fn health_check() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "healthy".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        timestamp: chrono::Utc::now().to_rfc3339(),
    })
}

pub async fn readiness_check(
    State(state): State<Arc<AppState>>,
) -> Result<Json<ReadinessResponse>, StatusCode> {
    let db_status = match state.db.health_check().await {
        Ok(_) => "connected".to_string(),
        Err(e) => {
            tracing::error!("Database health check failed: {}", e);
            return Err(StatusCode::SERVICE_UNAVAILABLE);
        }
    };

    Ok(Json(ReadinessResponse {
        status: "ready".to_string(),
        database: db_status,
        timestamp: chrono::Utc::now().to_rfc3339(),
    }))
}
