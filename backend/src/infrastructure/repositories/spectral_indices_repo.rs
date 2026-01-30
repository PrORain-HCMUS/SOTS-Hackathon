use async_trait::async_trait;
use chrono::{DateTime, Utc};
use sqlx::PgPool;
use uuid::Uuid;

use crate::domain::{
    repositories::SpectralIndicesRepository, DomainError, DomainResult, SpectralIndices,
    SpectralMeanValues,
};

pub struct PgSpectralIndicesRepository {
    pool: PgPool,
}

impl PgSpectralIndicesRepository {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[derive(sqlx::FromRow)]
struct SpectralIndicesRow {
    id: Uuid,
    image_id: Uuid,
    farm_id: Uuid,
    calculated_at: DateTime<Utc>,
    ndvi: Option<f32>,
    ndsi: Option<f32>,
    srvi: Option<f32>,
    red_edge_index: Option<f32>,
    mean_values: serde_json::Value,
}

impl From<SpectralIndicesRow> for SpectralIndices {
    fn from(row: SpectralIndicesRow) -> Self {
        let mean_values: SpectralMeanValues =
            serde_json::from_value(row.mean_values).unwrap_or_default();

        SpectralIndices {
            id: row.id,
            image_id: row.image_id,
            farm_id: row.farm_id,
            calculated_at: row.calculated_at,
            ndvi: row.ndvi,
            ndsi: row.ndsi,
            srvi: row.srvi,
            red_edge_index: row.red_edge_index,
            mean_values,
        }
    }
}

#[async_trait]
impl SpectralIndicesRepository for PgSpectralIndicesRepository {
    async fn find_by_farm_id(&self, farm_id: Uuid) -> DomainResult<Vec<SpectralIndices>> {
        let rows = sqlx::query_as::<_, SpectralIndicesRow>(
            r#"
            SELECT id, image_id, farm_id, calculated_at, ndvi, ndsi, srvi,
                   red_edge_index, mean_values
            FROM spectral_indices
            WHERE farm_id = $1
            ORDER BY calculated_at DESC
            "#,
        )
        .bind(farm_id)
        .fetch_all(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(rows.into_iter().map(SpectralIndices::from).collect())
    }

    async fn find_by_farm_and_date_range(
        &self,
        farm_id: Uuid,
        start_date: DateTime<Utc>,
        end_date: DateTime<Utc>,
    ) -> DomainResult<Vec<SpectralIndices>> {
        let rows = sqlx::query_as::<_, SpectralIndicesRow>(
            r#"
            SELECT id, image_id, farm_id, calculated_at, ndvi, ndsi, srvi,
                   red_edge_index, mean_values
            FROM spectral_indices
            WHERE farm_id = $1 AND calculated_at BETWEEN $2 AND $3
            ORDER BY calculated_at ASC
            "#,
        )
        .bind(farm_id)
        .bind(start_date)
        .bind(end_date)
        .fetch_all(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(rows.into_iter().map(SpectralIndices::from).collect())
    }

    async fn find_latest_by_farm(&self, farm_id: Uuid) -> DomainResult<Option<SpectralIndices>> {
        let row = sqlx::query_as::<_, SpectralIndicesRow>(
            r#"
            SELECT id, image_id, farm_id, calculated_at, ndvi, ndsi, srvi,
                   red_edge_index, mean_values
            FROM spectral_indices
            WHERE farm_id = $1
            ORDER BY calculated_at DESC
            LIMIT 1
            "#,
        )
        .bind(farm_id)
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(row.map(SpectralIndices::from))
    }

    async fn create(&self, indices: &SpectralIndices) -> DomainResult<SpectralIndices> {
        let mean_values_json = serde_json::to_value(&indices.mean_values)
            .map_err(|e| DomainError::database(e.to_string()))?;

        let row = sqlx::query_as::<_, SpectralIndicesRow>(
            r#"
            INSERT INTO spectral_indices (id, image_id, farm_id, calculated_at, ndvi, ndsi,
                                         srvi, red_edge_index, mean_values)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id, image_id, farm_id, calculated_at, ndvi, ndsi, srvi,
                      red_edge_index, mean_values
            "#,
        )
        .bind(indices.id)
        .bind(indices.image_id)
        .bind(indices.farm_id)
        .bind(indices.calculated_at)
        .bind(indices.ndvi)
        .bind(indices.ndsi)
        .bind(indices.srvi)
        .bind(indices.red_edge_index)
        .bind(&mean_values_json)
        .fetch_one(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(SpectralIndices::from(row))
    }

    async fn batch_create(&self, indices: &[SpectralIndices]) -> DomainResult<Vec<SpectralIndices>> {
        let mut results = Vec::with_capacity(indices.len());

        for idx in indices {
            let created = self.create(idx).await?;
            results.push(created);
        }

        Ok(results)
    }
}
