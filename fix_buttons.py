import re

def patch_file(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Find the IDE button
        ide_pattern = r'<button[^>]*onClick=\{\(e\) => \{ e\.stopPropagation\(\); onSwitch\(\'ide\'\); \}\}[^>]*>[\s\S]*?</button>'
        content = re.sub(ide_pattern, '', content)
        
        # Find the AGY button
        agy_pattern = r'<button[^>]*onClick=\{\(e\) => \{ e\.stopPropagation\(\); onSwitch\(\'agy\'\); \}\}[^>]*>[\s\S]*?</button>'
        content = re.sub(agy_pattern, '', content)
        
        # Change 'switch_to_classic' to 'switch_session'
        content = content.replace("t('accounts.switch_to_classic', '切换到 Antigravity (经典版)')", "t('accounts.switch_session', 'Переключить сессию в Z Code')")
        content = content.replace("t('accounts.switch_to_classic', 'Switch to Antigravity (Classic)')", "t('accounts.switch_session', 'Switch session in Z Code')")
        
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Patched {filepath}")
    except Exception as e:
        print(f"Error patching {filepath}: {e}")

patch_file('src/components/accounts/AccountTable.tsx')
patch_file('src/components/accounts/AccountCard.tsx')
