import os
import re

ROOT_DIR = "/Users/punyasurana/Documents/IITVIVRITI/Multi-agents"
IGNORE_DIRS = {".git", "node_modules", "venv", "__pycache__", ".ipynb_checkpoints", "build", "dist", ".vite", ".antigravity"}
IGNORE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".pyc", ".docx", ".DS_Store", ".sqlite3"}

def process_content(content):
    content = content.replace("QUANTISENSE", "QUANTISENSE")
    content = content.replace("Quantisense", "Quantisense")
    content = content.replace("quantisense", "quantisense")
    return content

# 1. First rename file contents
for root, dirs, files in os.walk(ROOT_DIR, topdown=True):
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
    for file in files:
        if any(file.endswith(ext) for ext in IGNORE_EXTS):
            continue
        file_path = os.path.join(root, file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            new_content = process_content(content)
            if content != new_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated content in {file_path}")
        except Exception as e:
            pass # ignore unreadable/binary files

# 2. Rename files and directories bottom up
for root, dirs, files in os.walk(ROOT_DIR, topdown=False):
    # Filter out ignored dirs so we don't traverse into or rename them inside
    # Actually topdown=False doesn't let us modify dirs in-place to skip traversal, it visits everything
    # So we'll just skip if any part of the path is in IGNORE_DIRS
    if any(ignore_d in root.split(os.sep) for ignore_d in IGNORE_DIRS):
        continue

    for name in files + dirs:
        if "quantisense" in name.lower():
            old_path = os.path.join(root, name)
            new_name = name.replace("QUANTISENSE", "QUANTISENSE").replace("Quantisense", "Quantisense").replace("quantisense", "quantisense")
            new_path = os.path.join(root, new_name)
            os.rename(old_path, new_path)
            print(f"Renamed {os.path.relpath(old_path, ROOT_DIR)} to {new_name}")
