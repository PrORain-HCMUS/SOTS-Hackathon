pub mod auth;
pub mod farm_mgmt;
pub mod monitoring;
pub mod dashboard;
pub mod analytics;
pub mod reports;
pub mod settings;
pub mod satellites;

use crate::shared::AppState;
use axum::Router;

pub fn auth_router() -> Router<AppState> {
    auth::router()
}

pub fn auth_protected_router() -> Router<AppState> {
    auth::protected_router()
}

pub fn farm_mgmt_router() -> Router<AppState> {
    farm_mgmt::router()
}

pub fn monitoring_router() -> Router<AppState> {
    monitoring::router()
}

pub fn dashboard_router() -> Router<AppState> {
    dashboard::router()
}

pub fn analytics_router() -> Router<AppState> {
    analytics::router()
}

pub fn reports_router() -> Router<AppState> {
    reports::router()
}

pub fn settings_router() -> Router<AppState> {
    settings::router()
}

pub fn satellites_router() -> Router<AppState> {
    satellites::router()
}