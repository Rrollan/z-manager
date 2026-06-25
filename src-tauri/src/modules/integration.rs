use crate::models::Account;
use crate::modules::{db, device, process, version};
use std::fs;
use std::process::Command;

pub trait SystemIntegration: Send + Sync {
    /// 当切换账号时执行的系统层操作（如杀进程、写入文件、注入数据库）
    async fn on_account_switch(
        &self,
        account: &crate::models::Account,
        target_ide: Option<&str>,
    ) -> Result<(), String>;

    /// 更新系统托盘（如果适用）
    fn update_tray(&self);

    /// 发送系统通知
    fn show_notification(&self, title: &str, body: &str);
}

/// 桌面版实现：包含完整的进程控制 and UI 同步
pub struct DesktopIntegration {
    pub app_handle: tauri::AppHandle,
}

impl SystemIntegration for DesktopIntegration {
    async fn on_account_switch(
        &self,
        account: &crate::models::Account,
        target_ide: Option<&str>,
    ) -> Result<(), String> {
        crate::modules::logger::log_info(&format!(
            "[Desktop] Executing system switch for: {} (target_ide: {:?})",
            account.email, target_ide
        ));

        // Sync credentials to ZCode configuration file
        if let Err(e) = sync_account_to_zcode(account) {
            crate::modules::logger::log_warn(&format!("[Desktop] Failed to sync credentials to ZCode: {}", e));
        } else {
            // If ZCode is running, restart it to apply the new session
            if process::is_process_running_by_name("ZCode") {
                crate::modules::logger::log_info("[Desktop] ZCode is running, restarting it to apply new session...");
                let _ = Command::new("killall").arg("ZCode").output();
                std::thread::sleep(std::time::Duration::from_millis(800));
            } else {
                crate::modules::logger::log_info("[Desktop] ZCode is not running, launching it to apply new session...");
            }
            let _ = Command::new("open").args(["-a", "ZCode"]).output();
            
            let msg = format!("Account {} activated and synced to ZCode.", account.email);
            self.show_notification("Z Manager", &msg);
        }

        // 4. 更新托盘
        self.update_tray();

        Ok(())
    }

    fn update_tray(&self) {
        let _ = crate::modules::tray::update_tray_menus(&self.app_handle);
    }

    fn show_notification(&self, title: &str, body: &str) {
        // 使用 tauri-plugin-dialog 或原生通知（此处简化）
        crate::modules::logger::log_info(&format!("[Notification] {}: {}", title, body));
    }
}

