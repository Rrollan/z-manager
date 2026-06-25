import re
with open('src/config/modelConfig.ts', 'r') as f:
    content = f.read()

content = re.sub(r"\s*i18nKey: '[^']+',", "", content)
content = re.sub(r"\s*i18nDescKey: '[^']+',", "", content)

with open('src/config/modelConfig.ts', 'w') as f:
    f.write(content)
print("Fixed modelConfig.ts i18n keys")
