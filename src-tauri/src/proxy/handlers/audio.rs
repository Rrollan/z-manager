// Audio Handler placeholder for Z Code / Z.ai
use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
};
use crate::proxy::server::AppState;

pub async fn handle_audio_transcription(
    State(_state): State<AppState>,
) -> impl IntoResponse {
    (StatusCode::NOT_IMPLEMENTED, "Audio transcription not supported in Z Code manager")
}
