"""
Final Verification Script for WOHR Company Data Extraction.
Runs the document parser on all 5 PDFs and prints the final report.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from utils.pdf_extractor import extract_text_from_multiple_pdfs
from agents.document_parser import run_document_parser

PDF_DIR = r"C:\Users\Vedant\OneDrive\Desktop\multi-3"

PDFS = [
    os.path.join(PDF_DIR, "Balance Sheet.pdf"),
    os.path.join(PDF_DIR, "Profit & Loss.pdf"),
    os.path.join(PDF_DIR, "Wohr_Balance Sheet_2025.pdf"),
    os.path.join(PDF_DIR, "8_IFCR Report Auditors Report_2025.pdf"),
    os.path.join(PDF_DIR, "10_Notes to Accounts Final_2025.pdf"),
]

print("=" * 70)
print("EXTRACTING TEXT FROM 5 PDFs...")
print("=" * 70)

# Extract text per document
extracted_docs = extract_text_from_multiple_pdfs(PDFS)

# Combine for fallback/legacy if needed
combined_text = "\n\n".join(extracted_docs.values())

print("\n" + "=" * 70)
print("RUNNING DOCUMENT PARSER...")
print("=" * 70)

# Run Parser
report = run_document_parser(combined_text, extracted_docs)

print("\n" + "=" * 70)
print("FINAL EXTRACTED REPORT")
print("=" * 70)
print(report)

# Write to output file
with open("final_report_output.txt", "w", encoding="utf-8") as f:
    f.write(report)
print("\n[SAVED] Output written to final_report_output.txt")
