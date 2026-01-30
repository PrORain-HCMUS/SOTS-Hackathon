use argon2::{
    password_hash::{rand_core::OsRng, PasswordHash, PasswordHasher, PasswordVerifier, SaltString},
    Argon2,
};
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use crate::shared::error::AppError;
use super::models::Claims;
use std::sync::LazyLock;

static JWT_SECRET: LazyLock<String> = LazyLock::new(|| {
    std::env::var("JWT_SECRET").expect("JWT_SECRET environment variable not set")
});

static JWT_ENCODING_KEY: LazyLock<EncodingKey> = LazyLock::new(|| {
    EncodingKey::from_secret(JWT_SECRET.as_bytes())
});

static JWT_DECODING_KEY: LazyLock<DecodingKey> = LazyLock::new(|| {
    DecodingKey::from_secret(JWT_SECRET.as_bytes())
});

pub fn hash_password(password: &str) -> Result<String, AppError> {
    let salt = SaltString::generate(&mut OsRng);
    let argon2 = Argon2::default();
    
    argon2
        .hash_password(password.as_bytes(), &salt)
        .map(|h| h.to_string())
        .map_err(|e| AppError::Internal(format!("Password hashing failed: {}", e)))
}

pub fn verify_password(password: &str, hash: &str) -> Result<bool, AppError> {
    let parsed_hash = PasswordHash::new(hash)
        .map_err(|e| AppError::Internal(format!("Invalid password hash: {}", e)))?;

    Ok(Argon2::default()
        .verify_password(password.as_bytes(), &parsed_hash)
        .is_ok())
}

pub fn generate_jwt(user_id: i64, email: &str, role: &str) -> Result<String, AppError> {
    let expiration = chrono::Utc::now()
        .checked_add_signed(chrono::Duration::hours(24))
        .ok_or_else(|| AppError::Internal("Failed to calculate expiration".to_string()))?
        .timestamp() as usize;

    let claims = Claims {
        sub: user_id,
        email: email.to_string(),
        role: role.to_string(),
        exp: expiration,
    };

    encode(&Header::default(), &claims, &JWT_ENCODING_KEY)
        .map_err(|e| AppError::Internal(format!("Token generation failed: {}", e)))
}

pub fn validate_jwt(token: &str) -> Result<Claims, AppError> {
    decode::<Claims>(token, &JWT_DECODING_KEY, &Validation::default())
        .map(|data| data.claims)
        .map_err(|e| AppError::Unauthorized(format!("Invalid token: {}", e)))
}