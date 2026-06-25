import re

with open('src/components/settings/PinnedQuotaModels.tsx', 'r') as f:
    content = f.read()

content = content.replace("t(cfg.i18nDescKey || cfg.i18nKey, cfg.label)", "(cfg.i18nDescKey || cfg.i18nKey ? t((cfg.i18nDescKey || cfg.i18nKey) as string, cfg.label) : cfg.label)")

with open('src/components/settings/PinnedQuotaModels.tsx', 'w') as f:
    f.write(content)

print("Fixed PinnedQuotaModels 2")
