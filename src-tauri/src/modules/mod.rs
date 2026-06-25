pub mod account;
pub mod account_service;
pub mod cache;
pub mod cloudflared;
pub mod config;
pub mod db;
pub mod device;
#[allow(dead_code)]
pub mod http_api;
pub mod i18n;
pub mod integration;
pub mod log_bridge;
pub mod logger;
pub mod migration;
pub mod oauth;
pub mod oauth_server;
pub mod process;
pub mod proxy_db;
pub mod quota;
pub mod scheduler;
pub mod security_db;
pub mod token_stats;
pub mod tray;
pub mod update_checker;
pub mod user_token_db;
pub mod version;

use crate::models;

// Re-export commonly used functions to the top level of the modules namespace for easy external calling
pub use account::*;
pub use config::*;
#[allow(unused_imports)]
pub use logger::*;
#[allow(unused_imports)]
pub use quota::*;
// pub use device::*;

pub async fn fetch_quota(
    access_token: &str,
    email: &str,
    account_id: Option<&str>,
) -> crate::error::AppResult<(models::QuotaData, Option<String>)> {
    if email.ends_with("(Z.ai)") {
        // For Z.ai accounts, use the ZCode billing/balance API with id_token
        // Try to get the id_token from the account file
        let id_token = if let Some(aid) = account_id {
            account::load_account(aid)
                .ok()
                .and_then(|acc| acc.token.id_token.clone())
        } else {
            None
        };
        
        let token_for_api = id_token.as_deref().unwrap_or(access_token);
        return quota::fetch_quota_zai(token_for_api, email, account_id).await;
    }

    quota::fetch_quota(access_token, email, account_id).await
}
