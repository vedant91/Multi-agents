"""Diagnose exactly where key P&L numbers appear in OCR text."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PDF_DIR = r"C:\Users\Vedant\OneDrive\Desktop\multi-3"

from utils.pdf_extractor import extract_text_from_pdf

pl_text = extract_text_from_pdf(os.path.join(PDF_DIR, "Profit & Loss.pdf"))
bs_text = extract_text_from_pdf(os.path.join(PDF_DIR, "Balance Sheet.pdf"))

print(f"P&L total chars: {len(pl_text):,}")
print(f"BS total chars: {len(bs_text):,}")

KEYWORDS = {
    "P&L": {
        "text": pl_text,
        "terms": [
            "Revenue from operations",
            "TOTAL INCOME",
            "Finance cost",
            "Depreciation",
            "Tax",
            "Profit for the"
        ]
    },
    "BS": {
        "text": bs_text,
        "terms": [
            "Share capital",
            "Reserves",
            "Borrowings",
            "Trade receivables",
            "Inventories",
            "Cash and"
        ]
    }
}

for doc_name, info in KEYWORDS.items():
    text = info["text"]
    print(f"\n{'='*60}")
    print(f"Document: {doc_name}")
    print(f"{'='*60}")
    for term in info["terms"]:
        idx = text.lower().find(term.lower())
        if idx >= 0:
            snippet = text[idx:idx+120].replace('\n', ' ').strip()
            print(f"\n  [{idx:6d}] '{term}':")
            print(f"           {snippet}")
        else:
            print(f"\n  [  N/A ] '{term}': NOT FOUND")
