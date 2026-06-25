import re

with open('src-tauri/src/modules/quota.rs', 'r') as f:
    content = f.read()

content = content.replace('tracing::debug!("Quota API returned {} models", quota_response.models.len());', 
                          'crate::modules::logger::log_info(&format!("Quota API raw models: {:?}", quota_response.models.keys()));')

with open('src-tauri/src/modules/quota.rs', 'w') as f:
    f.write(content)

print("Added logging")
