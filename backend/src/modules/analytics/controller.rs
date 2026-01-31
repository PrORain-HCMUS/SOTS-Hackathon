use axum::{
    extract::{Query, State},
    response::IntoResponse,
    Json,
};
use crate::shared::{AppState, error::AppResult};
use super::{models::*, repository};

pub async fn get_kpis(
    State(state): State<AppState>,
    Query(query): Query<AnalyticsQuery>,
) -> AppResult<impl IntoResponse> {
    let time_range = query.time_range.as_deref().unwrap_or("7d");
    let db = state.db();
    
    let (total_yield, yield_trend) = repository::get_total_yield(time_range, db).await?;
    let (efficiency, efficiency_trend) = repository::get_efficiency_rate(time_range, db).await?;
    let (water_usage, water_trend) = repository::get_water_usage(time_range, db).await?;
    let (cost, cost_trend) = repository::get_cost_per_hectare(time_range, db).await?;
    
    // Format water usage
    let water_formatted = if water_usage >= 1_000_000.0 {
        format!("{:.1}M", water_usage / 1_000_000.0)
    } else if water_usage >= 1_000.0 {
        format!("{:.0}K", water_usage / 1_000.0)
    } else {
        format!("{:.0}", water_usage)
    };
    
    let kpis = AnalyticsKPIs {
        total_yield: KPIItem {
            title: "Total Yield".to_string(),
            value: format!("{:.0}", total_yield),
            unit: "tons".to_string(),
            trend: format!("{:.1}%", yield_trend.abs()),
            trend_up: yield_trend >= 0.0,
            color: "blue".to_string(),
        },
        efficiency_rate: KPIItem {
            title: "Efficiency Rate".to_string(),
            value: format!("{:.1}", efficiency),
            unit: "%".to_string(),
            trend: format!("{:.1}%", efficiency_trend.abs()),
            trend_up: efficiency_trend >= 0.0,
            color: "green".to_string(),
        },
        water_usage: KPIItem {
            title: "Water Usage".to_string(),
            value: water_formatted,
            unit: "L".to_string(),
            trend: format!("{:.1}%", water_trend.abs()),
            trend_up: water_trend >= 0.0, // For water, down is good but we show the actual trend
            color: "amber".to_string(),
        },
        cost_per_hectare: KPIItem {
            title: "Cost per Hectare".to_string(),
            value: format!("${:.0}", cost),
            unit: "".to_string(),
            trend: format!("{:.1}%", cost_trend.abs()),
            trend_up: cost_trend >= 0.0,
            color: "purple".to_string(),
        },
    };
    
    Ok(Json(kpis))
}

pub async fn get_regional_metrics(
    State(state): State<AppState>,
) -> AppResult<impl IntoResponse> {
    let metrics = repository::get_regional_metrics(state.db()).await?;
    Ok(Json(metrics))
}

pub async fn get_yield_trends(
    State(state): State<AppState>,
    Query(query): Query<AnalyticsQuery>,
) -> AppResult<impl IntoResponse> {
    let time_range = query.time_range.as_deref().unwrap_or("7d");
    let region = query.region.as_deref();
    
    let data = repository::get_yield_trends(time_range, region, state.db()).await?;
    
    let values: Vec<f64> = data.iter().map(|p| p.value).collect();
    let avg = if !values.is_empty() {
        values.iter().sum::<f64>() / values.len() as f64
    } else {
        0.0
    };
    let min = values.iter().cloned().fold(f64::INFINITY, f64::min);
    let max = values.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    
    let response = YieldTrendsResponse {
        data,
        period: time_range.to_string(),
        avg,
        min: if min.is_finite() { min } else { 0.0 },
        max: if max.is_finite() { max } else { 0.0 },
    };
    
    Ok(Json(response))
}

pub async fn get_regional_performance(
    State(state): State<AppState>,
) -> AppResult<impl IntoResponse> {
    let performance = repository::get_regional_performance(state.db()).await?;
    Ok(Json(performance))
}
