use std::net::SocketAddr;

use tokio::net::TcpListener;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use backend::{
    api::{create_router, routes::AppState},
    config::AppConfig,
    infrastructure::Database,
};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "info,bio_radar_backend=debug,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    tracing::info!("🚀 Starting Bio-Radar Backend...");

    let config = AppConfig::load();
    tracing::info!("Configuration loaded");

    let db = Database::connect(&config.database).await?;
    tracing::info!("Database connected");

    let state = AppState {
        config: config.clone(),
        db,
    };

    let app = create_router(state);

    let addr = SocketAddr::from((
        config.server.host.parse::<std::net::IpAddr>().unwrap_or([0, 0, 0, 0].into()),
        config.server.port,
    ));

    tracing::info!("🌐 Server listening on http://{}", addr);

    let listener = TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;

    Ok(())
}
