import re

with open('src/components/settings/PinnedQuotaModels.tsx', 'r') as f:
    content = f.read()

content = content.replace("t(config?.i18nKey, config?.label)", "(config?.i18nKey ? t(config.i18nKey, config?.label) : config?.label)")

with open('src/components/settings/PinnedQuotaModels.tsx', 'w') as f:
    f.write(content)

print("Fixed PinnedQuotaModels")
