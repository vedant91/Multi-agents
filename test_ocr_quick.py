"""
Quick test: Extract text from the Balance Sheet PDF using Gemini OCR.
Run with: python test_ocr_quick.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("PYTHONPATH", os.path.dirname(os.path.abspath(__file__)))

from utils.pdf_extractor import extract_text_from_pdf

# Test on the two critical scanned PDFs
test_pdfs = [
    r"C:\Users\Vedant\OneDrive\Desktop\multi-3\Balance Sheet.pdf",
    r"C:\Users\Vedant\OneDrive\Desktop\multi-3\Profit & Loss.pdf",
]

for pdf_path in test_pdfs:
    if not os.path.exists(pdf_path):
        print(f"NOT FOUND: {pdf_path}")
        continue

    print(f"\n{'='*60}")
    print(f"Testing: {os.path.basename(pdf_path)}")
    print("="*60)

    text = extract_text_from_pdf(pdf_path)

    print(f"\nTotal extracted chars: {len(text):,}")
    print("\n--- FIRST 2000 CHARS OF EXTRACTED TEXT ---")
    print(text[:2000])
    print("\n--- LAST 1000 CHARS ---")
    print(text[-1000:] if len(text) > 1000 else text)
    print("="*60)
