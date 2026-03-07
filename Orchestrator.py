# orchestrator.py
# THE BRAIN — Runs all 7 SENTINEL agents in the correct sequence

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.document_parser import run_document_parser
from agents.research_agent import run_research_agent
from agents.company_intelligence import run_company_intelligence
from agents.fact_checker import run_fact_checker
from agents.fraud_detector import run_fraud_detector
from agents.bull_bear_agents import run_bull_agent, run_bear_agent
from agents.chairman_agent import run_chairman_agent
from agents.stress_test_agent import run_stress_test
from agents.cam_generator import run_cam_generator
from utils.pdf_extractor import extract_text_from_multiple_pdfs, combine_all_documents


def run_sentinel(
    company_name: str,
    promoter_name: str,
    sector: str,
    loan_amount: float,
    loan_purpose: str,
    loan_tenure_months: int,
    uploaded_files: list,        # List of file paths to uploaded PDFs
    primary_notes: str = "",     # Credit officer site visit / interview notes
    progress_callback=None       # Optional function for UI progress updates
) -> dict:
    """
    Master orchestrator — runs all 7 SENTINEL agents in sequence.
    
    Returns a dict with:
    - all agent outputs (for display in UI)
    - cam_text (the full CAM text)
    - cam_doc_path (path to the generated Word document)
    - final_decision (extracted decision for summary)
    """
    
    def update_progress(step: str, pct: int):
        print(f"\n{'='*60}")
        print(f"  SENTINEL [{pct}%] — {step}")
        print(f"{'='*60}")
        if progress_callback:
            progress_callback(step, pct)

    loan_details = {
        "company_name": company_name,
        "promoter_name": promoter_name,
        "sector": sector,
        "loan_amount": loan_amount,
        "loan_purpose": loan_purpose,
        "loan_tenure_months": loan_tenure_months
    }

    outputs = {"loan_details": loan_details}

    # ──────────────────────────────────────────────────────────
    # STEP 1: Extract text from all uploaded documents
    # ──────────────────────────────────────────────────────────
    update_progress("Extracting documents...", 5)
    
    if uploaded_files:
        extracted_docs = extract_text_from_multiple_pdfs(uploaded_files)
        combined_text = combine_all_documents(extracted_docs)
    else:
        combined_text = f"No documents uploaded. Company: {company_name}, Sector: {sector}"
        print("⚠️  Warning: No documents uploaded. Analysis will be based on research only.")

    # ──────────────────────────────────────────────────────────
    # STEP 2: Document Parser Agent
    # ──────────────────────────────────────────────────────────
    update_progress("Parsing financial documents...", 15)
    parser_output = run_document_parser(combined_text)
    outputs['parser'] = parser_output

    # ──────────────────────────────────────────────────────────
    # STEP 3: Research Intelligence Agent
    # ──────────────────────────────────────────────────────────
    update_progress("Conducting web research & background checks...", 30)
    research_output = run_research_agent(company_name, promoter_name, sector)
    outputs['research'] = research_output

    # ──────────────────────────────────────────────────────────
    # STEP 3B: Company Intelligence Agent (NEW)
    # ──────────────────────────────────────────────────────────
    update_progress("Analyzing company tier and credibility...", 35)
    company_intel = run_company_intelligence(company_name, research_output)
    outputs['company_intelligence'] = company_intel

    # Store tier info for downstream agents to use
    company_tier = company_intel['tier']
    credibility_bonus = company_intel['credibility_bonus']
    research_threshold = company_intel['research_threshold']

    # ──────────────────────────────────────────────────────────
    # STEP 4: Fraud Detection Agent
    # ──────────────────────────────────────────────────────────
    update_progress("Running fraud pattern detection...", 45)
    fraud_output = run_fraud_detector(parser_output, research_output, primary_notes)
    outputs['fraud'] = fraud_output

    # ──────────────────────────────────────────────────────────
    # STEPS 5 & 6: Bull + Bear Agents (can run together)
    # ──────────────────────────────────────────────────────────
    update_progress("Bull Agent building approval case...", 55)
    bull_output = run_bull_agent(parser_output, fraud_output, research_output, loan_details)
    outputs['bull'] = bull_output

    update_progress("Bear Agent hunting for risks...", 63)
    bear_output = run_bear_agent(parser_output, fraud_output, research_output, loan_details)
    outputs['bear'] = bear_output

    # ──────────────────────────────────────────────────────────
    # STEP 7: Chairman Agent — Final Decision
    # ──────────────────────────────────────────────────────────
    update_progress("Chairman weighing the debate...", 72)
    chairman_output = run_chairman_agent(
        bull_brief=bull_output,
        bear_brief=bear_output,
        fraud_output=fraud_output,
        parser_output=parser_output,
        loan_details=loan_details,
        primary_notes=primary_notes,
        company_intelligence=company_intel
    )
    outputs['chairman'] = chairman_output

    # ──────────────────────────────────────────────────────────
    # STEP 8: Stress Test Agent
    # ──────────────────────────────────────────────────────────
    update_progress("Running stress test simulations...", 82)
    stress_output = run_stress_test(parser_output, chairman_output, loan_details)
    outputs['stress_test'] = stress_output

    # ──────────────────────────────────────────────────────────
    # STEP 9: CAM Generator — Final Document
    # ──────────────────────────────────────────────────────────
    update_progress("Generating Credit Appraisal Memo...", 92)
    outputs['primary_notes'] = primary_notes
    cam_text, cam_doc_path = run_cam_generator(outputs)
    outputs['cam_text'] = cam_text
    outputs['cam_doc_path'] = cam_doc_path

    update_progress("SENTINEL Analysis Complete!", 100)
    
    return outputs


# ──────────────────────────────────────────────────────────────
# QUICK TEST — Run this file directly to test the full pipeline
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  SENTINEL — ADVERSARIAL CREDIT INTELLIGENCE")
    print("  Test Run (No Documents Uploaded)")
    print("="*60 + "\n")

    results = run_sentinel(
        company_name="ABC Steel Manufacturing Pvt Ltd",
        promoter_name="Rajesh Kumar Sharma",
        sector="steel manufacturing",
        loan_amount=20,
        loan_purpose="Working capital and machinery purchase",
        loan_tenure_months=60,
        uploaded_files=[],  # No files in test mode
        primary_notes="Factory visited on 01/06/2025. Operating at approximately 65% capacity. Machinery is well-maintained. Workforce of ~150 workers observed. Management was cooperative and transparent during interview.",
    )

    print("\n" + "="*60)
    print("CHAIRMAN'S VERDICT PREVIEW:")
    print("="*60)
    print(results['chairman'][:1000])
    print(f"\n✅ Full CAM saved to: {results['cam_doc_path']}")