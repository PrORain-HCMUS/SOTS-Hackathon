use axum::{
    extract::{Request, State},
    http::{header::AUTHORIZATION},
    middleware::Next,
    response::Response,
};
use crate::shared::{AppState, error::AppError};
use super::service;

pub async fn auth_middleware(
    State(_state): State<AppState>,
    mut req: Request,
    next: Next,
) -> Result<Response, AppError> {
    let auth_header = req
        .headers()
        .get(AUTHORIZATION)
        .and_then(|h| h.to_str().ok())
        .ok_or_else(|| AppError::Unauthorized("Missing authorization header".to_string()))?;

    let token = auth_header
        .strip_prefix("Bearer ")
        .ok_or_else(|| AppError::Unauthorized("Invalid authorization format".to_string()))?;

    let claims = service::validate_jwt(token)?;
    
    req.extensions_mut().insert(claims);
    
    Ok(next.run(req).await)
}