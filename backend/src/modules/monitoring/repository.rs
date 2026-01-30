use sqlx::{PgPool, Row};
use bigdecimal::{BigDecimal, ToPrimitive};
use std::convert::TryFrom;
use crate::shared::error::{AppResult, AppError};
use super::models::{Alert, SalinityLog, IntrusionVector, CreateAlert, CreateSalinityLog, CreateIntrusionVector, AlertSeverity};

pub async fn save_alert(alert: CreateAlert, db: &PgPool) -> AppResult<i64> {
    let record = sqlx::query_scalar(
        r#"
        INSERT INTO alerts (farm_id, severity, message, metadata, detected_at)
        VALUES ($1, $2, $3, $4, NOW())
        RETURNING id
        "#
    )
    .bind(alert.farm_id)
    .bind(alert.severity.as_str())
    .bind(alert.message)
    .bind(alert.metadata)
    .fetch_one(db)
    .await?;

    Ok(record)
}

pub async fn save_salinity_log(log: CreateSalinityLog, db: &PgPool) -> AppResult<i64> {
    // FIX: Use try_from instead of from for f64 conversion
    let ndsi = BigDecimal::try_from(log.ndsi_value)
        .map_err(|e| AppError::BadRequest(format!("Invalid NDSI value: {}", e)))?;

    let record = sqlx::query_scalar(
        r#"
        INSERT INTO salinity_logs (farm_id, ndsi_value, source, recorded_at)
        VALUES ($1, $2, $3, NOW())
        RETURNING id
        "#
    )
    .bind(log.farm_id)
    .bind(ndsi) 
    .bind(log.source)
    .fetch_one(db)
    .await?;

    Ok(record)
}

pub async fn save_intrusion_vector(vector: CreateIntrusionVector, db: &PgPool) -> AppResult<i64> {
    // FIX: Use try_from for f64 conversions
    let angle = BigDecimal::try_from(vector.angle_degrees)
        .map_err(|e| AppError::BadRequest(format!("Invalid angle: {}", e)))?;
    
    let magnitude = BigDecimal::try_from(vector.magnitude_km)
        .map_err(|e| AppError::BadRequest(format!("Invalid magnitude: {}", e)))?;

    let record = sqlx::query_scalar(
        r#"
        INSERT INTO intrusion_vectors (farm_id, direction, angle_degrees, magnitude_km, calculated_at)
        VALUES ($1, $2, $3, $4, NOW())
        RETURNING id
        "#
    )
    .bind(vector.farm_id)
    .bind(vector.direction)
    .bind(angle)
    .bind(magnitude)
    .fetch_one(db)
    .await?;

    Ok(record)
}

pub async fn get_ndsi_history(farm_id: i64, days: i32, db: &PgPool) -> AppResult<Vec<SalinityLog>> {
    let rows = sqlx::query(
        r#"
        SELECT id, farm_id, ndsi_value, source, recorded_at
        FROM salinity_logs
        WHERE farm_id = $1 AND recorded_at >= NOW() - INTERVAL '1 day' * $2
        ORDER BY recorded_at DESC
        "#,
    )
    .bind(farm_id)
    .bind(days as f64)
    .fetch_all(db)
    .await?;

    Ok(rows
        .into_iter()
        .filter_map(|row| {
            let ndsi: BigDecimal = row.get("ndsi_value");
            ndsi.to_f64().map(|val| SalinityLog {
                id: row.get("id"),
                farm_id: row.get("farm_id"),
                ndsi_value: val,
                source: row.get("source"),
                recorded_at: row.get("recorded_at"),
            })
        })
        .collect())
}

pub async fn get_recent_alerts(farm_id: i64, limit: i64, db: &PgPool) -> AppResult<Vec<Alert>> {
    let rows = sqlx::query(
        r#"
        SELECT id, farm_id, severity, message, metadata, detected_at, acknowledged, acknowledged_at
        FROM alerts
        WHERE farm_id = $1
        ORDER BY detected_at DESC
        LIMIT $2
        "#,
    )
    .bind(farm_id)
    .bind(limit)
    .fetch_all(db)
    .await?;

    Ok(rows
        .into_iter()
        .map(|row| {
            let severity_str: String = row.get("severity");
            Alert {
                id: row.get("id"),
                farm_id: row.get("farm_id"),
                severity: match severity_str.as_str() {
                    "critical" => AlertSeverity::Critical,
                    "high" => AlertSeverity::High,
                    "medium" => AlertSeverity::Medium,
                    _ => AlertSeverity::Low,
                },
                message: row.get("message"),
                metadata: row.get("metadata"),
                detected_at: row.get("detected_at"),
                acknowledged: row.get("acknowledged"),
                acknowledged_at: row.get("acknowledged_at"),
            }
        })
        .collect())
}

pub async fn get_latest_intrusion_vector(farm_id: i64, db: &PgPool) -> AppResult<Option<IntrusionVector>> {
    let row = sqlx::query(
        r#"
        SELECT id, farm_id, direction, angle_degrees, magnitude_km, calculated_at
        FROM intrusion_vectors
        WHERE farm_id = $1
        ORDER BY calculated_at DESC
        LIMIT 1
        "#,
    )
    .bind(farm_id)
    .fetch_optional(db)
    .await?;

    Ok(row.and_then(|row| {
        let angle_bd: BigDecimal = row.get("angle_degrees");
        let mag_bd: BigDecimal = row.get("magnitude_km");
        let angle = angle_bd.to_f64()?;
        let magnitude = mag_bd.to_f64()?;
        
        Some(IntrusionVector {
            id: row.get("id"),
            farm_id: row.get("farm_id"),
            direction: row.get("direction"),
            angle_degrees: angle,
            magnitude_km: magnitude,
            calculated_at: row.get("calculated_at"),
        })
    }))
}

pub async fn get_latest_ndsi(farm_id: i64, db: &PgPool) -> AppResult<Option<f64>> {
    let record = sqlx::query_scalar::<_, BigDecimal>(
        "SELECT ndsi_value FROM salinity_logs WHERE farm_id = $1 ORDER BY recorded_at DESC LIMIT 1"
    )
    .bind(farm_id)
    .fetch_optional(db)
    .await?;

    Ok(record.and_then(|bd| bd.to_f64()))
}