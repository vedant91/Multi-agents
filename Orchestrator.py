# orchestrator.py
# THE BRAIN — Runs all SENTINEL agents in the correct sequence

import sys, os, time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    Master orchestrator — runs all SENTINEL agents in sequence.
    
    Returns a dict with:
    - all agent outputs (for display in UI)
    - cam_text (the full CAM text)
    - cam_doc_path (path to the generated Word document)
    - final_decision (extracted decision for summary)
    - timing (per-agent timing data)
    """
    
    # ── Input Validation ─────────────────────────────────────────
    if not company_name or not company_name.strip():
        raise ValueError("company_name is required")
    if not sector or not sector.strip():
        raise ValueError("sector is required")
    if loan_amount <= 0:
        raise ValueError("loan_amount must be positive")
    if loan_tenure_months <= 0:
        raise ValueError("loan_tenure_months must be positive")

    pipeline_start = time.time()
    timing = {}

    def update_progress(step: str, pct: int):
        print(f"\n{'='*60}")
        print(f"  SENTINEL [{pct}%] — {step}")
        print(f"{'='*60}")
        if progress_callback:
            progress_callback(step, pct)

    def timed_run(name, func, *args, **kwargs):
        """Wrap an agent call with timing and error handling."""
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            timing[name] = round(elapsed, 1)
            print(f"  ✅ {name} completed in {elapsed:.1f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start
            timing[name] = round(elapsed, 1)
            error_msg = f"[AGENT ERROR - {name}]: {str(e)}"
            print(f"  ❌ {name} failed after {elapsed:.1f}s: {e}")
            return error_msg

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
    parser_output = timed_run("Document Parser", run_document_parser, combined_text)
    outputs['parser'] = parser_output
    time.sleep(2)  # Brief pause between agents

    # ──────────────────────────────────────────────────────────
    # STEP 3: Research Intelligence Agent
    # ──────────────────────────────────────────────────────────
    update_progress("Conducting web research & background checks...", 28)
    research_result = timed_run("Research Agent", run_research_agent, company_name, promoter_name, sector)
    
    # Research agent returns (analysis_text, raw_search_results) tuple
    if isinstance(research_result, tuple):
        research_output, raw_search_results = research_result
    else:
        # Error case — got a string error message
        research_output = research_result
        raw_search_results = ""
    outputs['research'] = research_output
    time.sleep(2)  # Brief pause between agents

    # ──────────────────────────────────────────────────────────
    # STEP 3B: Company Intelligence Agent
    # ──────────────────────────────────────────────────────────
    update_progress("Analyzing company tier and credibility...", 35)
    company_intel = timed_run("Company Intelligence", run_company_intelligence, company_name, research_output)
    outputs['company_intelligence'] = company_intel

    # Handle error case — use defaults if company_intelligence failed
    if isinstance(company_intel, str):
        company_intel = {
            "tier": "TIER 3", "credibility_bonus": 0,
            "research_threshold": "standard", "bear_threshold": "standard",
            "default_direction": "neutral", "analysis_text": company_intel
        }

    company_tier = company_intel['tier']
    credibility_bonus = company_intel['credibility_bonus']

    # ──────────────────────────────────────────────────────────
    # STEP 3C: Fact Checker Agent (NEW — was missing from pipeline!)
    # Verifies research findings against raw search results
    # Uses the SAME raw_search_results from research agent (no duplicate API calls)
    # ──────────────────────────────────────────────────────────
    update_progress("Fact-checking research findings...", 40)
    fact_check_output = timed_run("Fact Checker", run_fact_checker, research_output, raw_search_results)
    outputs['fact_check'] = fact_check_output
    time.sleep(2)  # Brief pause between agents

    # ──────────────────────────────────────────────────────────
    # STEP 4: Fraud Detection Agent (now tier-aware)
    # ──────────────────────────────────────────────────────────
    update_progress("Running fraud pattern detection...", 48)
    fraud_output = timed_run("Fraud Detector", run_fraud_detector, parser_output, research_output, primary_notes, company_tier)
    outputs['fraud'] = fraud_output
    time.sleep(2)  # Brief pause between agents

    # ──────────────────────────────────────────────────────────
    # STEPS 5 & 6: Bull + Bear Agents (RUN IN PARALLEL!)
    # Both are independent — no need to wait for one before the other.
    # ──────────────────────────────────────────────────────────
    update_progress("Bull & Bear agents debating (parallel)...", 55)

    with ThreadPoolExecutor(max_workers=2) as executor:
        bull_future = executor.submit(
            timed_run, "Bull Agent", run_bull_agent,
            parser_output, fraud_output, research_output, loan_details, company_tier
        )
        bear_future = executor.submit(
            timed_run, "Bear Agent", run_bear_agent,
            parser_output, fraud_output, research_output, loan_details, company_tier
        )
        
        bull_output = bull_future.result()
        bear_output = bear_future.result()
    
    outputs['bull'] = bull_output
    outputs['bear'] = bear_output
    time.sleep(1.5)  # Rate limiting between agents

    # ──────────────────────────────────────────────────────────
    # STEP 7: Chairman Agent — Final Decision
    # ──────────────────────────────────────────────────────────
    update_progress("Chairman weighing the debate...", 72)
    chairman_output = timed_run(
        "Chairman Agent", run_chairman_agent,
        bull_brief=bull_output,
        bear_brief=bear_output,
        fraud_output=fraud_output,
        parser_output=parser_output,
        loan_details=loan_details,
        primary_notes=primary_notes,
        company_intelligence=company_intel
    )
    outputs['chairman'] = chairman_output
    time.sleep(1.5)  # Rate limiting between agents

    # ──────────────────────────────────────────────────────────
    # STEP 8: Stress Test Agent
    # ──────────────────────────────────────────────────────────
    update_progress("Running stress test simulations...", 82)
    stress_output = timed_run("Stress Test", run_stress_test, parser_output, chairman_output, loan_details)
    outputs['stress_test'] = stress_output
    time.sleep(1.5)  # Rate limiting between agents

    # ──────────────────────────────────────────────────────────
    # STEP 9: CAM Generator — Final Document
    # ──────────────────────────────────────────────────────────
    update_progress("Generating Credit Appraisal Memo...", 92)
    outputs['primary_notes'] = primary_notes
    cam_text, cam_doc_path = timed_run("CAM Generator", run_cam_generator, outputs)
    
    # Handle error case
    if isinstance(cam_text, str) and cam_text.startswith("[AGENT ERROR"):
        cam_doc_path = ""
    
    outputs['cam_text'] = cam_text
    outputs['cam_doc_path'] = cam_doc_path

    # ── Pipeline Summary ─────────────────────────────────────
    total_elapsed = time.time() - pipeline_start
    timing['total'] = round(total_elapsed, 1)
    outputs['timing'] = timing

    update_progress("SENTINEL Analysis Complete!", 100)
    
    print(f"\n{'='*60}")
    print(f"  PIPELINE TIMING SUMMARY")
    print(f"{'='*60}")
    for agent, t in timing.items():
        print(f"  {agent:.<30} {t:>6.1f}s")
    print(f"{'='*60}")
    
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