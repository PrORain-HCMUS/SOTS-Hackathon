pub mod ai;
pub mod controller;
pub mod models;
pub mod repository;
pub mod service;

use axum::{routing::{get, post}, Router};
use crate::shared::AppState;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/health", get(controller::health_check))
        .route("/analyze", post(controller::trigger_analysis))
        .route("/alerts/{farm_id}", get(controller::get_alerts))
        .route("/salinity/{farm_id}", get(controller::get_salinity_history))
        .route("/vector/{farm_id}", get(controller::get_intrusion_vector))
        .route("/status/{farm_id}", get(controller::get_farm_status))
}
