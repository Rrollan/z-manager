import os
import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # If there's `const claudeModel = ...` and another `const claudeModel = ...`,
    # the first one came from `geminiFlashModel`. I will change the first one to `claudeModel` and delete the second one, or just rename them properly.
    # Actually, the original code had:
    # const geminiFlashModel = account...
    # const geminiImageModel = account...
    # const claudeModel = account...
    # So I replaced `geminiFlashModel` with `claudeModel` everywhere, which caused conflicts with the original `claudeModel`.
    
    # Let's just fix it by manually removing the second declaration if it exists.
    # The second one looks like:
    # const claudeModel = account?.quota?.models.find(m => m.name.toLowerCase().includes('claude-3-5-sonnet'));
    # And the first one is the same!
    
    # Let's find occurrences of `const claudeModel = `
    parts = content.split('const claudeModel =')
    if len(parts) > 2:
        print(f"Fixing redeclaration in {filepath}")
        # There's more than one `const claudeModel =`
        # Let's just replace the second `const claudeModel = ` with `const claudeModel2 = ` or just remove it if it's identical
        
        # Actually, let's just use `sed` to replace the second one with a comment.
        # But maybe they are used? I replaced `geminiFlashModel` with `claudeModel`, so it uses `claudeModel`.
        # I replaced `claudeModel` with `claudeModel` (no change in usage).
        # So I just need to remove the duplicate definition!
        
        # The duplicate definition usually looks exactly like:
        # const claudeModel = account.quota?.models.find(m => m.name.toLowerCase().includes('claude-3-5-sonnet'));
        # OR const claudeModel = account?.quota?.models...
        
        # Let's just remove the SECOND one.
        first_idx = content.find('const claudeModel =')
        second_idx = content.find('const claudeModel =', first_idx + 1)
        
        # Find the end of the statement for the second one
        end_idx = content.find(';', second_idx)
        if end_idx != -1:
            content = content[:second_idx] + content[end_idx+1:]
        
        with open(filepath, 'w') as f:
            f.write(content)

src_dir = "src/components"
for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith(".tsx"):
            process_file(os.path.join(root, file))

print("Fixed redeclarations")
