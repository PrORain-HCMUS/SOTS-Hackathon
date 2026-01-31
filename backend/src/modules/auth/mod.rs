pub mod models;
pub mod repository;
pub mod service;
pub mod controller;
pub mod middleware;

use axum::{routing::{post, get}, Router};
use crate::shared::AppState;

pub fn router() -> Router<AppState> {
    Router::new()
        .route("/register", post(controller::register))
        .route("/login", post(controller::login))
}

pub fn protected_router() -> Router<AppState> {
    Router::new()
        .route("/profile", get(controller::get_profile))
}