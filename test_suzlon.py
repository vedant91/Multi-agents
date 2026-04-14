import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from utils.pdf_extractor import extract_text_from_multiple_pdfs, combine_all_documents
from agents.document_parser import run_document_parser
from agents.fraud_detector import run_fraud_detector
from agents.bull_bear_agents import run_bull_agent, run_bear_agent
from agents.chairman_agent import run_chairman_agent

PDF_DIR = r"C:\Users\Vedant\OneDrive\Desktop\multi-3"
pdf_path = os.path.join(PDF_DIR, "2_CONDITIONAL_Suzlon.pdf")

extracted = extract_text_from_multiple_pdfs([pdf_path])
combined  = combine_all_documents(extracted)

parser_output = run_document_parser(combined, extracted_docs=extracted)

fraud_output = run_fraud_detector(
    parser_output=parser_output,
    research_output="No web research available for this test run.",
    primary_notes="",
    company_tier="TIER 3"
)

loan_details = {
    "company_name": "Suzlon",
    "sector": "manufacturing",
    "loan_amount": 500000000, 
    "loan_purpose": "Working Capital",
    "loan_tenure_months": 84
}

bull_output = run_bull_agent(parser_output, fraud_output, "No research", loan_details, "TIER 3")
bear_output = run_bear_agent(parser_output, fraud_output, "No research", loan_details, "TIER 3")

chairman_output = run_chairman_agent(
    bull_brief=bull_output,
    bear_brief=bear_output,
    fraud_output=fraud_output,
    parser_output=parser_output,
    loan_details=loan_details,
    primary_notes="",
    company_intelligence=None
)

print("\n\n=== CHAIRMAN OUTPUT ===")
print(chairman_output)
