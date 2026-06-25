with open('src/config/modelConfig.ts', 'r') as f:
    content = f.read()

import re
# The new_config was written like this:
# export const MODEL_CONFIG: Record<string, ModelConfig> = { ... }
# Let's just redefine MODEL_CONFIG entirely to only have GLM models.

config_start = content.find('export const MODEL_CONFIG: Record<string, ModelConfig> = {')
config_end = content.find('};', config_start) + 2

new_config = """export const MODEL_CONFIG: Record<string, ModelConfig> = {
    'glm-5.2': {
        label: 'GLM-5.2',
        shortLabel: 'GLM 5.2',
        protectedKey: 'glm',
        Icon: ZIcon,
        i18nKey: 'proxy.model.glm_5_2',
        i18nDescKey: 'proxy.model.glm_5_2',
        group: 'GLM',
        tags: ['pro'],
    },
    'glm-5-turbo': {
        label: 'GLM-5-Turbo',
        shortLabel: 'GLM 5 Turbo',
        protectedKey: 'glm',
        Icon: ZIcon,
        i18nKey: 'proxy.model.glm_5_turbo',
        i18nDescKey: 'proxy.model.glm_5_turbo',
        group: 'GLM',
        tags: ['pro'],
    }
};"""

content = content[:config_start] + new_config + content[config_end:]

with open('src/config/modelConfig.ts', 'w') as f:
    f.write(content)

print("Removed extra models from modelConfig.ts")
