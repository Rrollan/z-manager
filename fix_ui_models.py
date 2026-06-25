import os
import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Replacements for AccountRow.tsx and CurrentAccount.tsx, MiniView.tsx
    # We replace geminiProModel -> glm5hModel
    # geminiFlashModel -> claudeModel
    # geminiImageModel -> gptModel
    
    # But wait, we need to change how they are defined.
    # Let's just do a simple sed-like replace for the definitions:
    
    content = re.sub(
        r"const geminiProModel = account(\??)\.quota\?\.models\s*\n\s*\.filter\(m =>.*?\.sort.*?\[0\];",
        r"const glm5hModel = account\1.quota?.models.find(m => m.name.toLowerCase().includes('glm-5.2 (5h)') || m.name.toLowerCase() === 'glm-5.2');",
        content,
        flags=re.DOTALL
    )
    
    content = re.sub(
        r"const geminiProModel = account(\??)\.quota\?\.models\.find\(m => m\.name\.toLowerCase\(\) === 'gemini-3\.1-pro-high' \|\| m\.name\.toLowerCase\(\) === 'gemini-3\.1-pro-low'\);",
        r"const glm5hModel = account\1.quota?.models.find(m => m.name.toLowerCase().includes('glm-5.2 (5h)') || m.name.toLowerCase() === 'glm-5.2');",
        content
    )
    
    content = re.sub(
        r"const geminiFlashModel = account(\??)\.quota\?\.models\.find\(m => m\.name\.toLowerCase\(\) === 'gemini-3-flash'\);",
        r"const claudeModel = account\1.quota?.models.find(m => m.name.toLowerCase().includes('claude-3-5-sonnet'));",
        content
    )

    content = re.sub(
        r"const geminiImageModel = account(\??)\.quota\?\.models\.find\(m => m\.name\.toLowerCase\(\) === 'gemini-3-pro-image'\);",
        r"const gptModel = account\1.quota?.models.find(m => m.name.toLowerCase().includes('gpt-4o') && !m.name.toLowerCase().includes('mini'));",
        content
    )
    
    content = re.sub(
        r"const claudeGroupNames = \[.*?\];\s*const claudeModel = account(\??)\.quota\?\.models.*?\.sort.*?\[0\];",
        r"const claudeModel = account\1.quota?.models.find(m => m.name.toLowerCase().includes('claude-3-5-sonnet'));",
        content,
        flags=re.DOTALL
    )

    # Replace usages
    content = content.replace("geminiProModel", "glm5hModel")
    content = content.replace("geminiFlashModel", "claudeModel")
    content = content.replace("geminiImageModel", "gptModel")
    
    content = content.replace("G3.1 Pro", "GLM 5.2")
    content = content.replace("Gemini 3.1 Pro", "GLM 5.2")
    
    content = content.replace("G3 Flash", "Claude 3.5")
    content = content.replace("Gemini 3 Flash", "Claude 3.5 Sonnet")
    
    content = content.replace("G3 Image", "GPT-4o")
    content = content.replace("Gemini 3 Image", "GPT-4o")
    
    content = content.replace("Claude 4.6 TK", "Claude 3.5")
    content = content.replace("Claude 4.6", "Claude 3.5 Sonnet")
    
    # In AccountRow, there are 4 columns. We can just keep them as GLM, Claude, GPT, and maybe we can remove the 4th or change it to GLM Weekly.
    
    with open(filepath, 'w') as f:
        f.write(content)

src_dir = "src/components"
for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith(".tsx"):
            process_file(os.path.join(root, file))

print("Done replacing in components")
