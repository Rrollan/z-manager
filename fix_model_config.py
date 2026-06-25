with open('src/config/modelConfig.ts', 'r') as f:
    content = f.read()

# Replace Icon: Gemini.Color with Icon: ZIcon, and define ZIcon at the top
import re

if "const ZIcon = " not in content:
    # insert at the top after imports
    idx = content.find("import ")
    last_import = content.rfind("import ", 0, content.find("export interface"))
    end_of_imports = content.find("\n", last_import) + 1
    
    z_icon = """
import LogoIcon from '../../src-tauri/icons/icon.png';
const ZIcon = ({ size = 24, className = '' }) => (
    <img src={LogoIcon} width={size} height={size} className={className} alt="Z Code" />
);
"""
    content = content[:end_of_imports] + z_icon + content[end_of_imports:]

# Replace Gemini.Color, Claude.Color, Openai.Color with ZIcon
content = re.sub(r'Icon:\s*(Gemini|Claude|Openai)\.Color', 'Icon: ZIcon', content)

with open('src/config/modelConfig.ts', 'w') as f:
    f.write(content)

print("Patched modelConfig.ts")
