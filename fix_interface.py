import re

with open('src/config/modelConfig.ts', 'r') as f:
    content = f.read()

content = content.replace("i18nKey: string;", "i18nKey?: string;")
content = content.replace("i18nDescKey: string;", "i18nDescKey?: string;")

with open('src/config/modelConfig.ts', 'w') as f:
    f.write(content)

print("Fixed interface")
