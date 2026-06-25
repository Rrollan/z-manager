import re

def patch_file(filepath, replacements):
    with open(filepath, 'r') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(filepath, 'w') as f:
        f.write(content)

# 1. Fix AccountRow.tsx redeclaration
with open('src/components/accounts/AccountRow.tsx', 'r') as f:
    content = f.read()

# There are two `const glm52Model = ` declarations because my earlier python script injected the second one after `const { t } = useTranslation();`, 
# but my previous script `fix_ui_models.py` had already renamed `geminiProModel` to `glm5hModel`, then my second script renamed `glm5hModel` to `glm52Model`.
# Let's just remove the first one if we can find it.
first_decl = content.find("const glm52Model =")
second_decl = content.find("const glm52Model =", first_decl + 1)
if second_decl != -1:
    # Remove the FIRST declaration which is likely the old one:
    # const glm52Model = account.quota?.models...
    end_of_first = content.find(";", first_decl)
    content = content[:first_decl] + content[end_of_first+1:]
    with open('src/components/accounts/AccountRow.tsx', 'w') as f:
        f.write(content)

# 2. Fix AccountCard.tsx and AccountTable.tsx unused imports
def remove_imports(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    content = content.replace(", Repeat2", "")
    content = content.replace(", Terminal", "")
    content = content.replace("Repeat2,", "")
    content = content.replace("Terminal,", "")
    content = content.replace("Repeat2", "")
    content = content.replace("Terminal", "")
    with open(filepath, 'w') as f:
        f.write(content)

remove_imports('src/components/accounts/AccountCard.tsx')
remove_imports('src/components/accounts/AccountTable.tsx')

# 3. Fix unused imports in modelConfig.ts
with open('src/config/modelConfig.ts', 'r') as f:
    content = f.read()
content = content.replace("import { Gemini, Claude } from '@lobehub/icons';", "")
with open('src/config/modelConfig.ts', 'w') as f:
    f.write(content)

print("Fixed TS errors")
