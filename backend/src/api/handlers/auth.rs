use axum::{extract::State, http::StatusCode, Json};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use uuid::Uuid;
use validator::Validate;

use crate::api::handlers::ApiResponse;
use crate::api::middleware::auth::generate_token;
use crate::api::routes::AppState;

#[derive(Debug, Deserialize, Validate)]
pub struct LoginRequest {
    #[validate(email(message = "Invalid email format"))]
    pub email: String,
    #[validate(length(min = 6, message = "Password must be at least 6 characters"))]
    pub password: String,
}

#[derive(Debug, Deserialize, Validate)]
pub struct RegisterRequest {
    #[validate(email(message = "Invalid email format"))]
    pub email: String,
    #[validate(length(min = 2, message = "Name must be at least 2 characters"))]
    pub name: String,
    #[validate(length(min = 6, message = "Password must be at least 6 characters"))]
    pub password: String,
}

#[derive(Debug, Serialize)]
pub struct AuthResponse {
    pub token: String,
    pub user: UserResponse,
}

#[derive(Debug, Serialize)]
pub struct UserResponse {
    pub id: Uuid,
    pub email: String,
    pub name: String,
}

pub async fn login(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<LoginRequest>,
) -> Result<Json<ApiResponse<AuthResponse>>, (StatusCode, Json<ApiResponse<()>>)> {
    if let Err(errors) = payload.validate() {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(ApiResponse::error(format!("Validation failed: {}", errors))),
        ));
    }

    let user_id = Uuid::new_v4();
    let token = generate_token(
        user_id,
        &payload.email,
        &state.config.jwt.secret,
        state.config.jwt.expiration_hours,
    );

    Ok(Json(ApiResponse::success(AuthResponse {
        token,
        user: UserResponse {
            id: user_id,
            email: payload.email,
            name: "User".to_string(),
        },
    })))
}

pub async fn register(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<RegisterRequest>,
) -> Result<Json<ApiResponse<AuthResponse>>, (StatusCode, Json<ApiResponse<()>>)> {
    if let Err(errors) = payload.validate() {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(ApiResponse::error(format!("Validation failed: {}", errors))),
        ));
    }

    let user_id = Uuid::new_v4();
    let token = generate_token(
        user_id,
        &payload.email,
        &state.config.jwt.secret,
        state.config.jwt.expiration_hours,
    );

    tracing::info!("New user registered: {}", payload.email);

    Ok(Json(ApiResponse::success(AuthResponse {
        token,
        user: UserResponse {
            id: user_id,
            email: payload.email,
            name: payload.name,
        },
    })))
}
