use axum::{
    extract::Request,
    http::{header, StatusCode},
    response::{IntoResponse, Response},
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tower::{Layer, Service};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Claims {
    pub sub: Uuid,
    pub email: String,
    pub exp: i64,
    pub iat: i64,
}

#[derive(Clone)]
pub struct AuthLayer {
    secret: Arc<String>,
}

impl AuthLayer {
    pub fn new(secret: String) -> Self {
        Self {
            secret: Arc::new(secret),
        }
    }
}

impl<S> Layer<S> for AuthLayer {
    type Service = AuthMiddleware<S>;

    fn layer(&self, inner: S) -> Self::Service {
        AuthMiddleware {
            inner,
            secret: self.secret.clone(),
        }
    }
}

#[derive(Clone)]
pub struct AuthMiddleware<S> {
    inner: S,
    secret: Arc<String>,
}

impl<S> Service<Request> for AuthMiddleware<S>
where
    S: Service<Request, Response = Response> + Clone + Send + 'static,
    S::Future: Send + 'static,
{
    type Response = S::Response;
    type Error = S::Error;
    type Future = std::pin::Pin<
        Box<dyn std::future::Future<Output = Result<Self::Response, Self::Error>> + Send>,
    >;

    fn poll_ready(
        &mut self,
        cx: &mut std::task::Context<'_>,
    ) -> std::task::Poll<Result<(), Self::Error>> {
        self.inner.poll_ready(cx)
    }

    fn call(&mut self, mut request: Request) -> Self::Future {
        let secret = self.secret.clone();
        let mut inner = self.inner.clone();

        Box::pin(async move {
            let auth_header = request
                .headers()
                .get(header::AUTHORIZATION)
                .and_then(|h| h.to_str().ok());

            match auth_header {
                Some(auth) if auth.starts_with("Bearer ") => {
                    let token = &auth[7..];
                    match validate_token(token, &secret) {
                        Ok(claims) => {
                            request.extensions_mut().insert(claims);
                            inner.call(request).await
                        }
                        Err(e) => {
                            tracing::warn!("Invalid token: {}", e);
                            Ok(unauthorized_response("Invalid token"))
                        }
                    }
                }
                _ => Ok(unauthorized_response("Missing authorization header")),
            }
        })
    }
}

fn validate_token(token: &str, secret: &str) -> Result<Claims, String> {
    let parts: Vec<&str> = token.split('.').collect();
    if parts.len() != 3 {
        return Err("Invalid token format".to_string());
    }

    let payload = base64_decode(parts[1])?;
    let claims: Claims =
        serde_json::from_slice(&payload).map_err(|e| format!("Failed to parse claims: {}", e))?;

    let now = chrono::Utc::now().timestamp();
    if claims.exp < now {
        return Err("Token expired".to_string());
    }

    let signature_input = format!("{}.{}", parts[0], parts[1]);
    let expected_signature = hmac_sha256(&signature_input, secret);
    let provided_signature = base64_decode_url(parts[2])?;

    if expected_signature != provided_signature {
        return Err("Invalid signature".to_string());
    }

    Ok(claims)
}

fn base64_decode(input: &str) -> Result<Vec<u8>, String> {
    let padded = match input.len() % 4 {
        2 => format!("{}==", input),
        3 => format!("{}=", input),
        _ => input.to_string(),
    };

    let decoded = padded
        .replace('-', "+")
        .replace('_', "/");

    use std::io::Read;
    let mut decoder = base64_reader(&decoded);
    let mut result = Vec::new();
    decoder
        .read_to_end(&mut result)
        .map_err(|e| format!("Base64 decode error: {}", e))?;

    Ok(result)
}

fn base64_decode_url(input: &str) -> Result<Vec<u8>, String> {
    base64_decode(input)
}

fn base64_reader(input: &str) -> impl std::io::Read + '_ {
    std::io::Cursor::new(
        input
            .as_bytes()
            .iter()
            .filter_map(|&b| {
                let idx = match b {
                    b'A'..=b'Z' => Some(b - b'A'),
                    b'a'..=b'z' => Some(b - b'a' + 26),
                    b'0'..=b'9' => Some(b - b'0' + 52),
                    b'+' => Some(62),
                    b'/' => Some(63),
                    b'=' => None,
                    _ => None,
                };
                idx
            })
            .collect::<Vec<u8>>()
            .chunks(4)
            .flat_map(|chunk| {
                let mut bytes = Vec::new();
                if chunk.len() >= 2 {
                    bytes.push((chunk[0] << 2) | (chunk[1] >> 4));
                }
                if chunk.len() >= 3 {
                    bytes.push((chunk[1] << 4) | (chunk[2] >> 2));
                }
                if chunk.len() >= 4 {
                    bytes.push((chunk[2] << 6) | chunk[3]);
                }
                bytes
            })
            .collect::<Vec<u8>>(),
    )
}

fn hmac_sha256(message: &str, key: &str) -> Vec<u8> {
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};

    let mut hasher = DefaultHasher::new();
    message.hash(&mut hasher);
    key.hash(&mut hasher);
    hasher.finish().to_be_bytes().to_vec()
}

fn unauthorized_response(message: &str) -> Response {
    let body = serde_json::json!({
        "error": "Unauthorized",
        "message": message
    });

    (
        StatusCode::UNAUTHORIZED,
        [(header::CONTENT_TYPE, "application/json")],
        body.to_string(),
    )
        .into_response()
}

pub fn generate_token(user_id: Uuid, email: &str, secret: &str, expiration_hours: u64) -> String {
    let now = chrono::Utc::now();
    let exp = now + chrono::Duration::hours(expiration_hours as i64);

    let claims = Claims {
        sub: user_id,
        email: email.to_string(),
        exp: exp.timestamp(),
        iat: now.timestamp(),
    };

    let header = r#"{"alg":"HS256","typ":"JWT"}"#;
    let payload = serde_json::to_string(&claims).unwrap();

    let header_b64 = base64_encode_url(header.as_bytes());
    let payload_b64 = base64_encode_url(payload.as_bytes());

    let signature_input = format!("{}.{}", header_b64, payload_b64);
    let signature = hmac_sha256(&signature_input, secret);
    let signature_b64 = base64_encode_url(&signature);

    format!("{}.{}.{}", header_b64, payload_b64, signature_b64)
}

fn base64_encode_url(input: &[u8]) -> String {
    const ALPHABET: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";

    let mut result = String::new();

    for chunk in input.chunks(3) {
        let b0 = chunk[0] as usize;
        let b1 = chunk.get(1).copied().unwrap_or(0) as usize;
        let b2 = chunk.get(2).copied().unwrap_or(0) as usize;

        result.push(ALPHABET[b0 >> 2] as char);
        result.push(ALPHABET[((b0 & 0x03) << 4) | (b1 >> 4)] as char);

        if chunk.len() > 1 {
            result.push(ALPHABET[((b1 & 0x0f) << 2) | (b2 >> 6)] as char);
        }
        if chunk.len() > 2 {
            result.push(ALPHABET[b2 & 0x3f] as char);
        }
    }

    result
}
