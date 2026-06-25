import re

with open('src-tauri/src/modules/quota.rs', 'r') as f:
    content = f.read()

old_filter = """                            if name.starts_with("gemini")
                                || name.starts_with("claude")
                                || name.starts_with("gpt")
                                || name.starts_with("image")
                                || name.starts_with("imagen")
                            {"""

new_filter = """                            if true {"""

content = content.replace(old_filter, new_filter)

with open('src-tauri/src/modules/quota.rs', 'w') as f:
    f.write(content)

print("Patched quota.rs filter!")
