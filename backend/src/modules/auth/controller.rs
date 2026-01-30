use axum::{extract::{State, Extension}, Json};
use crate::shared::{AppState, error::AppError};
use super::{
    models::{LoginRequest, LoginResponse, RegisterRequest, UserProfile, Claims},
    repository, service,
};

pub async fn register(
    State(state): State<AppState>,
    Json(payload): Json<RegisterRequest>,
) -> Result<Json<LoginResponse>, AppError> {
    if payload.email.is_empty() || payload.password.is_empty() {
        return Err(AppError::BadRequest("Email and password are required".to_string()));
    }

    if payload.password.len() < 8 {
        return Err(AppError::BadRequest("Password must be at least 8 characters".to_string()));
    }

    if repository::find_by_email(&state.db, &payload.email).await?.is_some() {
        return Err(AppError::BadRequest("Email already registered".to_string()));
    }

    let password_hash = service::hash_password(&payload.password)?;
    let user = repository::create_user(&state.db, &payload.email, &password_hash, &payload.role).await?;

    let token = service::generate_jwt(user.id, &user.email, &user.role)?;

    Ok(Json(LoginResponse {
        token,
        user_id: user.id,
        email: user.email,
        role: user.role,
    }))
}

pub async fn login(
    State(state): State<AppState>,
    Json(payload): Json<LoginRequest>,
) -> Result<Json<LoginResponse>, AppError> {
    let user = repository::find_by_email(&state.db, &payload.email)
        .await?
        .ok_or_else(|| AppError::Unauthorized("Invalid credentials".to_string()))?;

    if !service::verify_password(&payload.password, &user.password_hash)? {
        return Err(AppError::Unauthorized("Invalid credentials".to_string()));
    }

    let token = service::generate_jwt(user.id, &user.email, &user.role)?;

    Ok(Json(LoginResponse {
        token,
        user_id: user.id,
        email: user.email,
        role: user.role,
    }))
}

pub async fn get_profile(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
) -> Result<Json<UserProfile>, AppError> {
    let user = repository::find_by_id(&state.db, claims.sub)
        .await?
        .ok_or_else(|| AppError::NotFound("User not found".to_string()))?;

    Ok(Json(UserProfile {
        id: user.id,
        email: user.email,
        role: user.role,
        created_at: user.created_at,
    }))
}