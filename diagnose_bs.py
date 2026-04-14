"""Check exact OCR text around problematic Balance Sheet fields."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PDF_DIR = r"C:\Users\Vedant\OneDrive\Desktop\multi-3"
from utils.pdf_extractor import extract_text_from_pdf

bs_text = extract_text_from_pdf(os.path.join(PDF_DIR, "Balance Sheet.pdf"))

# Print snippets around key terms
TERMS = [
    "Total Current Assets", "Total Current Liabilities",
    "Current Assets", "Current Liabilities",
    "Capital work", "CWIP", "Capital Work",
    "Total current",
    "Trade receivables",
    "21367", "16812",
]

seen = set()
for term in TERMS:
    idx = bs_text.lower().find(term.lower())
    if idx >= 0:
        snippet = bs_text[max(0, idx-20):idx+200].replace('\n', ' ')
        key = snippet[:30]
        if key not in seen:
            seen.add(key)
            print(f"[{idx:5d}] '{term}': ...{snippet}...")
    else:
        print(f"[  N/A] '{term}': NOT FOUND")
