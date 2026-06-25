use axum::{
    body::Body,
    http::{header, HeaderMap, HeaderValue, Method, StatusCode},
    response::{IntoResponse, Response},
};
use bytes::Bytes;
use futures::StreamExt;
use serde_json::Value;
use tokio::time::Duration;
use crate::proxy::server::AppState;

pub async fn forward_request_to_zai(
    state: &AppState,
    method: Method,
    url: &str,
    incoming_headers: &HeaderMap,
    body: Value,
    api_key: &str,
) -> Response {
    let timeout_secs = state.request_timeout.max(5);
    
    // Copy incoming headers that are safe to pass through
    let mut headers = HeaderMap::new();
    for (k, v) in incoming_headers.iter() {
        let key = k.as_str().to_ascii_lowercase();
        match key.as_str() {
            "content-type" | "accept" | "anthropic-version" | "user-agent" | "accept-encoding" | "cache-control" => {
                headers.insert(k.clone(), v.clone());
            }
            _ => {}
        }
    }

    // Set Z.ai Auth
    let has_auth = incoming_headers.contains_key(header::AUTHORIZATION);
    let has_x_api_key = incoming_headers.contains_key("x-api-key");
    if has_x_api_key && !has_auth {
        if let Ok(v) = HeaderValue::from_str(api_key) {
            headers.insert("x-api-key", v);
        }
    } else {
        if let Ok(v) = HeaderValue::from_str(&format!("Bearer {}", api_key)) {
            headers.insert(header::AUTHORIZATION, v);
        }
    }

    // Ensure content-type
    headers.entry(header::CONTENT_TYPE).or_insert(HeaderValue::from_static("application/json"));

    // Serialize body
    let body_bytes = serde_json::to_vec(&body).unwrap_or_default();

    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(timeout_secs))
        .tcp_nodelay(true)
        .build()
        .unwrap_or_default();

    let req = client
        .request(method, url)
        .headers(headers)
        .body(body_bytes);

    let resp = match req.send().await {
        Ok(r) => r,
        Err(e) => {
            return (
                StatusCode::BAD_GATEWAY,
                format!("Upstream Z.ai request failed: {}", e),
            ).into_response();
        }
    };

    let status = StatusCode::from_u16(resp.status().as_u16()).unwrap_or(StatusCode::BAD_GATEWAY);

    let mut out = Response::builder().status(status);
    if let Some(ct) = resp.headers().get(header::CONTENT_TYPE) {
        out = out.header(header::CONTENT_TYPE, ct.clone());
    }

    // Stream response body (SSE and non-SSE)
    let stream = resp.bytes_stream().map(|chunk| match chunk {
        Ok(b) => Ok::<Bytes, std::io::Error>(b),
        Err(e) => Ok(Bytes::from(format!("Upstream stream error: {}", e))),
    });

    out.body(Body::from_stream(stream)).unwrap_or_else(|_| {
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            "Failed to build response",
        ).into_response()
    })
}
