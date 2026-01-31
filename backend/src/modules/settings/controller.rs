use axum::{
    extract::{Path, State},
    response::IntoResponse,
    Extension, Json,
};
use chrono::{Utc, Duration};
use crate::shared::{AppState, error::{AppResult, AppError}};
use crate::modules::auth::models::Claims;
use super::{models::*, repository};

pub async fn get_preferences(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
) -> AppResult<impl IntoResponse> {
    let prefs = repository::get_or_create_preferences(claims.sub, state.db()).await?;
    Ok(Json(PreferencesResponse::from(prefs)))
}

pub async fn update_preferences(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Json(req): Json<UpdatePreferencesRequest>,
) -> AppResult<impl IntoResponse> {
    // Validate data retention days
    if let Some(days) = req.data_retention_days {
        if ![30, 90, 365].contains(&days) {
            return Err(AppError::BadRequest("Invalid data retention days. Valid values: 30, 90, 365".to_string()));
        }
    }
    
    // Validate theme
    if let Some(ref theme) = req.theme {
        if !["light", "dark", "system"].contains(&theme.as_str()) {
            return Err(AppError::BadRequest("Invalid theme. Valid values: light, dark, system".to_string()));
        }
    }
    
    // Validate refresh interval
    if let Some(interval) = req.refresh_interval_minutes {
        if interval < 1 || interval > 60 {
            return Err(AppError::BadRequest("Refresh interval must be between 1 and 60 minutes".to_string()));
        }
    }
    
    let prefs = repository::update_preferences(claims.sub, &req, state.db()).await?;
    Ok(Json(PreferencesResponse::from(prefs)))
}

pub async fn list_integrations(
    State(state): State<AppState>,
) -> AppResult<impl IntoResponse> {
    let integrations = repository::list_integrations(state.db()).await?;
    let responses: Vec<IntegrationResponse> = integrations.into_iter().map(Into::into).collect();
    Ok(Json(responses))
}

pub async fn toggle_integration(
    State(state): State<AppState>,
    Path(id): Path<i64>,
) -> AppResult<impl IntoResponse> {
    let integration = repository::get_integration_by_id(id, state.db()).await?
        .ok_or_else(|| AppError::NotFound("Integration not found".to_string()))?;
    
    // Toggle status
    let new_status = match integration.status.as_str() {
        "connected" | "active" => "offline",
        "offline" | "disconnected" => "connected",
        _ => "connected",
    };
    
    let updated = repository::update_integration_status(id, new_status, state.db()).await?;
    Ok(Json(IntegrationResponse::from(updated)))
}

pub async fn export_global_data(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
) -> AppResult<impl IntoResponse> {
    let data = repository::get_global_export_data(claims.sub, state.db()).await?;
    
    // In a real implementation, this would create a file and return a download URL
    // For now, return the data directly with metadata
    let response = DataExportResponse {
        success: true,
        message: "Data export prepared successfully".to_string(),
        download_url: Some(format!("/api/settings/exports/{}", claims.sub)),
        expires_at: Some(Utc::now() + Duration::hours(24)),
    };
    
    Ok(Json(serde_json::json!({
        "metadata": response,
        "data": data
    })))
}

pub async fn purge_cache(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
) -> AppResult<impl IntoResponse> {
    let purged = repository::purge_cache(claims.sub, state.db()).await?;
    
    let response = CachePurgeResponse {
        success: true,
        message: "Cache purged successfully".to_string(),
        purged_items: purged,
    };
    
    Ok(Json(response))
}
