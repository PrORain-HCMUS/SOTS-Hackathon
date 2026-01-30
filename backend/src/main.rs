mod shared;
mod modules;

use axum::{Router, http::Method, middleware};
use tower_http::cors::{CorsLayer, Any};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};
use std::net::SocketAddr;
use modules::monitoring::ai::engine::AiEngine;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    dotenvy::dotenv().ok();

    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info,backend=debug,sqlx=warn".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    tracing::info!("Starting Bio-Radar Backend Server");

    let database_url = std::env::var("DATABASE_URL")
        .expect("DATABASE_URL must be set");

    tracing::info!("Connecting to database...");
    let db = shared::db::init_pool(&database_url).await?;
    tracing::info!("Database connected successfully");

    let mut state = shared::AppState::new(db);

    if let (Ok(config_path), Ok(weights_path)) = (
        std::env::var("AI_CONFIG_PATH"),
        std::env::var("AI_WEIGHTS_PATH"),
    ) {
        match AiEngine::new(&config_path, &weights_path) {
            Ok(engine) => {
                tracing::info!("AI Engine initialized successfully");
                state = state.with_ai_engine(engine);
            }
            Err(e) => {
                tracing::warn!("AI Engine initialization failed: {}. Continuing without AI.", e);
            }
        }
    } else {
        tracing::info!("AI Engine not configured (AI_CONFIG_PATH or AI_WEIGHTS_PATH missing)");
    }

    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods([Method::GET, Method::POST, Method::PUT, Method::DELETE])
        .allow_headers(Any);

    let app = Router::new()
        .nest("/api/auth", modules::auth_router())
        .nest("/api/monitoring", modules::monitoring_router())
        .nest("/api/farms", modules::farm_mgmt_router())
        .route_layer(middleware::from_fn_with_state(
            state.clone(),
            modules::auth::middleware::auth_middleware
        ))
        .layer(cors)
        .with_state(state);

    let host = std::env::var("SERVER_HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
    let port = std::env::var("SERVER_PORT").unwrap_or_else(|_| "8000".to_string());
    let addr: SocketAddr = format!("{}:{}", host, port).parse()?;

    tracing::info!("Server listening on {}", addr);

    axum::serve(
        tokio::net::TcpListener::bind(addr).await?,
        app,
    ).await?;

    Ok(())
}