import os
import re

def remove_emojis_from_print(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        return False

    # Regex to find print("..." or print(f"..." and replace non-ascii chars within strings
    # A simpler approach: replace any non-ascii character in the file with its closest english meaning or remove it
    
    replacements = {
        '[SUCCESS]': '[SUCCESS]',
        '[FAIL]': '[FAIL]',
        '[WARN]': '[WARN]',
        '[SEARCH]': '[SEARCH]',
        '[INFO]': '[INFO]',
        '[TIME]': '[TIME]',
        '[ROCKET]': '[ROCKET]',
        '[SCALE]': '[SCALE]',
        '[CHART]': '[CHART]',
        '[DOC]': '[DOC]',
        '[TREND]': '[TREND]',
        '[DOWN]': '[DOWN]',
        '[IDEA]': '[IDEA]',
        '[STOP]': '[STOP]',
        # A catch-all for other common emojis can be added, or we can just strip them
    }
    
    modified = False
    new_content = content
    for emoji, text in replacements.items():
        if emoji in new_content:
            new_content = new_content.replace(emoji, text)
            modified = True
            
    # Also strip any other character outside basic ASCII to be fully safe for cp1252
    # but only if we already knew there were emojis or just apply globally
    # Actually, the charmap issue is specifically about these emojis in print statements.
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def process_directory(directory):
    count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                if remove_emojis_from_print(path):
                    print(f"Updated {path}")
                    count += 1
    print(f"Total files updated: {count}")

if __name__ == '__main__':
    process_directory('.')
