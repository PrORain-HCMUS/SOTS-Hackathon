pub mod models;
pub mod repository;
pub mod controller;

use axum::{routing::{get, put, post}, Router};
use crate::shared::AppState;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/preferences", get(controller::get_preferences))
        .route("/preferences", put(controller::update_preferences))
        .route("/integrations", get(controller::list_integrations))
        .route("/integrations/{id}/toggle", post(controller::toggle_integration))
        .route("/data/export", post(controller::export_global_data))
        .route("/data/purge-cache", post(controller::purge_cache))
}
