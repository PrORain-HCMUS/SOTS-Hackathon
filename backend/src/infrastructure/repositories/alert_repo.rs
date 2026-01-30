use async_trait::async_trait;
use chrono::{DateTime, Utc};
use sqlx::PgPool;
use uuid::Uuid;

use crate::domain::{
    repositories::AlertRepository, Alert, AlertMetadata, AlertSeverity, AlertType, DomainError,
    DomainResult,
};

pub struct PgAlertRepository {
    pool: PgPool,
}

impl PgAlertRepository {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }
}

#[derive(sqlx::FromRow)]
struct AlertRow {
    id: Uuid,
    farm_id: Uuid,
    alert_type: String,
    severity: String,
    title: String,
    description: String,
    geometry_json: Option<serde_json::Value>,
    detected_at: DateTime<Utc>,
    acknowledged: bool,
    acknowledged_at: Option<DateTime<Utc>>,
    metadata: serde_json::Value,
}

impl From<AlertRow> for Alert {
    fn from(row: AlertRow) -> Self {
        let geometry = row
            .geometry_json
            .and_then(|g| serde_json::from_value(g).ok());

        let metadata: AlertMetadata =
            serde_json::from_value(row.metadata).unwrap_or_default();

        Alert {
            id: row.id,
            farm_id: row.farm_id,
            alert_type: parse_alert_type(&row.alert_type),
            severity: parse_severity(&row.severity),
            title: row.title,
            description: row.description,
            geometry,
            detected_at: row.detected_at,
            acknowledged: row.acknowledged,
            acknowledged_at: row.acknowledged_at,
            metadata,
        }
    }
}

fn parse_alert_type(s: &str) -> AlertType {
    match s {
        "salinity_intrusion" => AlertType::SalinityIntrusion,
        "crop_stress" => AlertType::CropStress,
        "deforestation" => AlertType::Deforestation,
        _ => AlertType::AnomalyDetected,
    }
}

fn alert_type_to_string(t: &AlertType) -> String {
    match t {
        AlertType::SalinityIntrusion => "salinity_intrusion".to_string(),
        AlertType::CropStress => "crop_stress".to_string(),
        AlertType::Deforestation => "deforestation".to_string(),
        AlertType::AnomalyDetected => "anomaly_detected".to_string(),
    }
}

fn parse_severity(s: &str) -> AlertSeverity {
    match s {
        "low" => AlertSeverity::Low,
        "medium" => AlertSeverity::Medium,
        "high" => AlertSeverity::High,
        "critical" => AlertSeverity::Critical,
        _ => AlertSeverity::Medium,
    }
}

fn severity_to_string(s: &AlertSeverity) -> String {
    match s {
        AlertSeverity::Low => "low".to_string(),
        AlertSeverity::Medium => "medium".to_string(),
        AlertSeverity::High => "high".to_string(),
        AlertSeverity::Critical => "critical".to_string(),
    }
}

