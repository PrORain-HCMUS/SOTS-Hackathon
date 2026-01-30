use axum::{
    routing::{delete, get, post, put},
    Router,
};
use std::sync::Arc;
use tower_http::{
    compression::CompressionLayer,
    cors::{Any, CorsLayer},
    trace::TraceLayer,
};

use crate::config::AppConfig;

use super::handlers::{auth, chatbot, farm, health, monitoring};
use super::middleware::auth::AuthLayer;

#[derive(Clone)]
pub struct AppState {
    pub config: AppConfig,
    pub db: crate::infrastructure::Database,
}

pub fn create_router(state: AppState) -> Router {
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    let public_routes = Router::new()
        .route("/health", get(health::health_check))
        .route("/health/ready", get(health::readiness_check))
        .route("/auth/login", post(auth::login))
        .route("/auth/register", post(auth::register));

    let farm_routes = Router::new()
        .route("/", get(farm::list_farms))
        .route("/", post(farm::create_farm))
        .route("/:id", get(farm::get_farm))
        .route("/:id", put(farm::update_farm))
        .route("/:id", delete(farm::delete_farm))
        .route("/:id/indices", get(farm::get_farm_indices))
        .route("/:id/alerts", get(farm::get_farm_alerts));

    let monitoring_routes = Router::new()
        .route("/status", get(monitoring::get_status))
        .route("/alerts", get(monitoring::list_alerts))
        .route("/alerts/:id/acknowledge", post(monitoring::acknowledge_alert))
        .route("/salinity", get(monitoring::get_salinity_data))
        .route("/intrusion-vector", get(monitoring::get_intrusion_vector))
        .route("/process", post(monitoring::trigger_processing));

    let chatbot_routes = Router::new()
        .route("/message", post(chatbot::send_message))
        .route("/todos", get(chatbot::list_todos))
        .route("/todos", post(chatbot::create_todo))
        .route("/todos/:id", put(chatbot::update_todo))
        .route("/todos/:id/complete", post(chatbot::complete_todo))
        .route("/report", post(chatbot::generate_report));

    let protected_routes = Router::new()
        .nest("/farms", farm_routes)
        .nest("/monitoring", monitoring_routes)
        .nest("/chatbot", chatbot_routes)
        .layer(AuthLayer::new(state.config.jwt.secret.clone()));

    Router::new()
        .nest("/api/v1", public_routes)
        .nest("/api/v1", protected_routes)
        .layer(TraceLayer::new_for_http())
        .layer(CompressionLayer::new())
        .layer(cors)
        .with_state(Arc::new(state))
}
