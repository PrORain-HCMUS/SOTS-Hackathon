use async_trait::async_trait;
use chrono::{DateTime, Utc};
use uuid::Uuid;

use super::errors::DomainResult;
use super::models::*;

#[async_trait]
pub trait UserRepository: Send + Sync {
    async fn find_by_id(&self, id: Uuid) -> DomainResult<Option<User>>;
    async fn find_by_email(&self, email: &str) -> DomainResult<Option<User>>;
    async fn create(&self, user: &User) -> DomainResult<User>;
    async fn update(&self, user: &User) -> DomainResult<User>;
    async fn delete(&self, id: Uuid) -> DomainResult<()>;
}

#[async_trait]
pub trait FarmRepository: Send + Sync {
    async fn find_by_id(&self, id: Uuid) -> DomainResult<Option<Farm>>;
    async fn find_by_user_id(&self, user_id: Uuid) -> DomainResult<Vec<Farm>>;
    async fn find_by_geometry_intersection(&self, geometry: &GeoPolygon) -> DomainResult<Vec<Farm>>;
    async fn create(&self, farm: &Farm) -> DomainResult<Farm>;
    async fn update(&self, farm: &Farm) -> DomainResult<Farm>;
    async fn delete(&self, id: Uuid) -> DomainResult<()>;
}

#[async_trait]
pub trait SatelliteImageRepository: Send + Sync {
    async fn find_by_id(&self, id: Uuid) -> DomainResult<Option<SatelliteImage>>;
    async fn find_by_geometry_and_date_range(
        &self,
        geometry: &GeoPolygon,
        start_date: DateTime<Utc>,
        end_date: DateTime<Utc>,
    ) -> DomainResult<Vec<SatelliteImage>>;
    async fn find_unprocessed(&self, limit: i64) -> DomainResult<Vec<SatelliteImage>>;
    async fn create(&self, image: &SatelliteImage) -> DomainResult<SatelliteImage>;
    async fn mark_processed(&self, id: Uuid) -> DomainResult<()>;
    async fn delete(&self, id: Uuid) -> DomainResult<()>;
}

#[async_trait]
pub trait SpectralIndicesRepository: Send + Sync {
    async fn find_by_farm_id(&self, farm_id: Uuid) -> DomainResult<Vec<SpectralIndices>>;
    async fn find_by_farm_and_date_range(
        &self,
        farm_id: Uuid,
        start_date: DateTime<Utc>,
        end_date: DateTime<Utc>,
    ) -> DomainResult<Vec<SpectralIndices>>;
    async fn find_latest_by_farm(&self, farm_id: Uuid) -> DomainResult<Option<SpectralIndices>>;
    async fn create(&self, indices: &SpectralIndices) -> DomainResult<SpectralIndices>;
    async fn batch_create(&self, indices: &[SpectralIndices]) -> DomainResult<Vec<SpectralIndices>>;
}

#[async_trait]
pub trait AlertRepository: Send + Sync {
    async fn find_by_id(&self, id: Uuid) -> DomainResult<Option<Alert>>;
    async fn find_by_farm_id(&self, farm_id: Uuid) -> DomainResult<Vec<Alert>>;
    async fn find_unacknowledged_by_user(&self, user_id: Uuid) -> DomainResult<Vec<Alert>>;
    async fn find_by_type_and_date_range(
        &self,
        alert_type: AlertType,
        start_date: DateTime<Utc>,
        end_date: DateTime<Utc>,
    ) -> DomainResult<Vec<Alert>>;
    async fn create(&self, alert: &Alert) -> DomainResult<Alert>;
    async fn acknowledge(&self, id: Uuid) -> DomainResult<()>;
    async fn delete(&self, id: Uuid) -> DomainResult<()>;
}

#[async_trait]
pub trait SegmentationResultRepository: Send + Sync {
    async fn find_by_image_id(&self, image_id: Uuid) -> DomainResult<Option<SegmentationResult>>;
    async fn create(&self, result: &SegmentationResult) -> DomainResult<SegmentationResult>;
}

#[async_trait]
pub trait TodoRepository: Send + Sync {
    async fn find_by_id(&self, id: Uuid) -> DomainResult<Option<Todo>>;
    async fn find_by_user_id(&self, user_id: Uuid) -> DomainResult<Vec<Todo>>;
    async fn find_pending_by_user(&self, user_id: Uuid) -> DomainResult<Vec<Todo>>;
    async fn create(&self, todo: &Todo) -> DomainResult<Todo>;
    async fn update(&self, todo: &Todo) -> DomainResult<Todo>;
    async fn mark_completed(&self, id: Uuid) -> DomainResult<()>;
    async fn delete(&self, id: Uuid) -> DomainResult<()>;
}

#[async_trait]
pub trait ReportRepository: Send + Sync {
    async fn find_by_id(&self, id: Uuid) -> DomainResult<Option<Report>>;
    async fn find_by_user_id(&self, user_id: Uuid) -> DomainResult<Vec<Report>>;
    async fn find_by_farm_id(&self, farm_id: Uuid) -> DomainResult<Vec<Report>>;
    async fn create(&self, report: &Report) -> DomainResult<Report>;
    async fn delete(&self, id: Uuid) -> DomainResult<()>;
}
