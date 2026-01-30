pub mod auth;
pub mod farm_mgmt;
pub mod monitoring;

use crate::shared::AppState;
use axum::Router;

pub fn auth_router() -> Router<AppState> {
    auth::router()
}

pub fn farm_mgmt_router() -> Router<AppState> {
    farm_mgmt::router()
}

pub fn monitoring_router() -> Router<AppState> {
    monitoring::router()
}