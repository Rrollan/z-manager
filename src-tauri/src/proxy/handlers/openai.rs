// OpenAI Handler for Z Code / Z.ai
use axum::{
    extract::Json, extract::State, http::StatusCode, response::IntoResponse, response::Response,
};
use serde_json::{json, Value};
use tracing::{debug, info};
use crate::proxy::server::AppState;
use axum::http::HeaderMap;

pub async fn handle_chat_completions(
    State(state): State<AppState>,
    headers: HeaderMap,
    Json(mut body): Json<Value>,
) -> Response {
    let trace_id = format!("req_{}", chrono::Utc::now().timestamp_subsec_millis());
    let original_model = body.get("model").and_then(|v| v.as_str()).unwrap_or("glm-5.2").to_string();
    
    // Acquire active Z.ai account/API Key
    let mapped_model = "glm-5.2";
    let (access_token, _project_id, email, _account_id, _wait_ms) = match state.token_manager
        .get_token("openai", false, None, mapped_model)
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
        "[{}] Z.ai Chat Request: {} | Using account: {}",
        trace_id,
        original_model,
        email
    );

    // If target model is not already a GLM model, map it to glm-5.2
    if !original_model.to_lowercase().contains("glm-") {
        body["model"] = Value::String(mapped_model.to_string());
    }

    // Forward request to Z.ai
    let zai_base_url = "https://api.z.ai/api/coding/paas/v4";
    let url = format!("{}/chat/completions", zai_base_url);

    crate::proxy::providers::zai::forward_request_to_zai(&state, axum::http::Method::POST, &url, &headers, body, &access_token).await
}

pub async fn handle_completions(
    state: State<AppState>,
    headers: HeaderMap,
    Json(mut body): Json<Value>,
) -> Response {
    // Basic delegation to handle_chat_completions if messages exist
    if body.get("messages").is_some() {
        return handle_chat_completions(state, headers, Json(body)).await;
    }

    // Convert prompt to messages
    let prompt = body.get("prompt").and_then(|v| v.as_str()).unwrap_or("");
    body["messages"] = json!([
        { "role": "user", "content": prompt }
    ]);
    body.as_object_mut().map(|m| m.remove("prompt"));

    handle_chat_completions(state, headers, Json(body)).await
}

pub async fn handle_list_models(State(_state): State<AppState>) -> impl IntoResponse {
    (
        StatusCode::OK,
        Json(json!({
            "object": "list",
            "data": [
                {
                    "id": "glm-5.2",
                    "object": "model",
                    "created": 1719234000,
                    "owned_by": "z.ai"
                },
                {
                    "id": "glm-5.1",
                    "object": "model",
                    "created": 1719234000,
                    "owned_by": "z.ai"
                }
            ]
        }))
    )
}

// Dummy placeholders for unused image APIs to avoid compilation failures
pub async fn handle_images_generations(
    State(_state): State<AppState>,
    Json(_body): Json<Value>,
) -> impl IntoResponse {
    (StatusCode::NOT_IMPLEMENTED, "Image generation not implemented for Z Code")
}

pub async fn handle_images_edits(
    State(_state): State<AppState>,
    Json(_body): Json<Value>,
) -> impl IntoResponse {
    (StatusCode::NOT_IMPLEMENTED, "Image edits not implemented for Z Code")
}
