// Warmup Handler placeholder for Z Code / Z.ai
use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    Json,
};
use serde_json::json;
use crate::proxy::server::AppState;

pub async fn handle_warmup(
    State(_state): State<AppState>,
) -> impl IntoResponse {
    (
        StatusCode::OK,
        Json(json!({
            "success": true,
            "message": "Warmup bypassed for Z Code"
        }))
    )
}
