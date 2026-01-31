use serde::{Deserialize, Serialize};
use chrono::NaiveDate;

#[derive(Debug, Serialize, Deserialize)]
pub struct AnalyticsKPIs {
    pub total_yield: KPIItem,
    pub efficiency_rate: KPIItem,
    pub water_usage: KPIItem,
    pub cost_per_hectare: KPIItem,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct KPIItem {
    pub title: String,
    pub value: String,
    pub unit: String,
    pub trend: String,
    pub trend_up: bool,
    pub color: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RegionalMetric {
    pub region: String,
    pub region_code: String,
    pub area: String,
    pub yield_per_hectare: String,
    pub efficiency: String,
    pub status: String,
    pub status_color: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct YieldTrendPoint {
    pub date: NaiveDate,
    pub value: f64,
    pub region: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct YieldTrendsResponse {
    pub data: Vec<YieldTrendPoint>,
    pub period: String,
    pub avg: f64,
    pub min: f64,
    pub max: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RegionalPerformance {
    pub region: String,
    pub region_code: String,
    pub score: f64,
    pub metrics: PerformanceMetrics,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PerformanceMetrics {
    pub yield_index: f64,
    pub efficiency_index: f64,
    pub sustainability_index: f64,
    pub risk_index: f64,
}

#[derive(Debug, Deserialize)]
pub struct AnalyticsQuery {
    pub time_range: Option<String>, // "24h", "7d", "30d", "90d"
    pub region: Option<String>,
}
