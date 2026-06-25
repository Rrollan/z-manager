// Common Handlers for Z Code / Z.ai
use crate::proxy::server::AppState;
use axum::{
    extract::State,
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde_json::{json, Value};
use tokio::time::Duration;

#[derive(Debug, Clone)]
pub enum RetryStrategy {
    NoRetry,
    FixedDelay(Duration),
}

pub fn determine_retry_strategy(
    status_code: u16,
    _error_text: &str,
) -> RetryStrategy {
    match status_code {
        429 => RetryStrategy::FixedDelay(Duration::from_secs(2)),
        _ => RetryStrategy::NoRetry,
    }
}

pub fn should_rotate_account(strategy: &RetryStrategy) -> bool {
    matches!(strategy, RetryStrategy::FixedDelay(_))
}

pub async fn handle_detect_model(
    State(_state): State<AppState>,
    Json(body): Json<Value>,
) -> Response {
    let model_name = body.get("model").and_then(|v| v.as_str()).unwrap_or("");

    if model_name.is_empty() {
        return (StatusCode::BAD_REQUEST, "Missing 'model' field").into_response();
    }

    let response = json!({
        "model": model_name,
        "mapped_model": "glm-5.2",
        "type": "text",
        "features": {
            "has_web_search": true,
            "is_image_gen": false
        }
    });

    Json(response).into_response()
}
