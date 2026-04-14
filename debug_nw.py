import re
from utils.pdf_extractor import extract_text_from_pdf

text = extract_text_from_pdf(r'c:\Users\Vedant\OneDrive\Desktop\multi-3\Annual Report FY 2024-25.pdf')

for m in re.finditer(r'(?i)standalone\s+metrics', text):
    candidate = text[m.start(): m.start() + 5000]
    if 'Revenue' not in candidate:
        continue

    nw = candidate.find('Networth')
    bor = candidate.find('Borrowings')
    print(f"Networth at {nw}, Borrowings at {bor}")

    # Networth section (bounded by next label)
    nw_section = candidate[nw:bor] if bor > nw else candidate[nw:nw+300]
    print("--- Networth section ---")
    for line in nw_section.split('\n'):
        if line.strip():
            print(f"  {line.strip()}")

    # Where is 189,392?
    idx_189 = candidate.find('189,392')
    print(f"\n189,392 at pos {idx_189} (Networth={nw}, Borrowings={bor})")
    if idx_189 >= 0:
        print(f"Context: {candidate[idx_189-30:idx_189+30]}")
    break
