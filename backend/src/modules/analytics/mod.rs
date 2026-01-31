pub mod models;
pub mod repository;
pub mod controller;

use axum::{routing::get, Router};
use crate::shared::AppState;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/kpis", get(controller::get_kpis))
        .route("/regional-metrics", get(controller::get_regional_metrics))
        .route("/yield-trends", get(controller::get_yield_trends))
        .route("/performance", get(controller::get_regional_performance))
}
