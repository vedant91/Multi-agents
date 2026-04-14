"""
Diagnostic script to understand what the OCR text looks like around tax/current assets/liabilities sections.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from utils.pdf_extractor import extract_text_from_pdf

PDF_DIR = r"C:\Users\Vedant\OneDrive\Desktop\multi-3"

# Extract P&L and Balance Sheet text
pl_path = os.path.join(PDF_DIR, "Profit & Loss.pdf")
bs_path = os.path.join(PDF_DIR, "Balance Sheet.pdf")

print("=" * 70)
print("EXTRACTING P&L TEXT...")
print("=" * 70)
pl_text = extract_text_from_pdf(pl_path)

print("\n" + "=" * 70)
print("EXTRACTING BS TEXT...")
print("=" * 70)
bs_text = extract_text_from_pdf(bs_path)

# Search for tax-related keywords in P&L text
print("\n" + "=" * 70)
print("TAX SEARCH IN P&L TEXT")
print("=" * 70)

tax_keywords = [
    "Current Tax", "current tax", "Deferred Tax", "deferred tax",
    "Tax expense", "tax expense", "Tax Expense",
    "Income tax", "income tax",
    "Less: Tax", "less: tax",
    "Provision for tax", "provision for tax",
    "1006.99", "1,006.99",  # Actual current tax FY25
    "513.36", "189.20", "12.34",  # Other tax values
    "1,196.19", "1196.19",  # Total tax FY25
    "525.70",  # Total tax FY24
    "220.23", "2037.34", "2,037.34",  # Wrong tax values being extracted
]

for kw in tax_keywords:
    idx = pl_text.lower().find(kw.lower())
    if idx >= 0:
        start = max(0, idx - 50)
        end = min(len(pl_text), idx + 200)
        snippet = pl_text[start:end].replace("\n", " | ")
        print(f"\n[FOUND] '{kw}' at pos {idx}:")
        print(f"  ...{snippet}...")
    else:
        print(f"[NOT FOUND] '{kw}'")

# Search for total current assets / liabilities in BS text
print("\n" + "=" * 70)
print("CURRENT ASSETS/LIABILITIES SEARCH IN BS TEXT")
print("=" * 70)

ca_keywords = [
    "Total current assets", "Total Current Assets", "TOTAL CURRENT ASSETS",
    "Total current liabilities", "Total Current Liabilities", "TOTAL CURRENT LIABILITIES",
    "17756", "17,756", "11971", "11,971",
    "Short term provisions", "short term provisions",
    "Other current liabilities", "other current liabilities",
    "Short term loans", "short term loans",
    "Other current assets", "other current assets",
    "1503.90", "1,503.90", "445.83",
    "4435.76", "4,435.76", "1989.69", "1,989.69",
]

for kw in ca_keywords:
    idx = bs_text.lower().find(kw.lower())
    if idx >= 0:
        start = max(0, idx - 50)
        end = min(len(bs_text), idx + 200)
        snippet = bs_text[start:end].replace("\n", " | ")
        print(f"\n[FOUND] '{kw}' at pos {idx}:")
        print(f"  ...{snippet}...")
    else:
        print(f"[NOT FOUND] '{kw}'")

# Dump the full P&L text to find tax section
print("\n" + "=" * 70)
print("FULL P&L TEXT - SEARCHING FOR TAX SECTION")
print("=" * 70)

# Show text around "tax" mentions
import re
for m in re.finditer(r'(?i)tax', pl_text):
    start = max(0, m.start() - 80)
    end = min(len(pl_text), m.end() + 200)
    snippet = pl_text[start:end].replace("\n", " | ")
    print(f"\n[TAX at {m.start()}]: ...{snippet}...")

# Show text around "1006" or "513" (the actual tax numbers)
print("\n" + "=" * 70)
print("SEARCHING FOR ACTUAL TAX VALUES IN ALL TEXT")
print("=" * 70)
for val in ["1006", "513", "189", "12.34", "1196", "525"]:
    for label, text in [("P&L", pl_text), ("BS", bs_text)]:
        idx = text.find(val)
        if idx >= 0:
            start = max(0, idx - 80)
            end = min(len(text), idx + 150)
            snippet = text[start:end].replace("\n", " | ")
            print(f"\n[{label}] '{val}' at pos {idx}: ...{snippet}...")
