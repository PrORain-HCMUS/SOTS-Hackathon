pub mod models;
pub mod repository;
pub mod controller;

use axum::{routing::get, Router};
use crate::shared::AppState;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/stats", get(controller::get_dashboard_stats))
        .route("/alerts/recent", get(controller::get_recent_alerts))
        .route("/system-status", get(controller::get_system_status))
}
