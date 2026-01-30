use axum::{
    extract::{Path, State},
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use crate::shared::{AppState, AppResult, error::AppError};
use super::models::{AnalysisRequest, AnalysisResult};
use super::service;
use super::repository;
use super::ai::image_proc::{preprocess_image, postprocess_segmentation};

pub async fn trigger_analysis(
    State(state): State<AppState>,
    Json(payload): Json<AnalysisRequest>,
) -> AppResult<impl IntoResponse> {
    let farm_id = payload.farm_id;

    let ai_engine = state.ai_engine.as_ref()
        .ok_or_else(|| AppError::AiEngine("AI Engine not initialized".to_string()))?;

    let image_bytes = payload.image_base64
        .ok_or_else(|| AppError::BadRequest("image_base64 is required".to_string()))
        .and_then(|b64| {
            base64::Engine::decode(&base64::engine::general_purpose::STANDARD, b64)
                .map_err(|e| AppError::BadRequest(format!("Invalid base64: {}", e)))
        })?;

    let config = ai_engine.config();
    let device = ai_engine.device();

    let input_tensor = preprocess_image(&image_bytes, config, device)?;
    let output_tensor = ai_engine.predict(&input_tensor)?;

    let water_class_idx = config.classes
        .iter()
        .position(|c| c == "water")
        .unwrap_or(1);

    let water_pixels = postprocess_segmentation(&output_tensor, water_class_idx)?;

    let water_coverage_percent = if config.img_size > 0 {
        (water_pixels.len() as f64 / (config.img_size * config.img_size) as f64) * 100.0
    } else {
        0.0
    };

    let ndsi_value = water_coverage_percent / 100.0;
    service::save_ndsi_measurement(farm_id, ndsi_value, "ai_analysis", &state.db).await?;

    let alert = service::detect_salinity_anomaly(farm_id, &state.db).await?;

    let intrusion_vector = if !water_pixels.is_empty() {
        service::calculate_intrusion_vector(farm_id, &water_pixels, &state.db).await?
    } else {
        None
    };

    let result = AnalysisResult {
        farm_id,
        current_ndsi: ndsi_value,
        alert,
        intrusion_vector,
        water_coverage_percent,
    };

    Ok((StatusCode::OK, Json(result)))
}

pub async fn get_alerts(
    State(state): State<AppState>,
    Path(farm_id): Path<i64>,
) -> AppResult<impl IntoResponse> {
    let alerts = repository::get_recent_alerts(farm_id, 10, &state.db).await?;
    Ok(Json(alerts))
}

pub async fn get_salinity_history(
    State(state): State<AppState>,
    Path(farm_id): Path<i64>,
) -> AppResult<impl IntoResponse> {
    let history = repository::get_ndsi_history(farm_id, 30, &state.db).await?;
    Ok(Json(history))
}

pub async fn get_intrusion_vector(
    State(state): State<AppState>,
    Path(farm_id): Path<i64>,
) -> AppResult<impl IntoResponse> {
    let vector = repository::get_latest_intrusion_vector(farm_id, &state.db).await?;
    Ok(Json(vector))
}

pub async fn get_farm_status(
    State(state): State<AppState>,
    Path(farm_id): Path<i64>,
) -> AppResult<impl IntoResponse> {
    let status = service::get_farm_status(farm_id, &state.db).await?;
    Ok(Json(status))
}

pub async fn health_check() -> impl IntoResponse {
    Json(serde_json::json!({
        "status": "healthy",
        "module": "monitoring"
    }))
}