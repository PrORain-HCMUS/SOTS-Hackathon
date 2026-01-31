pub mod models;
pub mod repository;
pub mod controller;

use axum::{routing::{get, post, delete}, Router};
use crate::shared::AppState;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/", get(controller::list_reports))
        .route("/", post(controller::create_report))
        .route("/{id}", get(controller::get_report))
        .route("/{id}", delete(controller::delete_report))
        .route("/{id}/download", get(controller::download_report))
        .route("/generate", post(controller::generate_report))
        .route("/export/{format}", post(controller::export_data))
        .route("/templates", get(controller::get_templates))
}
