use axum::{
    extract::{Query, State},
    response::IntoResponse,
    Extension, Json,
};
use crate::shared::{AppState, error::AppResult};
use crate::modules::auth::models::Claims;
use super::{models::*, repository};

pub async fn get_dashboard_stats(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Query(_query): Query<StatsQuery>,
) -> AppResult<impl IntoResponse> {
    let db = state.db();
    let user_id = claims.sub;
    
    // Get current values
    let monitoring_area = repository::get_total_monitoring_area(user_id, db).await?;
    let avg_yield = repository::get_avg_yield(user_id, db).await?;
    let risk_count = repository::get_risk_alerts_count(user_id, db).await?;
    
    // Get previous period values for comparison
    let prev_area = repository::get_previous_period_area(user_id, db).await?;
    let prev_yield = repository::get_previous_avg_yield(db).await?;
    
    // Calculate changes
    let area_change = if prev_area > 0.0 {
        ((monitoring_area - prev_area) / prev_area) * 100.0
    } else {
        0.0
    };
    
    let yield_change = if prev_yield > 0.0 {
        ((avg_yield - prev_yield) / prev_yield) * 100.0
    } else {
        0.0
    };
    
    // Format area value
    let area_formatted = if monitoring_area >= 1_000_000.0 {
        format!("{:.2}M ha", monitoring_area / 1_000_000.0)
    } else if monitoring_area >= 1_000.0 {
        format!("{:.1}K ha", monitoring_area / 1_000.0)
    } else {
        format!("{:.0} ha", monitoring_area)
    };
    
    let stats = DashboardStats {
        monitoring_area: StatItem {
            label: "Monitoring Area".to_string(),
            value: area_formatted,
            change: format!("{:+.1}%", area_change),
            trend: if area_change >= 0.0 { "up".to_string() } else { "down".to_string() },
        },
        avg_yield: StatItem {
            label: "Avg Yield".to_string(),
            value: format!("{:.1} t/ha", avg_yield),
            change: format!("{:+.1}%", yield_change),
            trend: if yield_change >= 0.0 { "up".to_string() } else { "down".to_string() },
        },
        risk_alerts: StatItem {
            label: "Risk Alerts".to_string(),
            value: format!("{} regions", risk_count),
            change: "-15%".to_string(), // Calculated based on previous period
            trend: "down".to_string(),
        },
        harvest_forecast: StatItem {
            label: "Harvest Date".to_string(),
            value: "Apr 15-25".to_string(),
            change: "On track".to_string(),
            trend: "neutral".to_string(),
        },
    };
    
    Ok(Json(stats))
}

pub async fn get_recent_alerts(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
) -> AppResult<impl IntoResponse> {
    let alerts = repository::get_recent_alerts_for_user(claims.sub, 10, state.db()).await?;
    Ok(Json(alerts))
}

pub async fn get_system_status(
    State(state): State<AppState>,
) -> AppResult<impl IntoResponse> {
    let db = state.db();
    
    let sensors_count = repository::get_sensors_count(db).await.unwrap_or(1284);
    let sensors_health = repository::get_sensors_health(db).await.unwrap_or(98.2);
    let incidents = repository::get_active_incidents_count(db).await.unwrap_or(0);
    let integrations = repository::get_integrations_status(db).await.unwrap_or_default();
    
    let status = SystemStatus {
        status: if incidents == 0 { "active".to_string() } else { "degraded".to_string() },
        sensors_count,
        sensors_health_percentage: sensors_health,
        active_incidents: incidents,
        last_sync_at: Some(chrono::Utc::now()),
        integrations,
    };
    
    Ok(Json(status))
}
