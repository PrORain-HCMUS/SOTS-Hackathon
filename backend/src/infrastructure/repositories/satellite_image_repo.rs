use async_trait::async_trait;
use chrono::{DateTime, Utc};
use sqlx::PgPool;
use uuid::Uuid;

use crate::domain::{
    repositories::SatelliteImageRepository, DomainError, DomainResult, GeoPolygon, SatelliteImage,
    SatelliteSource, SpectralBand,
};

pub struct PgSatelliteImageRepository {
    pool: PgPool,
}

impl PgSatelliteImageRepository {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[derive(sqlx::FromRow)]
struct SatelliteImageRow {
    id: Uuid,
    source: String,
    acquisition_date: DateTime<Utc>,
    cloud_cover_percentage: f32,
    geometry_json: serde_json::Value,
    file_path: String,
    bands: serde_json::Value,
    processed: bool,
    created_at: DateTime<Utc>,
}

impl From<SatelliteImageRow> for SatelliteImage {
    fn from(row: SatelliteImageRow) -> Self {
        let geometry: GeoPolygon = serde_json::from_value(row.geometry_json).unwrap_or(GeoPolygon {
            coordinates: vec![],
            crs: "EPSG:4326".to_string(),
        });

        let bands: Vec<SpectralBand> = serde_json::from_value(row.bands).unwrap_or_default();

        let source = match row.source.as_str() {
            "sentinel2" => SatelliteSource::Sentinel2,
            "sentinel1" => SatelliteSource::Sentinel1,
            "landsat8" => SatelliteSource::Landsat8,
            _ => SatelliteSource::Sentinel2,
        };

        SatelliteImage {
            id: row.id,
            source,
            acquisition_date: row.acquisition_date,
            cloud_cover_percentage: row.cloud_cover_percentage,
            geometry,
            file_path: row.file_path,
            bands,
            processed: row.processed,
            created_at: row.created_at,
        }
    }
}

fn source_to_string(source: &SatelliteSource) -> String {
    match source {
        SatelliteSource::Sentinel2 => "sentinel2".to_string(),
        SatelliteSource::Sentinel1 => "sentinel1".to_string(),
        SatelliteSource::Landsat8 => "landsat8".to_string(),
    }
}

#[async_trait]
impl SatelliteImageRepository for PgSatelliteImageRepository {
    async fn find_by_id(&self, id: Uuid) -> DomainResult<Option<SatelliteImage>> {
        let row = sqlx::query_as::<_, SatelliteImageRow>(
            r#"
            SELECT id, source, acquisition_date, cloud_cover_percentage,
                   ST_AsGeoJSON(geometry)::jsonb as geometry_json,
                   file_path, bands, processed, created_at
            FROM satellite_images
            WHERE id = $1
            "#,
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(row.map(SatelliteImage::from))
    }

    async fn find_by_geometry_and_date_range(
        &self,
        geometry: &GeoPolygon,
        start_date: DateTime<Utc>,
        end_date: DateTime<Utc>,
    ) -> DomainResult<Vec<SatelliteImage>> {
        let geometry_json = serde_json::to_string(geometry)
            .map_err(|e| DomainError::geo_processing(e.to_string()))?;

        let rows = sqlx::query_as::<_, SatelliteImageRow>(
            r#"
            SELECT id, source, acquisition_date, cloud_cover_percentage,
                   ST_AsGeoJSON(geometry)::jsonb as geometry_json,
                   file_path, bands, processed, created_at
            FROM satellite_images
            WHERE ST_Intersects(geometry, ST_GeomFromGeoJSON($1))
              AND acquisition_date BETWEEN $2 AND $3
            ORDER BY acquisition_date DESC
            "#,
        )
        .bind(&geometry_json)
        .bind(start_date)
        .bind(end_date)
        .fetch_all(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(rows.into_iter().map(SatelliteImage::from).collect())
    }

    async fn find_unprocessed(&self, limit: i64) -> DomainResult<Vec<SatelliteImage>> {
        let rows = sqlx::query_as::<_, SatelliteImageRow>(
            r#"
            SELECT id, source, acquisition_date, cloud_cover_percentage,
                   ST_AsGeoJSON(geometry)::jsonb as geometry_json,
                   file_path, bands, processed, created_at
            FROM satellite_images
            WHERE processed = false
            ORDER BY acquisition_date ASC
            LIMIT $1
            "#,
        )
        .bind(limit)
        .fetch_all(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(rows.into_iter().map(SatelliteImage::from).collect())
    }

    async fn create(&self, image: &SatelliteImage) -> DomainResult<SatelliteImage> {
        let geometry_json = serde_json::to_string(&image.geometry)
            .map_err(|e| DomainError::geo_processing(e.to_string()))?;

        let bands_json = serde_json::to_value(&image.bands)
            .map_err(|e| DomainError::database(e.to_string()))?;

        let row = sqlx::query_as::<_, SatelliteImageRow>(
            r#"
            INSERT INTO satellite_images (id, source, acquisition_date, cloud_cover_percentage,
                                         geometry, file_path, bands, processed, created_at)
            VALUES ($1, $2, $3, $4, ST_GeomFromGeoJSON($5), $6, $7, $8, $9)
            RETURNING id, source, acquisition_date, cloud_cover_percentage,
                      ST_AsGeoJSON(geometry)::jsonb as geometry_json,
                      file_path, bands, processed, created_at
            "#,
        )
        .bind(image.id)
        .bind(source_to_string(&image.source))
        .bind(image.acquisition_date)
        .bind(image.cloud_cover_percentage)
        .bind(&geometry_json)
        .bind(&image.file_path)
        .bind(&bands_json)
        .bind(image.processed)
        .bind(image.created_at)
        .fetch_one(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(SatelliteImage::from(row))
    }

    async fn mark_processed(&self, id: Uuid) -> DomainResult<()> {
        sqlx::query("UPDATE satellite_images SET processed = true WHERE id = $1")
            .bind(id)
            .execute(&self.pool)
            .await
            .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(())
    }

    async fn delete(&self, id: Uuid) -> DomainResult<()> {
        sqlx::query("DELETE FROM satellite_images WHERE id = $1")
            .bind(id)
            .execute(&self.pool)
            .await
            .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(())
    }
}
