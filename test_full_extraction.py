"""
Full extraction test — verifies all 5 PDFs extract financial data correctly.
Run with: python test_full_extraction.py
Output is saved to extraction_test_output.txt
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from utils.pdf_extractor import extract_text_from_pdf

PDF_DIR = r"C:\Users\Vedant\OneDrive\Desktop\multi-3"

PDFS = [
    "Balance Sheet.pdf",
    "Profit & Loss.pdf",
    "Wohr_Balance Sheet_2025.pdf",
    "8_IFCR Report Auditors Report_2025.pdf",
    "10_Notes to Accounts Final_2025.pdf",
]

# Key financial terms to search for
FINANCIAL_KEYWORDS = [
    "Revenue from operations", "Total Revenue", "Total Income",
    "Profit", "PAT", "Finance cost", "Depreciation",
    "Share capital", "Reserves", "Borrowings",
    "Current Assets", "Current Liabilities",
    "Trade Receiv", "Inventory", "Cash flow",
    "In Lakhs", "in Lakhs", "Lakhs",
    "31.03.2025", "31.03.2024", "31.03.2023",
]

output_lines = []

def log(line=""):
    print(line)
    output_lines.append(line)

log("=" * 70)
log("FULL EXTRACTION TEST — ALL 5 PDFs")
log("=" * 70)

all_text = {}

for pdf_name in PDFS:
    pdf_path = os.path.join(PDF_DIR, pdf_name)
    if not os.path.exists(pdf_path):
        log(f"\n[MISSING] {pdf_name}")
        continue

    log(f"\n{'=' * 70}")
    log(f"PDF: {pdf_name}")
    log("=" * 70)

    text = extract_text_from_pdf(pdf_path)
    all_text[pdf_name] = text
    char_count = len(text.strip())

    log(f"Chars extracted: {char_count:,}")

    if char_count < 100:
        log("  [FAIL] Very little text extracted!")
        continue

    # Check for financial keywords
    log("\nFinancial terms found:")
    found_any = False
    for kw in FINANCIAL_KEYWORDS:
        idx = text.lower().find(kw.lower())
        if idx >= 0:
            snippet = text[max(0, idx - 5):idx + 80].replace("\n", " ").strip()
            log(f"  [OK] '{kw}': ...{snippet}...")
            found_any = True

    if not found_any:
        log("  [WARN] No financial keywords found — possible OCR quality issue")

    # Print first 1500 chars of extracted content
    log(f"\nFirst 1500 chars of extracted text:")
    log("-" * 40)
    log(text[:1500].replace("\n", "\n  "))

log("\n" + "=" * 70)
log("TEST COMPLETE")
log("=" * 70)

# Save to file
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extraction_test_output.txt")
with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"\n[SAVED] Full output written to: {output_path}")
