import os
import re

def strip_emojis(text):
    # This regex catches most miscellaneous symbols and pictographs, emoticons, etc.
    emoji_pattern = re.compile(
        r'['
        r'\U0001f600-\U0001f64f'  # emoticons
        r'\U0001f300-\U0001f5ff'  # symbols & pictographs
        r'\U0001f680-\U0001f6ff'  # transport & map symbols
        r'\U0001f1e0-\U0001f1ff'  # flags (iOS)
        r'\u2600-\u26ff'         # misc symbols
        r'\u2700-\u27bf'         # dingbats
        r'\u2B50'                # star
        r']+',
        re.UNICODE)
    return emoji_pattern.sub('', text)

def process_directory(directory):
    count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    new_content = strip_emojis(content)
                    
                    if new_content != content:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Stripped emojis from {path}")
                        count += 1
                except Exception as e:
                    print(f"Error processing {path}: {e}")
                    
    print(f"Total files updated: {count}")

if __name__ == '__main__':
    process_directory('.')
