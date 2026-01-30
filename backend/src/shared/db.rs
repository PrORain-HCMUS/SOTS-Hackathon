use sqlx::{postgres::PgPoolOptions, PgPool};
use anyhow::Result;

pub async fn init_pool(database_url: &str) -> Result<PgPool> {
    let pool = PgPoolOptions::new()
        .max_connections(10)
        .acquire_timeout(std::time::Duration::from_secs(5))
        .connect(database_url)
        .await?;

    sqlx::query("CREATE EXTENSION IF NOT EXISTS postgis")
        .execute(&pool)
        .await?;

    sqlx::migrate!("./migrations")
        .run(&pool)
        .await?;

    Ok(pool)
}
