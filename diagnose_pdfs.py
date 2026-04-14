"""
Diagnostic: Test what pdfplumber actually extracts from each PDF.
Run with: python diagnose_pdfs.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pdfplumber
import glob

# Find all PDFs
pdf_files = glob.glob(os.path.join(os.path.dirname(__file__), "**", "*.pdf"), recursive=True)
# Also check parent dirs
pdf_files += glob.glob(r"C:\Users\Vedant\OneDrive\Desktop\multi-3\**\*.pdf", recursive=True)
pdf_files = list(set(pdf_files))

print(f"Found {len(pdf_files)} PDFs:\n")
for p in pdf_files:
    print(f"  {p}")

print("\n" + "="*80)

for pdf_path in pdf_files:
    print(f"\n{'='*80}")
    print(f"PDF: {os.path.basename(pdf_path)}")
    print(f"Path: {pdf_path}")
    print("="*80)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"Total pages: {total_pages}")
            total_chars = 0

            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                total_chars += len(text.strip())
                scanned = "SCANNED" if len(text.strip()) < 50 else "TEXT"
                print(f"\n  Page {i+1} [{scanned}]: {len(text.strip())} chars")
                if text.strip():
                    # Print first 600 chars as preview
                    preview = text.strip()[:600].replace('\n', ' | ')
                    print(f"  Preview: {preview}")
                else:
                    print(f"  NO TEXT EXTRACTED (image-based / scanned page)")

            print(f"\n  TOTAL CHARS from pdfplumber: {total_chars}")
            print(f"  STATUS: {'DIGITAL PDF (text-based)' if total_chars > 200 else 'SCANNED PDF (needs OCR)'}")

    except Exception as e:
        print(f"  ERROR: {e}")

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE")
