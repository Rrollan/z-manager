// Anthropic/Claude Handler for Z Code / Z.ai
use axum::{
    extract::Json, extract::State, http::StatusCode, response::IntoResponse, response::Response,
};
use serde_json::{json, Value};
use tracing::info;
use crate::proxy::server::AppState;
use axum::http::HeaderMap;

pub async fn handle_messages(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(mut body): Json<Value>,
) -> Response {
    let trace_id = format!("req_{}", chrono::Utc::now().timestamp_subsec_millis());
    let original_model = body.get("model").and_then(|v| v.as_str()).unwrap_or("glm-5.2").to_string();
    
    // Acquire active Z.ai account/API Key
    let mapped_model = "glm-5.2";
    let (access_token, _project_id, email, _account_id, _wait_ms) = match state.token_manager
        .get_token("claude", false, None, mapped_model)
        .await
    {
        Ok(t) => t,
        Err(e) => {
            return (
                StatusCode::SERVICE_UNAVAILABLE,
                Json(json!({
                    "error": {
                        "message": format!("Token acquisition failed: {}", e),
                        "type": "server_error"
                    }
                }))
            ).into_response();
        }
    };

    info!(
        "[{}] Z.ai Anthropic Request: {} | Using account: {}",
        trace_id,
        original_model,
        email
    );

    // If target model is not already a GLM model, map it to glm-5.2
    if !original_model.to_lowercase().contains("glm-") {
        body["model"] = Value::String(mapped_model.to_string());
    }

    // Forward request to Z.ai Anthropic endpoint
    let url = "https://api.z.ai/api/anthropic/v1/messages";

    crate::proxy::providers::zai::forward_request_to_zai(&state, axum::http::Method::POST, url, &headers, body, &access_token).await
}

pub async fn handle_count_tokens(
    State(_state): State<AppState>,
    Json(_body): Json<Value>,
) -> impl IntoResponse {
    // Return a dummy token count
    (
        StatusCode::OK,
        Json(json!({
            "input_tokens": 100
        }))
    )
}

pub async fn handle_list_models(State(_state): State<AppState>) -> impl IntoResponse {
    (
        StatusCode::OK,
        Json(json!({
            "models": [
                {
                    "id": "glm-5.2",
                    "display_name": "GLM-5.2"
                }
            ]
        }))
    )
}
