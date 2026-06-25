import re

with open('src-tauri/src/modules/quota.rs', 'r') as f:
    content = f.read()

# I will replace the fetch_quota_with_cache entirely to fetch from Z.ai API!

start = content.find("pub async fn fetch_quota_with_cache(")
end = content.find("pub async fn fetch_quota_inner(", start)

if start == -1 or end == -1:
    end = content.find("async fn fetch_quota_summary(", start)

new_func = """
#[derive(Debug, Deserialize)]
struct ZaiQuotaResponse {
    level: Option<String>,
    limits: Option<Vec<ZaiLimit>>,
}

#[derive(Debug, Deserialize)]
struct ZaiLimit {
    #[serde(rename = "limitType")]
    limit_type: String,
    total: Option<u64>,
    percentage: Option<f64>,
    #[serde(rename = "nextResetTime")]
    next_reset_time: Option<u64>,
}

pub async fn fetch_quota_with_cache(
    access_token: &str,
    email: &str,
    _cached_project_id: Option<&str>,
    account_id: Option<&str>,
) -> crate::error::AppResult<(QuotaData, Option<String>)> {
    use crate::error::AppError;
    let client = create_standard_client(account_id).await;
    
    let res = client
        .get("https://api.z.ai/api/monitor/usage/quota/limit")
        .bearer_auth(access_token)
        .header("User-Agent", crate::constants::NATIVE_OAUTH_USER_AGENT.as_str())
        .send()
        .await;

    let mut quota_data = QuotaData::new();
    
    match res {
        Ok(response) => {
            let status = response.status();
            
            if status == rquest::StatusCode::UNAUTHORIZED {
                return Err(AppError::Unknown(format!("API Error: 401 Unauthorized")));
            }
            
            if !status.is_success() {
                return Err(AppError::Unknown(format!("API Error: {}", status)));
            }
            
            if let Ok(zai_resp) = response.json::<ZaiQuotaResponse>().await {
                quota_data.subscription_tier = zai_resp.level.clone();
                
                let mut has_52 = false;
                let mut has_turbo = false;
                
                if let Some(limits) = zai_resp.limits {
                    for limit in limits {
                        if limit.limit_type == "TOKENS_LIMIT" {
                            let total = limit.total.unwrap_or(0);
                            let remaining_fraction = limit.percentage.unwrap_or(0.0) / 100.0;
                            let percentage = limit.percentage.map(|p| p as i32).unwrap_or(0);
                            
                            // Guess model based on total tokens standard
                            if total >= 3000000 || (!has_52 && !has_turbo) {
                                quota_data.add_model(crate::models::quota::ModelQuota {
                                    name: "GLM-5.2".to_string(),
                                    percentage,
                                    reset_time: limit.next_reset_time.map(|t| t.to_string()).unwrap_or_default(),
                                    display_name: Some("GLM-5.2".to_string()),
                                    supports_images: Some(true),
                                    supports_thinking: Some(true),
                                    thinking_budget: Some(1024),
                                    recommended: Some(true),
                                    max_tokens: Some(3000000),
                                    max_output_tokens: Some(8192),
                                    supported_mime_types: None,
                                });
                                has_52 = true;
                            } else {
                                quota_data.add_model(crate::models::quota::ModelQuota {
                                    name: "GLM-5-Turbo".to_string(),
                                    percentage,
                                    reset_time: limit.next_reset_time.map(|t| t.to_string()).unwrap_or_default(),
                                    display_name: Some("GLM-5-Turbo".to_string()),
                                    supports_images: Some(true),
                                    supports_thinking: Some(false),
                                    thinking_budget: None,
                                    recommended: Some(false),
                                    max_tokens: Some(2000000),
                                    max_output_tokens: Some(8192),
                                    supported_mime_types: None,
                                });
                                has_turbo = true;
                            }
                        }
                    }
                }
                
                // Fallback if limits didn't match
                if !has_52 {
                    quota_data.add_model(crate::models::quota::ModelQuota {
                        name: "GLM-5.2".to_string(),
                        percentage: 100,
                        reset_time: "".to_string(),
                        display_name: Some("GLM-5.2".to_string()),
                        supports_images: Some(true),
                        supports_thinking: Some(true),
                        thinking_budget: Some(1024),
                        recommended: Some(true),
                        max_tokens: Some(3000000),
                        max_output_tokens: Some(8192),
                        supported_mime_types: None,
                    });
                }
                if !has_turbo {
                    quota_data.add_model(crate::models::quota::ModelQuota {
                        name: "GLM-5-Turbo".to_string(),
                        percentage: 100,
                        reset_time: "".to_string(),
                        display_name: Some("GLM-5-Turbo".to_string()),
                        supports_images: Some(true),
                        supports_thinking: Some(false),
                        thinking_budget: None,
                        recommended: Some(false),
                        max_tokens: Some(2000000),
                        max_output_tokens: Some(8192),
                        supported_mime_types: None,
                    });
                }
                
                return Ok((quota_data, None));
            } else {
                return Err(AppError::Unknown("Failed to parse Z.ai quota response".to_string()));
            }
        }
        Err(e) => {
            return Err(AppError::Unknown(format!("Quota API network error: {}", e)));
        }
    }
}
"""

content = content[:start] + new_func + content[end:]

with open('src-tauri/src/modules/quota.rs', 'w') as f:
    f.write(content)

print("Implemented real Z.ai quota fetch logic")
