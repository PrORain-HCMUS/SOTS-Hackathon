pub mod models;
pub mod repository;
pub mod controller;

use axum::{routing::get, Router};
use crate::shared::AppState;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/tiles", get(controller::get_tiles))
        .route("/tiles/{tile_id}", get(controller::get_tile_by_id))
        .route("/tiles/{tile_id}/stats", get(controller::get_tile_stats))
        .route("/crop-classes", get(controller::get_crop_classes))
        .route("/coverage", get(controller::get_coverage_area))
}