/// 辅助方法：向宿主操作系统的 Keychain/Credentials Manager 写入 Token
fn write_to_system_keyring(account: &crate::models::Account) -> Result<(), String> {
    // 1. 构建 Token 的 JSON Payload，并将过期时间戳格式化为符合 RFC3339 的带微秒格式
    let expiry_datetime = chrono::DateTime::from_timestamp(account.token.expiry_timestamp, 0)
        .unwrap_or_else(|| chrono::Utc::now());
    let expiry_str = expiry_datetime.to_rfc3339_opts(chrono::SecondsFormat::Micros, true);

    #[derive(serde::Serialize)]
    struct KeyringTokenDetails {
        access_token: String,
        token_type: String,
        refresh_token: String,
        expiry: String,
    }

    #[derive(serde::Serialize)]
    struct KeyringPayload {
        token: KeyringTokenDetails,
        auth_method: String,
    }

    let payload_json = serde_json::to_string(&KeyringPayload {
        token: KeyringTokenDetails {
            access_token: account.token.access_token.clone(),
            token_type: "Bearer".to_string(),
            refresh_token: account.token.refresh_token.clone(),
            expiry: expiry_str,
        },
        auth_method: "consumer".to_string(),
    })
    .map_err(|e| format!("Failed to serialize keyring JSON: {}", e))?;

    crate::modules::logger::log_info(&format!(
        "[Desktop] Writing token to system credential store for: {}",
        account.email
    ));

    // 2. 跨平台凭据注入
    #[cfg(target_os = "macos")]
    {
        use base64::{engine::general_purpose::STANDARD, Engine as _};
        let encoded_payload = STANDARD.encode(&payload_json);
        let full_keyring_value = format!("go-keyring-base64:{}", encoded_payload);

        // 2.1 macOS Keychain Access
        // 删除旧的
        let _ = Command::new("security")
            .args([
                "delete-generic-password",
                "-s",
                "gemini",
                "-a",
                "antigravity",
            ])
            .output();

        // 写入新的 (-A 参数允许所有本地应用免密码、无感直接读取凭据)
        let output = Command::new("security")
            .args([
                "add-generic-password",
                "-s",
                "gemini",
                "-a",
                "antigravity",
                "-w",
                &full_keyring_value,
                "-A",
            ])
            .output()
            .map_err(|e| format!("Failed to execute security command: {}", e))?;

        if !output.status.success() {
            let err_msg = String::from_utf8_lossy(&output.stderr);
            return Err(format!("macOS security command failed: {}", err_msg.trim()));
        }
    }

    #[cfg(target_os = "windows")]
    {
        // 2.2 Windows Credential Manager direct Win32 API calls to write raw UTF-8 bytes
        use std::os::windows::ffi::OsStrExt;
        use std::ptr;

        #[repr(C)]
        struct FILETIME {
            dw_low_date_time: u32,
            dw_high_date_time: u32,
        }

        #[repr(C)]
        struct CREDENTIALW {
            flags: u32,
            cred_type: u32,
            target_name: *const u16,
            comment: *const u16,
            last_written: FILETIME,
            credential_blob_size: u32,
            credential_blob: *const u8,
            persist: u32,
            attribute_count: u32,
            attributes: *const std::ffi::c_void,
            target_alias: *const u16,
            user_name: *const u16,
        }

        #[link(name = "advapi32")]
        extern "system" {
            fn CredWriteW(credential: *const CREDENTIALW, flags: u32) -> i32;
            fn CredDeleteW(target_name: *const u16, type_: u32, flags: u32) -> i32;
        }

        let target = "gemini:antigravity";
        let user = "antigravity";
        let secret = payload_json.as_bytes();

        let target_wide: Vec<u16> = std::ffi::OsStr::new(target)
            .encode_wide()
            .chain(std::iter::once(0))
            .collect();

        let user_wide: Vec<u16> = std::ffi::OsStr::new(user)
            .encode_wide()
            .chain(std::iter::once(0))
            .collect();

        let cred = CREDENTIALW {
            flags: 0,
            cred_type: 1, // CRED_TYPE_GENERIC
            target_name: target_wide.as_ptr(),
            comment: ptr::null(),
            last_written: FILETIME {
                dw_low_date_time: 0,
                dw_high_date_time: 0,
            },
            credential_blob_size: secret.len() as u32,
            credential_blob: secret.as_ptr(),
            persist: 2, // CRED_PERSIST_LOCAL_MACHINE
            attribute_count: 0,
            attributes: ptr::null(),
            target_alias: ptr::null(),
            user_name: user_wide.as_ptr(),
        };

        unsafe {
            // Delete first to ensure we write clean
            let _ = CredDeleteW(target_wide.as_ptr(), 1, 0);

            let res = CredWriteW(&cred, 0);
            if res == 0 {
                let err = std::io::Error::last_os_error();
                return Err(format!("Windows CredWriteW failed: {}", err));
            }
        }
    }

    #[cfg(target_os = "linux")]
    {
        // 2.3 Linux Secret Service API
        use std::io::Write;
        let mut child = Command::new("secret-tool")
            .args([
                "store",
                "--label=gemini",
                "service",
                "gemini",
                "username",
                "antigravity",
            ])
            .stdin(std::process::Stdio::piped())
            .stdout(std::process::Stdio::piped())
            .stderr(std::process::Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to spawn secret-tool: {}", e))?;

        if let Some(mut stdin) = child.stdin.take() {
            stdin
                .write_all(payload_json.as_bytes())
                .map_err(|e| format!("Failed to write to secret-tool stdin: {}", e))?;
        }

        let output = child
            .wait_with_output()
            .map_err(|e| format!("Failed to wait for secret-tool: {}", e))?;

        if !output.status.success() {
            let err_msg = String::from_utf8_lossy(&output.stderr);
            return Err(format!("Linux secret-tool failed: {}", err_msg.trim()));
        }
    }

    crate::modules::logger::log_info(
        "[Desktop] Successfully wrote token to system credential store.",
    );
    Ok(())
}

/// Headless/Docker 实现：仅执行数据层操作，忽略 UI 和进程控制
pub struct HeadlessIntegration;

impl SystemIntegration for HeadlessIntegration {
    async fn on_account_switch(
        &self,
        account: &crate::models::Account,
        _target_ide: Option<&str>,
    ) -> Result<(), String> {
        if _target_ide == Some("agy") {
            return Err(
                "Switching to the agy CLI is not supported in headless mode (no host keyring access)."
                    .to_string(),
            );
        }

        crate::modules::logger::log_info(&format!(
            "[Headless] Account switched in memory: {}",
            account.email
        ));
        // Docker 模式下通常不直接控制宿主机的 VS Code 进程
        // 如果需要同步配置 to 某个 volume，可以在此处添加逻辑
        Ok(())
    }

    fn update_tray(&self) {
        // No-op
    }

    fn show_notification(&self, title: &str, body: &str) {
        crate::modules::logger::log_info(&format!("[Log Notification] {}: {}", title, body));
    }
}

/// 系统集成管理器：替代 Arc<dyn SystemIntegration> 以解决 async trait 的 dyn 兼容性问题
#[derive(Clone)]
pub enum SystemManager {
    Desktop(tauri::AppHandle),
    Headless,
}

impl SystemManager {
    pub async fn on_account_switch(
        &self,
        account: &Account,
        target_ide: Option<&str>,
    ) -> Result<(), String> {
        match self {
            SystemManager::Desktop(handle) => {
                let integration = DesktopIntegration {
                    app_handle: handle.clone(),
                };
                integration.on_account_switch(account, target_ide).await
            }
            SystemManager::Headless => {
                let integration = HeadlessIntegration;
                integration.on_account_switch(account, target_ide).await
            }
        }
    }

    pub fn update_tray(&self) {
        if let SystemManager::Desktop(handle) = self {
            let integration = DesktopIntegration {
                app_handle: handle.clone(),
            };
            integration.update_tray();
        }
    }

    pub fn show_notification(&self, title: &str, body: &str) {
        match self {
            SystemManager::Desktop(handle) => {
                let integration = DesktopIntegration {
                    app_handle: handle.clone(),
                };
                integration.show_notification(title, body);
            }
            SystemManager::Headless => {
                let integration = HeadlessIntegration;
                integration.show_notification(title, body);
            }
        }
    }
}

impl SystemIntegration for SystemManager {
    async fn on_account_switch(
        &self,
        account: &crate::models::Account,
        target_ide: Option<&str>,
    ) -> Result<(), String> {
        match self {
            SystemManager::Desktop(handle) => {
                let integration = DesktopIntegration {
                    app_handle: handle.clone(),
                };
                integration.on_account_switch(account, target_ide).await
            }
            SystemManager::Headless => {
                let integration = HeadlessIntegration;
                integration.on_account_switch(account, target_ide).await
            }
        }
    }

    fn update_tray(&self) {
        self.update_tray();
    }

    fn show_notification(&self, title: &str, body: &str) {
        self.show_notification(title, body);
    }
}

fn encrypt_zcode_string(plaintext: &str) -> Result<String, String> {
    use aes_gcm::{
        aead::{Aead, KeyInit},
        Aes256Gcm, Nonce,
    };
    use rand::{rngs::OsRng, RngCore};
    use base64::{engine::general_purpose, Engine as _};
    use sha2::Digest;
    
    // 1. Derive key
    let home_dir = dirs::home_dir().ok_or_else(|| "Failed to get home directory".to_string())?;
    let home_dir_str = home_dir.to_string_lossy().to_string();
    
    let username = std::env::var("USER")
        .or_else(|_| std::env::var("USERNAME"))
        .unwrap_or_else(|_| "unknown".to_string());
        
    let fallback_secret = format!("zcode-credential-fallback:darwin:{}:{}", home_dir_str, username);
    let mut key_bytes = [0u8; 32];
    let hash = sha2::Sha256::digest(fallback_secret.as_bytes());
    key_bytes.copy_from_slice(&hash);
    
    // 2. Cipher
    let cipher = Aes256Gcm::new(&key_bytes.into());
    
    let mut nonce_bytes = [0u8; 12];
    OsRng.fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);
    
    let ciphertext_with_tag = cipher
        .encrypt(nonce, plaintext.as_bytes())
        .map_err(|e| format!("Encryption failed: {}", e))?;
        
    if ciphertext_with_tag.len() < 16 {
        return Err("Encryption yielded invalid ciphertext length".to_string());
    }
    
    let actual_ciphertext = &ciphertext_with_tag[..ciphertext_with_tag.len() - 16];
    let auth_tag = &ciphertext_with_tag[ciphertext_with_tag.len() - 16..];
    
    let encoded_iv = general_purpose::URL_SAFE_NO_PAD.encode(nonce_bytes);
    let encoded_tag = general_purpose::URL_SAFE_NO_PAD.encode(auth_tag);
    let encoded_ciphertext = general_purpose::URL_SAFE_NO_PAD.encode(actual_ciphertext);
    
    Ok(format!("enc:v1:{}.{}.{}", encoded_iv, encoded_tag, encoded_ciphertext))
}

