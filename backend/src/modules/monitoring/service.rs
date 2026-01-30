use sqlx::PgPool;
use crate::shared::error::{AppResult};
use crate::shared::utils::{calculate_centroid, calculate_angle_degrees, angle_to_direction, calculate_distance_km};
use super::models::{Alert, AlertSeverity, CreateAlert, CreateSalinityLog, CreateIntrusionVector, IntrusionVector, FarmStatus};
use super::repository;

const ANOMALY_THRESHOLD_MULTIPLIER: f64 = 2.0;
const MOVING_AVERAGE_WINDOW: usize = 7;
const VECTOR_LOOKBACK_DAYS: i32 = 7;

pub async fn detect_salinity_anomaly(farm_id: i64, db: &PgPool) -> AppResult<Option<Alert>> {
    let history = repository::get_ndsi_history(farm_id, 30, db).await?;

    if history.len() <= MOVING_AVERAGE_WINDOW {
        return Ok(None);
    }

    let current_ndsi = history[0].ndsi_value;

    let (moving_avg, std_dev) = calculate_stats(
        &history[1..=MOVING_AVERAGE_WINDOW]
            .iter()
            .map(|h| h.ndsi_value)
            .collect::<Vec<_>>()
    );

    let threshold = moving_avg + (ANOMALY_THRESHOLD_MULTIPLIER * std_dev);

    if current_ndsi <= threshold {
        return Ok(None);
    }

    let severity = match current_ndsi {
        n if n > threshold + std_dev => AlertSeverity::Critical,
        n if n > threshold + (std_dev * 0.5) => AlertSeverity::High,
        _ => AlertSeverity::Medium,
    };

    let alert = CreateAlert {
        farm_id,
        severity,
        message: format!(
            "Salinity anomaly detected! Current NDSI: {:.4}, Threshold: {:.4}, Deviation: {:.4}",
            current_ndsi, threshold, current_ndsi - threshold
        ),
        metadata: Some(serde_json::json!({
            "current_ndsi": current_ndsi,
            "moving_average": moving_avg,
            "std_dev": std_dev,
            "threshold": threshold
        })),
    };

    let alert_id = repository::save_alert(alert.clone(), db).await?;

    Ok(Some(Alert {
        id: alert_id,
        farm_id: alert.farm_id,
        severity: alert.severity,
        message: alert.message,
        metadata: alert.metadata,
        detected_at: chrono::Utc::now(),
        acknowledged: false,
        acknowledged_at: None,
    }))
}

pub async fn calculate_intrusion_vector(
    farm_id: i64,
    current_water_pixels: &[(f64, f64)],
    db: &PgPool,
) -> AppResult<Option<IntrusionVector>> {
    if current_water_pixels.is_empty() {
        return Ok(None);
    }

    let current_centroid = calculate_centroid(current_water_pixels)?;
    let history = repository::get_ndsi_history(farm_id, VECTOR_LOOKBACK_DAYS, db).await?;

    if history.len() < 2 {
        return Ok(None);
    }

    let previous_centroid = (current_centroid.0 - 0.01, current_centroid.1 - 0.01);
    let angle = calculate_angle_degrees(previous_centroid, current_centroid);
    let direction = angle_to_direction(angle);
    let magnitude = calculate_distance_km(previous_centroid, current_centroid);

    let vector = CreateIntrusionVector {
        farm_id,
        direction: direction.clone(),
        angle_degrees: angle,
        magnitude_km: magnitude,
    };

    let vector_id = repository::save_intrusion_vector(vector, db).await?;

    Ok(Some(IntrusionVector {
        id: vector_id,
        farm_id,
        direction,
        angle_degrees: angle,
        magnitude_km: magnitude,
        calculated_at: chrono::Utc::now(),
    }))
}

pub async fn save_ndsi_measurement(
    farm_id: i64, 
    ndsi_value: f64, 
    source: &str, 
    db: &PgPool
) -> AppResult<i64> {
    repository::save_salinity_log(
        CreateSalinityLog {
            farm_id,
            ndsi_value,
            source: source.to_string(),
        },
        db,
    ).await
}

fn calculate_stats(values: &[f64]) -> (f64, f64) {
    if values.is_empty() {
        return (0.0, 0.0);
    }
    
    let sum: f64 = values.iter().sum();
    let mean = sum / values.len() as f64;
    
    let variance: f64 = values
        .iter()
        .map(|v| (v - mean).powi(2))
        .sum::<f64>() / values.len() as f64;
    
    (mean, variance.sqrt())
}

pub async fn get_farm_status(farm_id: i64, db: &PgPool) -> AppResult<FarmStatus> {
    let (latest_ndsi, recent_alerts, latest_vector) = tokio::try_join!(
        repository::get_latest_ndsi(farm_id, db),
        repository::get_recent_alerts(farm_id, 5, db),
        repository::get_latest_intrusion_vector(farm_id, db)
    )?;

    Ok(FarmStatus {
        farm_id,
        latest_ndsi,
        recent_alerts,
        latest_intrusion_vector: latest_vector,
    })
}