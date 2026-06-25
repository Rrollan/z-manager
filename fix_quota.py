import re

with open('src-tauri/src/modules/quota.rs', 'r') as f:
    content = f.read()

# I want to rewrite the limit parsing. Instead of checking `unit == 3`, I will just map the limit whose `total` is 3000000 to GLM-5.2, and 2000000 to GLM-5-Turbo. 
# But wait, what if `total` is not exactly 3000000? 
# The user said "у них лимиты стандартно это: 3,000,000 на 5.2 и 2,000,000 на 5-Turbo в сутки"
# Let's just create these two models in `quota.rs` based on the limits.

new_logic = """
        let mut has_52 = false;
        let mut has_turbo = false;

        if let Some(limits) = zai_resp.limits {
            for limit in limits {
                let used_pct = limit.percentage.unwrap_or(0.0);
                let remaining_pct = (100.0 - used_pct).max(0.0).min(100.0);
                let remaining_fraction = remaining_pct / 100.0;
                let reset_time_str = limit.next_reset_time.map(format_epoch_to_rfc3339).unwrap_or_default();
                let total = limit.total.unwrap_or(0);

                if limit.limit_type == "TOKENS_LIMIT" {
                    if total >= 3000000 || (!has_52 && !has_turbo) {
                        has_52 = true;
                        quota_data.models.push(ModelQuota {
                            name: "GLM-5.2".to_string(),
                            percentage: remaining_pct as i32,
                            reset_time: reset_time_str.clone(),
                            display_name: Some("GLM-5.2".to_string()),
                            supports_images: Some(true),
                            supports_thinking: Some(true),
                            thinking_budget: Some(1024),
                            recommended: Some(true),
                            max_tokens: Some(3000000),
                            max_output_tokens: Some(8192),
                            supported_mime_types: None,
                        });
                        buckets.push(QuotaBucket {
                            bucket_id: "glm-5.2".to_string(),
                            window: "24h".to_string(),
                            remaining_fraction,
                            reset_time: reset_time_str.clone(),
                            display_name: Some("GLM-5.2 Daily Limit".to_string()),
                            description: Some(format!("Used: {:.1}%", used_pct)),
                        });
                    } else if total >= 2000000 || (has_52 && !has_turbo) {
                        has_turbo = true;
                        quota_data.models.push(ModelQuota {
                            name: "GLM-5-Turbo".to_string(),
                            percentage: remaining_pct as i32,
                            reset_time: reset_time_str.clone(),
                            display_name: Some("GLM-5-Turbo".to_string()),
                            supports_images: Some(true),
                            supports_thinking: Some(false),
                            thinking_budget: None,
                            recommended: Some(false),
                            max_tokens: Some(2000000),
                            max_output_tokens: Some(8192),
                            supported_mime_types: None,
                        });
                        buckets.push(QuotaBucket {
                            bucket_id: "glm-5-turbo".to_string(),
                            window: "24h".to_string(),
                            remaining_fraction,
                            reset_time: reset_time_str,
                            display_name: Some("GLM-5-Turbo Daily Limit".to_string()),
                            description: Some(format!("Used: {:.1}%", used_pct)),
                        });
                    }
                }
            }
        }
"""

start_idx = content.find('if let Some(limits) = zai_resp.limits {')
end_idx = content.find('if !buckets.is_empty() {', start_idx)

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_logic + content[end_idx:]
    with open('src-tauri/src/modules/quota.rs', 'w') as f:
        f.write(content)
    print("Patched quota.rs")
else:
    print("Could not find limits parsing logic in quota.rs")
