import re

with open('src-tauri/src/modules/quota.rs', 'r') as f:
    content = f.read()

# Replace the body of fetch_quota_with_cache
# from `pub async fn fetch_quota_with_cache(` to the end of the function (where `Ok((quota_data, project_id.clone()))` is, or just before the `fetch_quota_summary` function)
start = content.find("pub async fn fetch_quota_with_cache(")
end = content.find("pub async fn fetch_quota_inner(", start)

if start == -1 or end == -1:
    end = content.find("async fn fetch_quota_summary(", start)

new_func = """pub async fn fetch_quota_with_cache(
    _access_token: &str,
    email: &str,
    _cached_project_id: Option<&str>,
    _account_id: Option<&str>,
) -> crate::error::AppResult<(QuotaData, Option<String>)> {
    crate::modules::logger::log_info(&format!("Mocking Z.ai quota for {}", email));
    
    let mut quota_data = QuotaData::new();
    quota_data.subscription_tier = Some("Z Code Pro".to_string());
    
    let reset_time = chrono::Utc::now()
        .date_naive()
        .and_hms_opt(23, 59, 59)
        .unwrap()
        .and_utc()
        .to_rfc3339();

    quota_data.add_model(crate::models::quota::ModelQuota {
        name: "GLM-5.2".to_string(),
        percentage: 100,
        reset_time: reset_time.clone(),
        display_name: Some("GLM-5.2".to_string()),
        supports_images: Some(true),
        supports_thinking: Some(true),
        thinking_budget: Some(1024),
        recommended: Some(true),
        max_tokens: Some(3000000),
        max_output_tokens: Some(8192),
        supported_mime_types: None,
    });

    quota_data.add_model(crate::models::quota::ModelQuota {
        name: "GLM-5-Turbo".to_string(),
        percentage: 100,
        reset_time: reset_time.clone(),
        display_name: Some("GLM-5-Turbo".to_string()),
        supports_images: Some(true),
        supports_thinking: Some(false),
        thinking_budget: None,
        recommended: Some(false),
        max_tokens: Some(2000000),
        max_output_tokens: Some(8192),
        supported_mime_types: None,
    });

    Ok((quota_data, None))
}

"""

content = content[:start] + new_func + content[end:]

with open('src-tauri/src/modules/quota.rs', 'w') as f:
    f.write(content)

print("Hardcoded quota in quota.rs")
