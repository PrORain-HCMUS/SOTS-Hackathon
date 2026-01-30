mod models;
mod repository;
mod service;
mod controller;

use axum::{routing::{get, post, put, delete}, Router};
use crate::shared::AppState;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/", post(controller::create_farm))
        .route("/", get(controller::list_farms))
        .route("/{id}", get(controller::get_farm))
        .route("/{id}", put(controller::update_farm))
        .route("/{id}", delete(controller::delete_farm))
        .route("/convert/wkt", post(controller::convert_to_wkt))
        .route("/intersect", get(controller::find_intersecting_farms))
}