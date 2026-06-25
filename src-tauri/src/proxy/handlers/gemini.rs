// Gemini Handler placeholder for Z Code / Z.ai
use axum::{
    extract::{State, Path},
    extract::Json,
    http::{StatusCode, HeaderMap},
    response::IntoResponse,
};
use serde_json::{json, Value};
use crate::proxy::server::AppState;

pub async fn handle_generate(
    State(_state): State<AppState>,
    Path(_model_action): Path<String>,
    _headers: HeaderMap,
    _body: Option<Json<Value>>,
) -> impl IntoResponse {
    (StatusCode::NOT_IMPLEMENTED, "Gemini protocol not supported in Z Code manager")
}

pub async fn handle_list_models(State(_state): State<AppState>) -> impl IntoResponse {
    (
        StatusCode::OK,
        Json(json!({
            "models": [
                {
                    "name": "models/glm-5.2",
                    "version": "v1beta",
                    "displayName": "GLM-5.2",
                    "description": "Z.ai GLM Reasoning Model"
                }
            ]
        }))
    )
}

pub async fn handle_get_model(
    State(_state): State<AppState>,
    Path(_model): Path<String>,
) -> impl IntoResponse {
    (
        StatusCode::OK,
        Json(json!({
            "name": "models/glm-5.2",
            "version": "v1beta",
            "displayName": "GLM-5.2",
            "description": "Z.ai GLM Reasoning Model"
        }))
    )
}

pub async fn handle_count_tokens(
    State(_state): State<AppState>,
    Path(_model): Path<String>,
    _body: Json<Value>,
) -> impl IntoResponse {
    (
        StatusCode::OK,
        Json(json!({
            "totalTokens": 100
        }))
    )
}
