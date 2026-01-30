use sqlx::{PgPool, Row};
use crate::shared::error::AppError;
use super::models::Farm;

pub async fn create(
    pool: &PgPool,
    user_id: i64,
    name: &str,
    geojson: &str,
) -> Result<Farm, AppError> {
    sqlx::query_as::<_, Farm>(
        r#"
        INSERT INTO farms (user_id, name, geometry, area_hectares)
        VALUES ($1, $2, ST_GeomFromGeoJSON($3), ST_Area(ST_GeomFromGeoJSON($3)::geography) / 10000)
        RETURNING id, user_id, name, area_hectares, created_at, updated_at
        "#
    )
    .bind(user_id)
    .bind(name)
    .bind(geojson)
    .fetch_one(pool)
    .await
    .map_err(Into::into)
}

pub async fn get_by_id(pool: &PgPool, id: i64) -> Result<Option<Farm>, AppError> {
    sqlx::query_as::<_, Farm>(
        r#"
        SELECT id, user_id, name, area_hectares, created_at, updated_at 
        FROM farms WHERE id = $1
        "#
    )
    .bind(id)
    .fetch_optional(pool)
    .await
    .map_err(Into::into)
}

pub async fn get_by_user_with_geojson(
    pool: &PgPool, 
    user_id: i64
) -> Result<Vec<(Farm, String)>, AppError> {
    let rows = sqlx::query(
        r#"
        SELECT 
            f.id, f.user_id, f.name, f.area_hectares, f.created_at, f.updated_at,
            ST_AsGeoJSON(f.geometry) as geojson
        FROM farms f
        WHERE f.user_id = $1
        ORDER BY f.created_at DESC
        "#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await?;

    rows.into_iter()
        .map(|row| {
            let farm = Farm {
                id: row.get("id"),
                user_id: row.get("user_id"),
                name: row.get("name"),
                area_hectares: row.get("area_hectares"),
                created_at: row.get("created_at"),
                updated_at: row.get("updated_at"),
            };
            let geojson: Option<String> = row.get("geojson");
            Ok((farm, geojson.unwrap_or_else(|| "{}".to_string())))
        })
        .collect()
}

pub async fn update(
    pool: &PgPool,
    id: i64,
    name: Option<&str>,
    geojson: Option<&str>,
) -> Result<Farm, AppError> {
    let farm = if let Some(geo) = geojson {
        sqlx::query_as::<_, Farm>(
            r#"
            UPDATE farms
            SET name = COALESCE($2, name),
                geometry = ST_GeomFromGeoJSON($3),
                area_hectares = ST_Area(ST_GeomFromGeoJSON($3)::geography) / 10000,
                updated_at = NOW()
            WHERE id = $1
            RETURNING id, user_id, name, area_hectares, created_at, updated_at
            "#
        )
        .bind(id)
        .bind(name)
        .bind(geo)
        .fetch_one(pool)
        .await?
    } else {
        sqlx::query_as::<_, Farm>(
            r#"
            UPDATE farms 
            SET name = COALESCE($2, name), updated_at = NOW() 
            WHERE id = $1 
            RETURNING id, user_id, name, area_hectares, created_at, updated_at
            "#
        )
        .bind(id)
        .bind(name)
        .fetch_one(pool)
        .await?
    };

    Ok(farm)
}

pub async fn delete(pool: &PgPool, id: i64) -> Result<(), AppError> {
    let result = sqlx::query("DELETE FROM farms WHERE id = $1")
        .bind(id)
        .execute(pool)
        .await?;

    if result.rows_affected() == 0 {
        return Err(AppError::NotFound(format!("Farm {} not found", id)));
    }

    Ok(())
}

pub async fn find_intersecting(
    pool: &PgPool,
    bbox_geojson: &str,
) -> Result<Vec<Farm>, AppError> {
    sqlx::query_as::<_, Farm>(
        r#"
        SELECT id, user_id, name, area_hectares, created_at, updated_at 
        FROM farms 
        WHERE ST_Intersects(geometry, ST_GeomFromGeoJSON($1))
        "#
    )
    .bind(bbox_geojson)
    .fetch_all(pool)
    .await
    .map_err(Into::into)
}

pub async fn get_geojson(pool: &PgPool, id: i64) -> Result<Option<String>, AppError> {
    sqlx::query_scalar("SELECT ST_AsGeoJSON(geometry) FROM farms WHERE id = $1")
        .bind(id)
        .fetch_optional(pool)
        .await
        .map_err(Into::into)
}