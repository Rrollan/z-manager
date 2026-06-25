import os

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Find and remove claudeGroupNames declaration
    lines = content.split('\n')
    new_lines = []
    skip = False
    for line in lines:
        if 'const claudeGroupNames =' in line:
            skip = True
        if skip and '];' in line:
            skip = False
            continue
        if not skip:
            new_lines.append(line)
            
    with open(filepath, 'w') as f:
        f.write('\n'.join(new_lines))

src_dir = "src/components"
for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith(".tsx"):
            process_file(os.path.join(root, file))

print("Fixed unused variable")
