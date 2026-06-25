use crate::models::{Account, TokenData};
use crate::modules;

/// 账号服务层 - 彻底解除对 Tauri 运行时的依赖
pub struct AccountService {
    pub integration: crate::modules::integration::SystemManager,
}

async fn resolve_token(code_or_token: &str) -> Result<String, String> {
    let trimmed = code_or_token.trim();
    
    // If it's a JWT (contains dots and is long)
    if trimmed.contains('.') && trimmed.len() > 40 {
        return Ok(trimmed.to_string());
    }
    
    // If it starts with zcode:// or is a zcode auth URL containing code=
    let mut captured_state = None;
    let code = if trimmed.starts_with("zcode://") || trimmed.contains("code=") {
        if let Ok(url) = url::Url::parse(trimmed) {
            let mut captured_code = None;
            if let Some(query) = url.query() {
                for (k, v) in url::form_urlencoded::parse(query.as_bytes()) {
                    if k == "code" {
                        captured_code = Some(v.into_owned());
                    } else if k == "state" {
                        captured_state = Some(v.into_owned());
                    }
                }
            }
            captured_code.ok_or_else(|| "Failed to find 'code' parameter in ZCode redirect URL".to_string())?
        } else {
            // Fallback: simple string splitting if parsing fails
            if let Some(pos) = trimmed.find("code=") {
                let code_part = &trimmed[pos + 5..];
                let end_pos = code_part.find('&').unwrap_or(code_part.len());
                code_part[..end_pos].to_string()
            } else {
                trimmed.to_string()
            }
        }
    } else {
        trimmed.to_string()
    };
    
    // If it still looks like an API Key or token (starts with eyJ or has dots or is very long), return it directly
    if code.contains('.') || code.starts_with("eyJ") || code.len() > 100 {
        return Ok(code);
    }
    
    modules::logger::log_info(&format!("Exchanging ZCode authorization code for access token..."));
    
    let client = reqwest::Client::new();
    let state_val = captured_state.unwrap_or_else(|| uuid::Uuid::new_v4().simple().to_string());

    let response = client.post("https://zcode.z.ai/api/v1/oauth/token")
        .json(&serde_json::json!({
            "provider": "zai",
            "code": code,
            "redirect_uri": "zcode://zai-auth/callback",
            "state": state_val
        }))
        .send()
        .await
        .map_err(|e| format!("OAuth token exchange request failed: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().await.unwrap_or_default();
        return Err(format!("OAuth token exchange failed ({}): {}", status, body));
    }

    let body_text = response.text().await
        .map_err(|e| format!("Failed to read response body: {}", e))?;

    modules::logger::log_info(&format!("Raw ZCode token exchange response: {}", body_text));

    let json: serde_json::Value = serde_json::from_str(&body_text)
        .map_err(|e| format!("Failed to parse response as JSON: {}. Raw body: {}", e, body_text))?;

    // 1. Check code
    let code_val = json.get("code")
        .and_then(|v| v.as_i64())
        .unwrap_or(0);

    if code_val != 0 {
        let msg = json.get("msg")
            .and_then(|v| v.as_str())
            .unwrap_or("Unknown business error");
        return Err(format!("OAuth token exchange business error ({}): {}", code_val, msg));
    }

    // 2. Extract zcode_jwt_token (from data.token)
    let data = json.get("data").ok_or_else(|| format!("Response missing 'data' field. Raw body: {}", body_text))?;
    
    let zcode_jwt_token = data.get("token")
        .and_then(|v| v.as_str())
        .map(|s| s.to_string())
        .ok_or_else(|| format!("Response 'data' missing 'token' field. Raw body: {}", body_text))?;

    // 3. Extract access_token (replicate ZCode's CY(o) exactly)
    let access_token = data.get("zai")
        .and_then(|zai| zai.get("access_token").or_else(|| zai.get("accessToken")))
        .or_else(|| data.get("bigmodel").and_then(|bm| bm.get("access_token").or_else(|| bm.get("accessToken"))))
        .or_else(|| data.get("access_token"))
        .or_else(|| data.get("accessToken"))
        .and_then(|v| v.as_str())
        .map(|s| s.to_string())
        .unwrap_or_else(|| zcode_jwt_token.clone());

    Ok(format!("{}|{}", access_token, zcode_jwt_token))
}

impl AccountService {
    pub fn new(integration: crate::modules::integration::SystemManager) -> Self {
        Self { integration }
    }

    /// 添加 Z.ai 账号逻辑
    pub async fn add_account(&self, email_input: &str, api_key: &str) -> Result<Account, String> {
        let resolved_api_key = resolve_token(api_key).await
            .map_err(|e| format!("Token resolution failed: {}", e))?;
            
        // Split combined resolved key (access_token|zcode_jwt_token)
        let (access_token, zcode_jwt_token) = if resolved_api_key.contains('|') {
            let parts: Vec<&str> = resolved_api_key.split('|').collect();
            (parts[0].to_string(), Some(parts[1].to_string()))
        } else {
            (resolved_api_key.clone(), Some(resolved_api_key.clone()))
        };
            
        let account_id = uuid::Uuid::new_v4().to_string();

        let email = if email_input.trim().is_empty() {
            let masked = if access_token.len() > 12 {
                format!("{}...{}", &access_token[..6], &access_token[access_token.len()-6..])
            } else {
                "zcode_key".to_string()
            };
            format!("{} (Z.ai)", masked)
        } else {
            email_input.to_string()
        };

        // 1. 获取 Quota 来验证 API Key 并且获取 Limits
        // For Z.ai accounts (using JWT), the quota API (which expects an sk- key) will reject it.
        // So we bypass the quota check and use default values.
        let (quota_data, _) = if email.ends_with("(Z.ai)") {
            // Use the ZCode billing/balance API with the id_token (zcode_jwt_token)
            let zai_token = zcode_jwt_token.as_deref().unwrap_or(&access_token);
            match modules::quota::fetch_quota_zai(zai_token, &email, Some(&account_id)).await {
                Ok(result) => result,
                Err(e) => {
                    // Fallback to defaults if billing API fails
                    crate::modules::logger::log_warn(&format!(
                        "Z.ai billing API failed during add_account, using defaults: {}", e
                    ));
                    let mut fallback_quota = crate::models::QuotaData::new();
                    fallback_quota.subscription_tier = Some("ZCode Start Plan".to_string());
                    fallback_quota.add_model(crate::models::ModelQuota {
                        name: "glm-5.2".to_string(),
                        percentage: 100,
                        reset_time: String::new(),
                        display_name: Some("GLM-5.2".to_string()),
                        supports_images: Some(true),
                        supports_thinking: Some(true),
                        thinking_budget: Some(1024),
                        recommended: Some(true),
                        max_tokens: Some(3000000),
                        max_output_tokens: Some(8192),
                        supported_mime_types: None,
                    });
                    fallback_quota.add_model(crate::models::ModelQuota {
                        name: "glm-5-turbo".to_string(),
                        percentage: 100,
                        reset_time: String::new(),
                        display_name: Some("GLM-5-Turbo".to_string()),
                        supports_images: Some(true),
                        supports_thinking: Some(false),
                        thinking_budget: None,
                        recommended: Some(false),
                        max_tokens: Some(2000000),
                        max_output_tokens: Some(8192),
                        supported_mime_types: None,
                    });
                    (fallback_quota, None)
                }
            }
        } else {
            modules::quota::fetch_quota(&access_token, &email, Some(&account_id))
                .await
                .map_err(|e| format!("Failed to validate Z.ai API key: {}", e))?
        };

        // 2. 构造 TokenData
        let token = TokenData::new(
            access_token.clone(),
            access_token.clone(),
            315360000, // 10 years expiry
            Some(email.clone()),
            None,
            None,
            false,
            zcode_jwt_token, // Store ZCode JWT token in id_token
        );

        // 3. 持久化
        let mut account = modules::upsert_account(email.clone(), Some("Z Code Account".to_string()), token)?;
        account.quota = Some(quota_data);

        if let Err(e) = modules::account::save_account(&account) {
            modules::logger::log_warn(&format!(
                "[Service] Failed to save quota for {}: {}",
                email, e
            ));
        }

        modules::logger::log_info(&format!(
            "[Service] Added/Updated Z Code account: {}",
            account.email
        ));

        self.integration.update_tray();

        Ok(account)
    }

    /// 删除账号逻辑
    pub fn delete_account(&self, account_id: &str) -> Result<(), String> {
        modules::delete_account(account_id)?;
        self.integration.update_tray();
        Ok(())
    }

    /// 切换账号逻辑
    pub async fn switch_account(
        &self,
        account_id: &str,
        target_ide: Option<&str>,
    ) -> Result<(), String> {
        modules::account::switch_account(account_id, target_ide, &self.integration).await
    }

    /// 列表获取
    pub fn list_accounts(&self) -> Result<Vec<Account>, String> {
        modules::list_accounts()
    }

    /// 获取当前 ID
    pub fn get_current_id(&self) -> Result<Option<String>, String> {
        modules::get_current_account_id()
    }

    // --- OAuth 逻辑 (留作 dummy 占位，避免编译错误) ---

    pub async fn prepare_oauth_url(
        &self,
        _oauth_client_key: Option<String>,
    ) -> Result<String, String> {
        Err("OAuth not supported in Z Code manager".to_string())
    }

    pub async fn start_oauth_login(
        &self,
        _oauth_client_key: Option<String>,
    ) -> Result<Account, String> {
        Err("OAuth not supported in Z Code manager".to_string())
    }

    pub async fn complete_oauth_login(&self) -> Result<Account, String> {
        Err("OAuth not supported in Z Code manager".to_string())
    }

    pub fn cancel_oauth_login(&self) {}

    pub async fn submit_oauth_code(
        &self,
        _code: String,
        _state: Option<String>,
    ) -> Result<(), String> {
        Err("OAuth not supported in Z Code manager".to_string())
    }
}
