with open('src/config/modelConfig.ts', 'r') as f:
    content = f.read()

import re
# Replace all models in MODEL_CONFIG with the actual ones
# Just overwrite the MODEL_CONFIG dict completely
config_start = content.find('export const MODEL_CONFIG: Record<string, ModelConfig> = {')
config_end = content.find('};', config_start) + 2

new_config = """export const MODEL_CONFIG: Record<string, ModelConfig> = {
    'glm-5.2 (5h)': {
        label: 'GLM 5.2',
        shortLabel: 'GLM 5.2',
        protectedKey: 'glm',
        Icon: Gemini.Color,
        i18nKey: 'proxy.model.glm_5_2',
        i18nDescKey: 'proxy.model.glm_5_2',
        group: 'GLM',
        tags: ['pro'],
    },
    'glm-5.2': {
        label: 'GLM 5.2',
        shortLabel: 'GLM 5.2',
        protectedKey: 'glm',
        Icon: Gemini.Color,
        i18nKey: 'proxy.model.glm_5_2',
        i18nDescKey: 'proxy.model.glm_5_2',
        group: 'GLM',
        tags: ['pro'],
    },
    'claude-3-5-sonnet': {
        label: 'Claude 3.5 Sonnet',
        shortLabel: 'Claude 3.5',
        protectedKey: 'claude',
        Icon: Claude.Color,
        i18nKey: 'proxy.model.claude_sonnet',
        i18nDescKey: 'proxy.model.claude_sonnet',
        group: 'Claude',
        tags: ['sonnet'],
    },
    'gpt-4o': {
        label: 'GPT-4o',
        shortLabel: 'GPT-4o',
        protectedKey: 'openai',
        Icon: Gemini.Color, // Use a placeholder icon if Openai not imported
        i18nKey: 'proxy.model.gpt_4o',
        i18nDescKey: 'proxy.model.gpt_4o',
        group: 'OpenAI',
        tags: ['pro'],
    }
};"""

content = content[:config_start] + new_config + content[config_end:]

with open('src/config/modelConfig.ts', 'w') as f:
    f.write(content)
print("Config fixed")