#[async_trait]
impl AlertRepository for PgAlertRepository {
    async fn find_by_id(&self, id: Uuid) -> DomainResult<Option<Alert>> {
        let row = sqlx::query_as::<_, AlertRow>(
            r#"
            SELECT id, farm_id, alert_type, severity, title, description,
                   ST_AsGeoJSON(geometry)::jsonb as geometry_json,
                   detected_at, acknowledged, acknowledged_at, metadata
            FROM alerts
            WHERE id = $1
            "#,
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(row.map(Alert::from))
    }

    async fn find_by_farm_id(&self, farm_id: Uuid) -> DomainResult<Vec<Alert>> {
        let rows = sqlx::query_as::<_, AlertRow>(
            r#"
            SELECT id, farm_id, alert_type, severity, title, description,
                   ST_AsGeoJSON(geometry)::jsonb as geometry_json,
                   detected_at, acknowledged, acknowledged_at, metadata
            FROM alerts
            WHERE farm_id = $1
            ORDER BY detected_at DESC
            "#,
        )
        .bind(farm_id)
        .fetch_all(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(rows.into_iter().map(Alert::from).collect())
    }

    async fn find_unacknowledged_by_user(&self, user_id: Uuid) -> DomainResult<Vec<Alert>> {
        let rows = sqlx::query_as::<_, AlertRow>(
            r#"
            SELECT a.id, a.farm_id, a.alert_type, a.severity, a.title, a.description,
                   ST_AsGeoJSON(a.geometry)::jsonb as geometry_json,
                   a.detected_at, a.acknowledged, a.acknowledged_at, a.metadata
            FROM alerts a
            INNER JOIN farms f ON a.farm_id = f.id
            WHERE f.user_id = $1 AND a.acknowledged = false
            ORDER BY a.severity DESC, a.detected_at DESC
            "#,
        )
        .bind(user_id)
        .fetch_all(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(rows.into_iter().map(Alert::from).collect())
    }

    async fn find_by_type_and_date_range(
        &self,
        alert_type: AlertType,
        start_date: DateTime<Utc>,
        end_date: DateTime<Utc>,
    ) -> DomainResult<Vec<Alert>> {
        let rows = sqlx::query_as::<_, AlertRow>(
            r#"
            SELECT id, farm_id, alert_type, severity, title, description,
                   ST_AsGeoJSON(geometry)::jsonb as geometry_json,
                   detected_at, acknowledged, acknowledged_at, metadata
            FROM alerts
            WHERE alert_type = $1 AND detected_at BETWEEN $2 AND $3
            ORDER BY detected_at DESC
            "#,
        )
        .bind(alert_type_to_string(&alert_type))
        .bind(start_date)
        .bind(end_date)
        .fetch_all(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(rows.into_iter().map(Alert::from).collect())
    }

    async fn create(&self, alert: &Alert) -> DomainResult<Alert> {
        let geometry_json = alert
            .geometry
            .as_ref()
            .map(|g| serde_json::to_string(g))
            .transpose()
            .map_err(|e| DomainError::geo_processing(e.to_string()))?;

        let metadata_json = serde_json::to_value(&alert.metadata)
            .map_err(|e| DomainError::database(e.to_string()))?;

        let row = sqlx::query_as::<_, AlertRow>(
            r#"
            INSERT INTO alerts (id, farm_id, alert_type, severity, title, description,
                               geometry, detected_at, acknowledged, acknowledged_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, 
                    CASE WHEN $7::text IS NOT NULL THEN ST_GeomFromGeoJSON($7) ELSE NULL END,
                    $8, $9, $10, $11)
            RETURNING id, farm_id, alert_type, severity, title, description,
                      ST_AsGeoJSON(geometry)::jsonb as geometry_json,
                      detected_at, acknowledged, acknowledged_at, metadata
            "#,
        )
        .bind(alert.id)
        .bind(alert.farm_id)
        .bind(alert_type_to_string(&alert.alert_type))
        .bind(severity_to_string(&alert.severity))
        .bind(&alert.title)
        .bind(&alert.description)
        .bind(&geometry_json)
        .bind(alert.detected_at)
        .bind(alert.acknowledged)
        .bind(alert.acknowledged_at)
        .bind(&metadata_json)
        .fetch_one(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(Alert::from(row))
    }

    async fn acknowledge(&self, id: Uuid) -> DomainResult<()> {
        sqlx::query(
            r#"
            UPDATE alerts
            SET acknowledged = true, acknowledged_at = NOW()
            WHERE id = $1
            "#,
        )
        .bind(id)
        .execute(&self.pool)
        .await
        .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(())
    }

    async fn delete(&self, id: Uuid) -> DomainResult<()> {
        sqlx::query("DELETE FROM alerts WHERE id = $1")
            .bind(id)
            .execute(&self.pool)
            .await
            .map_err(|e| DomainError::database(e.to_string()))?;

        Ok(())
    }
}