pub fn sync_account_to_zcode(account: &crate::models::Account) -> Result<(), String> {
    let access_token = &account.token.access_token;
    let zcode_jwt_token = account.token.id_token.as_ref().unwrap_or(&account.token.access_token);
    
    let enc_access_token = encrypt_zcode_string(access_token)?;
    let enc_zcode_jwt_token = encrypt_zcode_string(zcode_jwt_token)?;
    
    let user_id = &account.id;
    let email = &account.email;
    let name = email.split('@').next().unwrap_or("user");
    
    let user_info_json = serde_json::json!({
        "user_id": user_id,
        "email": email,
        "name": name,
        "avatar": ""
    });
    let user_info_str = serde_json::to_string(&user_info_json)
        .map_err(|e| format!("Failed to serialize user info: {}", e))?;
        
    let enc_user_info = encrypt_zcode_string(&user_info_str)?;
    let enc_active_provider = encrypt_zcode_string("zai")?;
    
    let home_dir = dirs::home_dir().ok_or_else(|| "Failed to get home directory".to_string())?;
    let zcode_dir = home_dir.join(".zcode").join("v2");
    let credentials_path = zcode_dir.join("credentials.json");
    
    let _ = std::fs::create_dir_all(&zcode_dir);
    
    let mut creds_map: serde_json::Map<String, serde_json::Value> = if credentials_path.exists() {
        let file_content = std::fs::read_to_string(&credentials_path)
            .map_err(|e| format!("Failed to read ZCode credentials: {}", e))?;
        serde_json::from_str(&file_content).unwrap_or_default()
    } else {
        serde_json::Map::new()
    };
    
    creds_map.insert("oauth:zai:access_token".to_string(), serde_json::Value::String(enc_access_token));
    creds_map.insert("zcodejwttoken".to_string(), serde_json::Value::String(enc_zcode_jwt_token));
    creds_map.insert("oauth:zai:user_info".to_string(), serde_json::Value::String(enc_user_info));
    creds_map.insert("oauth:active_provider".to_string(), serde_json::Value::String(enc_active_provider));
    
    let updated_content = serde_json::to_string_pretty(&creds_map)
        .map_err(|e| format!("Failed to serialize ZCode credentials: {}", e))?;
    std::fs::write(&credentials_path, updated_content)
        .map_err(|e| format!("Failed to write ZCode credentials: {}", e))?;
        
    crate::modules::logger::log_info(&format!("Successfully synced active Z.ai session to ZCode at {}", credentials_path.display()));
    
    Ok(())
}
