import os
import re

base_dir = r"c:\Users\nehau\Downloads\urbanmeal-ai-data-engineering-end-to-end-project-main\urbanmeal-ai-data-engineering-end-to-end-project-main"

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return # Skip binary or non-utf8 files
    
    # Case-sensitive replacements
    new_content = content.replace("URBANMEAL", "URBANMEAL")
    new_content = new_content.replace("UrbanMeal", "UrbanMeal")
    new_content = new_content.replace("urbanmeal", "urbanmeal")
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, dirs, files in os.walk(base_dir):
    # Ignore .git or similar if any
    if '.git' in root:
        continue
    for file in files:
        if file.endswith(('.py', '.sql', '.md', '.yml', '.yaml', '.env', '.json')):
            filepath = os.path.join(root, file)
            replace_in_file(filepath)

# Rename files
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if "urbanmeal" in file.lower():
            old_path = os.path.join(root, file)
            new_file = file.replace("urbanmeal", "urbanmeal").replace("UrbanMeal", "UrbanMeal").replace("URBANMEAL", "URBANMEAL")
            new_path = os.path.join(root, new_file)
            os.rename(old_path, new_path)
            print(f"Renamed {old_path} to {new_path}")

# Rename directories (need to do bottom up or careful)
for root, dirs, files in os.walk(base_dir, topdown=False):
    for dir_name in dirs:
        if "urbanmeal" in dir_name.lower():
            old_path = os.path.join(root, dir_name)
            new_dir = dir_name.replace("urbanmeal", "urbanmeal").replace("UrbanMeal", "UrbanMeal").replace("URBANMEAL", "URBANMEAL")
            new_path = os.path.join(root, new_dir)
            os.rename(old_path, new_path)
            print(f"Renamed {old_path} to {new_path}")
