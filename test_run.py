import os
import sys

# Ensure proper path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Orchestrator import run_sentinel

def mock_progress(step, pct):
    print(f"Progress: {step} ({pct}%)", flush=True)

if __name__ == "__main__":
    print("Testing backend orchestrator...", flush=True)
    try:
        results = run_sentinel(
            company_name="Dummy Corp",
            promoter_name="John Doe",
            sector="it services",
            loan_amount=10.0,
            loan_purpose="Expansion",
            loan_tenure_months=12,
            uploaded_files=[],
            primary_notes="",
            progress_callback=mock_progress
        )
        print("SUCCESS! Output keys: " + ", ".join(results.keys()), flush=True)
    except Exception as e:
        import traceback
        traceback.print_exc()
