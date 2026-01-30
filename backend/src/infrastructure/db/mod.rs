use sqlx::postgres::{PgPool, PgPoolOptions};
use std::sync::Arc;
use std::time::Duration;

use crate::config::DatabaseConfig;
use crate::domain::DomainError;

#[derive(Clone)]
pub struct Database {
    pool: Arc<PgPool>,
}

impl Database {
    pub async fn connect(config: &DatabaseConfig) -> Result<Self, DomainError> {
        let pool = PgPoolOptions::new()
            .max_connections(config.max_connections)
            .acquire_timeout(Duration::from_secs(30))
            .idle_timeout(Duration::from_secs(600))
            .max_lifetime(Duration::from_secs(1800))
            .connect(&config.url)
            .await
            .map_err(|e| DomainError::database(format!("Failed to connect to database: {}", e)))?;

        tracing::info!("Database connection pool established");

        Ok(Self {
            pool: Arc::new(pool),
        })
    }

    pub fn pool(&self) -> &PgPool {
        &self.pool
    }

    pub async fn health_check(&self) -> Result<(), DomainError> {
        sqlx::query("SELECT 1")
            .execute(self.pool())
            .await
            .map_err(|e| DomainError::database(format!("Health check failed: {}", e)))?;
        Ok(())
    }

    pub async fn run_migrations(&self) -> Result<(), DomainError> {
        sqlx::migrate!("./migrations")
            .run(self.pool())
            .await
            .map_err(|e| DomainError::database(format!("Migration failed: {}", e)))?;

        tracing::info!("Database migrations completed");
        Ok(())
    }
}
