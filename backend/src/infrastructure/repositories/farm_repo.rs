use async_trait::async_trait;
use sqlx::PgPool;
use uuid::Uuid;

use crate::domain::{repositories::FarmRepository, CropType, DomainError, DomainResult, Farm, GeoPolygon};

pub struct PgFarmRepository {
    pool: PgPool,
}

impl PgFarmRepository {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    fn parse_crop_type(s: Option<String>) -> Option<CropType> {
        s.map(|t| match t.as_str() {
            "rice" => CropType::Rice,
            "durian" => CropType::Durian,
            "mango" => CropType::Mango,
            "coconut" => CropType::Coconut,
            "shrimp" => CropType::Shrimp,
            other => CropType::Other(other.to_string()),
        })
    }

    fn crop_type_to_string(crop: &Option<CropType>) -> Option<String> {
        crop.as_ref().map(|c| match c {
            CropType::Rice => "rice".to_string(),
            CropType::Durian => "durian".to_string(),
            CropType::Mango => "mango".to_string(),
            CropType::Coconut => "coconut".to_string(),
            CropType::Shrimp => "shrimp".to_string(),
            CropType::Other(s) => s.clone(),
        })
    }
}

#[derive(sqlx::FromRow)]
struct FarmRow {
    id: Uuid,
    user_id: Uuid,
    name: String,
    geometry_json: serde_json::Value,
    area_hectares: f64,
    crop_type: Option<String>,
    created_at: chrono::DateTime<chrono::Utc>,
    updated_at: chrono::DateTime<chrono::Utc>,
}

impl From<FarmRow> for Farm {
    fn from(row: FarmRow) -> Self {
        let geometry: GeoPolygon = serde_json::from_value(row.geometry_json)
            .unwrap_or(GeoPolygon {
                coordinates: vec![],
                crs: "EPSG:4326".to_string(),
            });

        Farm {
            id: row.id,
            user_id: row.user_id,
            name: row.name,
            geometry,
            area_hectares: row.area_hectares,
            crop_type: PgFarmRepository::parse_crop_type(row.crop_type),
            created_at: row.created_at,
            updated_at: row.updated_at,
        }
    }
}

#[async_trait]
impl FarmRepository for PgFarmRepository {
    async fn find_by_id(&self, id: Uuid) -> DomainResult<Option<Farm>> {
        let row = sqlx::query_as::<_, FarmRow>(
            r#"
            SELECT id, user_id, name, 
                   ST_AsGeoJSON(geometry)::jsonb as geometry_json,
                   area_hectares, crop_type, created_at, updated_at
            FROM farms
            WHERE id = $1
            "#,
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(row.map(Farm::from))
    }

    async fn find_by_user_id(&self, user_id: Uuid) -> DomainResult<Vec<Farm>> {
        let rows = sqlx::query_as::<_, FarmRow>(
            r#"
            SELECT id, user_id, name,
                   ST_AsGeoJSON(geometry)::jsonb as geometry_json,
                   area_hectares, crop_type, created_at, updated_at
            FROM farms
            WHERE user_id = $1
            ORDER BY created_at DESC
            "#,
        )
        .bind(user_id)
        .fetch_all(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(rows.into_iter().map(Farm::from).collect())
    }

    async fn find_by_geometry_intersection(&self, geometry: &GeoPolygon) -> DomainResult<Vec<Farm>> {
        let geometry_json = serde_json::to_string(geometry)
            .map_err(|e| DomainError::geo_processing(e.to_string()))?;

        let rows = sqlx::query_as::<_, FarmRow>(
            r#"
            SELECT id, user_id, name,
                   ST_AsGeoJSON(geometry)::jsonb as geometry_json,
                   area_hectares, crop_type, created_at, updated_at
            FROM farms
            WHERE ST_Intersects(geometry, ST_GeomFromGeoJSON($1))
            "#,
        )
        .bind(&geometry_json)
        .fetch_all(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(rows.into_iter().map(Farm::from).collect())
    }

    async fn create(&self, farm: &Farm) -> DomainResult<Farm> {
        let geometry_json = serde_json::to_string(&farm.geometry)
            .map_err(|e| DomainError::geo_processing(e.to_string()))?;

        let crop_type_str = Self::crop_type_to_string(&farm.crop_type);

        let row = sqlx::query_as::<_, FarmRow>(
            r#"
            INSERT INTO farms (id, user_id, name, geometry, area_hectares, crop_type, created_at, updated_at)
            VALUES ($1, $2, $3, ST_GeomFromGeoJSON($4), $5, $6, $7, $8)
            RETURNING id, user_id, name, ST_AsGeoJSON(geometry)::jsonb as geometry_json,
                      area_hectares, crop_type, created_at, updated_at
            "#,
        )
        .bind(farm.id)
        .bind(farm.user_id)
        .bind(&farm.name)
        .bind(&geometry_json)
        .bind(farm.area_hectares)
        .bind(&crop_type_str)
        .bind(farm.created_at)
        .bind(farm.updated_at)
        .fetch_one(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(Farm::from(row))
    }

    async fn update(&self, farm: &Farm) -> DomainResult<Farm> {
        let geometry_json = serde_json::to_string(&farm.geometry)
            .map_err(|e| DomainError::geo_processing(e.to_string()))?;

        let crop_type_str = Self::crop_type_to_string(&farm.crop_type);

        let row = sqlx::query_as::<_, FarmRow>(
            r#"
            UPDATE farms
            SET name = $2, geometry = ST_GeomFromGeoJSON($3), area_hectares = $4,
                crop_type = $5, updated_at = $6
            WHERE id = $1
            RETURNING id, user_id, name, ST_AsGeoJSON(geometry)::jsonb as geometry_json,
                      area_hectares, crop_type, created_at, updated_at
            "#,
        )
        .bind(farm.id)
        .bind(&farm.name)
        .bind(&geometry_json)
        .bind(farm.area_hectares)
        .bind(&crop_type_str)
        .bind(farm.updated_at)
        .fetch_one(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(Farm::from(row))
    }

    async fn delete(&self, id: Uuid) -> DomainResult<()> {
        sqlx::query("DELETE FROM farms WHERE id = $1")
            .bind(id)
            .execute(&self.pool)
            .await
            .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(())
    }
}
