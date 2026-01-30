use axum::{
    extract::{Path, Query, State},
    Extension, Json,
};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use uuid::Uuid;

use crate::api::handlers::ApiResponse;
use crate::api::middleware::auth::Claims;
use crate::api::routes::AppState;
use crate::domain::{Alert, DomainError, IntrusionVector};

#[derive(Debug, Deserialize)]
pub struct DateRangeQuery {
    pub start_date: Option<DateTime<Utc>>,
    pub end_date: Option<DateTime<Utc>>,
    pub farm_id: Option<Uuid>,
}

#[derive(Debug, Deserialize)]
pub struct SalinityQuery {
    pub farm_id: Uuid,
    pub start_date: Option<DateTime<Utc>>,
    pub end_date: Option<DateTime<Utc>>,
}

#[derive(Debug, Serialize)]
pub struct MonitoringStatus {
    pub total_farms: u32,
    pub active_alerts: u32,
    pub critical_alerts: u32,
    pub last_satellite_update: Option<DateTime<Utc>>,
    pub processing_queue_size: u32,
}

#[derive(Debug, Serialize)]
pub struct SalinityDataPoint {
    pub timestamp: DateTime<Utc>,
    pub ndsi: f32,
    pub trend: String,
    pub is_anomaly: bool,
}

#[derive(Debug, Serialize)]
pub struct SalinityResponse {
    pub farm_id: Uuid,
    pub current_ndsi: f32,
    pub trend: String,
    pub risk_level: String,
    pub history: Vec<SalinityDataPoint>,
}

#[derive(Debug, Serialize)]
pub struct IntrusionVectorResponse {
    pub vector: Option<IntrusionVector>,
    pub prediction: Option<IntrusionPrediction>,
}

#[derive(Debug, Serialize)]
pub struct IntrusionPrediction {
    pub days_to_reach_farm: Option<f32>,
    pub predicted_direction: String,
    pub risk_level: String,
    pub affected_area_hectares: f64,
}

#[derive(Debug, Deserialize)]
pub struct ProcessingTrigger {
    pub farm_ids: Option<Vec<Uuid>>,
    pub force_refresh: bool,
}

pub async fn get_status(
    State(_state): State<Arc<AppState>>,
    Extension(claims): Extension<Claims>,
) -> Result<Json<ApiResponse<MonitoringStatus>>, DomainError> {
    tracing::info!("Getting monitoring status for user: {}", claims.sub);

    Ok(Json(ApiResponse::success(MonitoringStatus {
        total_farms: 0,
        active_alerts: 0,
        critical_alerts: 0,
        last_satellite_update: None,
        processing_queue_size: 0,
    })))
}

pub async fn list_alerts(
    State(_state): State<Arc<AppState>>,
    Extension(claims): Extension<Claims>,
    Query(query): Query<DateRangeQuery>,
) -> Result<Json<ApiResponse<Vec<Alert>>>, DomainError> {
    tracing::info!(
        "Listing alerts for user: {}, farm: {:?}",
        claims.sub,
        query.farm_id
    );

    Ok(Json(ApiResponse::success(vec![])))
}

pub async fn acknowledge_alert(
    State(_state): State<Arc<AppState>>,
    Extension(claims): Extension<Claims>,
    Path(id): Path<Uuid>,
) -> Result<Json<ApiResponse<()>>, DomainError> {
    tracing::info!("Acknowledging alert {} for user: {}", id, claims.sub);

    Ok(Json(ApiResponse::success(())))
}

pub async fn get_salinity_data(
    State(_state): State<Arc<AppState>>,
    Extension(claims): Extension<Claims>,
    Query(query): Query<SalinityQuery>,
) -> Result<Json<ApiResponse<SalinityResponse>>, DomainError> {
    tracing::info!(
        "Getting salinity data for farm {} user: {}",
        query.farm_id,
        claims.sub
    );

    Ok(Json(ApiResponse::success(SalinityResponse {
        farm_id: query.farm_id,
        current_ndsi: 0.0,
        trend: "stable".to_string(),
        risk_level: "low".to_string(),
        history: vec![],
    })))
}

pub async fn get_intrusion_vector(
    State(_state): State<Arc<AppState>>,
    Extension(claims): Extension<Claims>,
    Query(query): Query<SalinityQuery>,
) -> Result<Json<ApiResponse<IntrusionVectorResponse>>, DomainError> {
    tracing::info!(
        "Getting intrusion vector for farm {} user: {}",
        query.farm_id,
        claims.sub
    );

    Ok(Json(ApiResponse::success(IntrusionVectorResponse {
        vector: None,
        prediction: None,
    })))
}

pub async fn trigger_processing(
    State(_state): State<Arc<AppState>>,
    Extension(claims): Extension<Claims>,
    Json(payload): Json<ProcessingTrigger>,
) -> Result<Json<ApiResponse<String>>, DomainError> {
    tracing::info!(
        "Triggering processing for user: {}, farms: {:?}",
        claims.sub,
        payload.farm_ids
    );

    Ok(Json(ApiResponse::success(
        "Processing triggered successfully".to_string(),
    )))
}
