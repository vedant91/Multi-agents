"""
Pipeline test: Extract PDFs -> Document Parser -> Fraud Detector
Run: python test_pipeline.py
Saves output to: pipeline_test_output.txt
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

OUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline_test_output.txt")

lines = []
def log(x=""): print(x); lines.append(str(x))

# ── STEP 1: Extract PDFs ──────────────────────────────────────────────────────
log("=" * 60)
log("STEP 1: PDF EXTRACTION")
log("=" * 60)

from utils.pdf_extractor import extract_text_from_multiple_pdfs, combine_all_documents

pdf_paths = []
for name in PDFS:
    p = os.path.join(PDF_DIR, name)
    if os.path.exists(p):
        pdf_paths.append(p)
    else:
        log(f"[MISSING] {name}")

extracted = extract_text_from_multiple_pdfs(pdf_paths)
combined  = combine_all_documents(extracted)

log(f"\nTotal chars extracted: {len(combined):,}")
for name, text in extracted.items():
    log(f"  {name}: {len(text):,} chars")

# ── STEP 2: Document Parser ───────────────────────────────────────────────────
log("\n" + "=" * 60)
log("STEP 2: DOCUMENT PARSER AGENT")
log("=" * 60)

from agents.document_parser import run_document_parser
parser_output = run_document_parser(combined, extracted_docs=extracted)

log("\nPARSER OUTPUT:")
log("-" * 40)
log(parser_output)



# ── STEP 3: Fraud Detector ────────────────────────────────────────────────────
log("\n" + "=" * 60)
log("STEP 3: FRAUD DETECTOR AGENT")
log("=" * 60)

from agents.fraud_detector import run_fraud_detector
fraud_output = run_fraud_detector(
    parser_output=parser_output,
    research_output="No web research available for this test run.",
    primary_notes="",
    company_tier="TIER 3"
)

log("\nFRAUD DETECTOR OUTPUT:")
log("-" * 40)
log(fraud_output)

# ── STEP 4: Stress Test ───────────────────────────────────────────────────────
log("\n" + "=" * 60)
log("STEP 4: STRESS TEST AGENT")
log("=" * 60)

from agents.stress_test_agent import run_stress_test

loan_details = {
    "company_name": "Test Company Ltd",
    "sector": "textiles",
    "loan_amount": 200000000, # 20 Cr in raw rupees to test conversion
    "loan_purpose": "Working Capital",
    "loan_tenure_months": 84
}

stress_output = run_stress_test(
    parser_output=parser_output,
    chairman_output="Provisional approval pending stress test",
    loan_details=loan_details
)

log("\nSTRESS TEST OUTPUT:")
log("-" * 40)
log(stress_output)


# ── SAVE ─────────────────────────────────────────────────────────────────────
with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

log(f"\n[SAVED] {OUT_FILE}")
