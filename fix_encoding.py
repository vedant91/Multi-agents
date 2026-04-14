"""Fix all non-ASCII characters in document_parser.py"""
with open('agents/document_parser.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    '\u2192': '->',
    '\u2014': '--',
    '\u2013': '-',
    '\u2500': '-',
    '\u2018': "'",
    '\u2019': "'",
    '\u201c': '"',
    '\u201d': '"',
    '\u2022': '*',
    '\u2026': '...',
}
for bad, good in replacements.items():
    content = content.replace(bad, good)

remaining = [c for c in content if ord(c) > 127]
print(f'Remaining non-ASCII after fix: {len(remaining)}')
if remaining:
    uniq = set(remaining)
    print(f'  Still problematic: {[hex(ord(c)) for c in uniq]}')

with open('agents/document_parser.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Saved document_parser.py with ASCII-safe characters.')
