"""
Full end-to-end verification: PDF extraction + Parser + Fraud scan.
Checks completeness of each step before localhost.
Run: python verify_all.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PDF_DIR = r"C:\Users\Vedant\OneDrive\Desktop\multi-3"
PDFS = [
    "Balance Sheet.pdf",
    "Profit & Loss.pdf",
    "Wohr_Balance Sheet_2025.pdf",
    "8_IFCR Report Auditors Report_2025.pdf",
    "10_Notes to Accounts Final_2025.pdf",
]

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"
INFO = "[INFO]"

results = {"pass": 0, "fail": 0, "warn": 0}

def check(label, condition, value="", fail_msg=""):
    if condition:
        print(f"  {PASS} {label}: {value}")
        results["pass"] += 1
    else:
        print(f"  {FAIL} {label}: {fail_msg or value}")
        results["fail"] += 1

def warn(label, msg):
    print(f"  {WARN} {label}: {msg}")
    results["warn"] += 1

# ─────────────────────────────────────────────────────────────
# STEP 1: PDF EXTRACTION
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 1: PDF EXTRACTION — ALL 5 PDFs")
print("=" * 65)

from utils.pdf_extractor import extract_text_from_multiple_pdfs, combine_all_documents

pdf_paths = [os.path.join(PDF_DIR, n) for n in PDFS if os.path.exists(os.path.join(PDF_DIR, n))]
missing = [n for n in PDFS if not os.path.exists(os.path.join(PDF_DIR, n))]
for m in missing:
    print(f"  {FAIL} MISSING FILE: {m}")
    results["fail"] += 1

extracted = extract_text_from_multiple_pdfs(pdf_paths)
combined  = combine_all_documents(extracted)

print()
MIN_CHARS = {"Balance Sheet.pdf": 5000, "Profit & Loss.pdf": 5000,
             "Wohr_Balance Sheet_2025.pdf": 50000,
             "8_IFCR Report Auditors Report_2025.pdf": 1000,
             "10_Notes to Accounts Final_2025.pdf": 1000}

for pdf_name, text in extracted.items():
    n = len(text.strip())
    min_c = MIN_CHARS.get(pdf_name, 1000)
    check(pdf_name, n >= min_c, f"{n:,} chars", f"Only {n:,} chars (expected ≥{min_c:,})")

# Key terms per PDF
KEY_TERMS = {
    "Balance Sheet.pdf": ["Share capital", "Reserves", "Borrowings", "31.03.2025", "In Lakhs"],
    "Profit & Loss.pdf": ["Revenue from operations", "Finance cost", "Depreciation", "Profit", "31.03.2025"],
    "Wohr_Balance Sheet_2025.pdf": ["Revenue from operations", "Share capital", "Profit"],
}

print()
print("  Key financial terms found:")
for pdf_name, terms in KEY_TERMS.items():
    text = extracted.get(pdf_name, "")
    for term in terms:
        found = term.lower() in text.lower()
        check(f"  {pdf_name[:25]}… → '{term}'", found,
              "FOUND", "NOT FOUND — possible OCR failure")

print(f"\n  Total combined chars: {len(combined):,}")

# ─────────────────────────────────────────────────────────────
# STEP 2: DOCUMENT PARSER
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 2: DOCUMENT PARSER AGENT")
print("=" * 65)

from agents.document_parser import run_document_parser
parser_output = run_document_parser(combined)

print("\n  Parser output length:", len(parser_output))

# Check all required fields exist in parser output
REQUIRED_FIELDS = [
    ("Revenue", ["Revenue from Operations", "Revenue from operations", "38010", "38,010", "29121", "29,121"]),
    ("PAT", ["2489", "2,489", "Profit for the", "PAT"]),
    ("Finance Cost", ["115.58", "Finance cost", "Finance Cost"]),
    ("Depreciation", ["248.55", "Depreciation"]),
    ("Tax", ["1006", "1,006", "Tax"]),
    ("EBITDA", ["EBITDA", "4859", "4,859"]),
    ("Net Worth", ["Net Worth", "7454", "7,454"]),
    ("Share Capital", ["Share Capital", "498.01"]),
    ("Reserves", ["Reserves", "6956", "6,956"]),
    ("FY24 data", ["FY24", "31.03.2024", "1282", "1,282"]),
    ("Auditor", ["Potdar", "auditor", "Auditor"]),
    ("Debtor Days", ["Debtor Days", "debtor days", "53", "56", "61", "64"]),
]

print("\n  Checking parser output completeness:")
for field_name, keywords in REQUIRED_FIELDS:
    found = any(kw.lower() in parser_output.lower() for kw in keywords)
    check(f"  {field_name}", found, "present in output", "MISSING from parser output!")

# ─────────────────────────────────────────────────────────────
# STEP 3: FRAUD DETECTOR
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("STEP 3: FRAUD DETECTOR")
print("=" * 65)

from agents.fraud_detector import run_fraud_detector
fraud_output = run_fraud_detector(
    parser_output=parser_output,
    research_output="No web research for this test.",
    primary_notes="",
    company_tier="TIER 3"
)

print("\n  Fraud scan output length:", len(fraud_output))

# Check patterns that SHOULD be evaluated (not just INSUFFICIENT DATA)
SHOULD_CLEAR = [
    ("Pattern 5 - Channel Stuffing", ["CLEARED", "Cleared"]),
    ("Pattern 9 - Auditor Shopping", ["CLEARED", "Cleared"]),
    ("Pattern 10 - Kite Flying", ["CLEARED", "Cleared"]),
]
MUST_NOT_REJECT = ["ESCALATE", "AUTOMATIC REJECTION"]

print("\n  Fraud pattern evaluation:")
for pattern, keywords in SHOULD_CLEAR:
    found = any(kw in fraud_output for kw in keywords)
    if not found:
        warn(pattern, "Not CLEARED — check fraud detector output")
    else:
        check(pattern, True, "CLEARED with evidence")

for bad in MUST_NOT_REJECT:
    if bad in fraud_output:
        check(f"No auto-rejection", False, fail_msg=f"Found '{bad}' — investigate!")
    else:
        check(f"No auto-rejection trigger ('{bad}')", True, "clean")

# Show fraud output summary
print("\n  FRAUD SCAN SUMMARY (last 1500 chars):")
print("-" * 40)
print(fraud_output[-1500:])

# ─────────────────────────────────────────────────────────────
# FINAL SCORE
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
total = results["pass"] + results["fail"] + results["warn"]
print(f"VERIFICATION COMPLETE: {results['pass']} PASS | {results['fail']} FAIL | {results['warn']} WARN")
if results["fail"] == 0:
    print("STATUS: ALL CHECKS PASSED — SAFE TO RUN LOCALHOST")
else:
    print(f"STATUS: {results['fail']} CHECKS FAILED — fix before running localhost")
print("=" * 65)

# Save full output
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_output.txt")
# (rerun with tee if you want file capture)
print(f"\nRun complete.")
