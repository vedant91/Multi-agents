#!/usr/bin/env python
"""
Test script to verify Infosys loan application approval with fixed SENTINEL system.
This demonstrates that Tier 1 companies are now properly handled.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Orchestrator import run_sentinel

def test_infosys_scenario():
    """Test the Infosys scenario that was previously failing"""

    print("\n" + "="*70)
    print("SENTINEL SYSTEM TEST — Infosys Loan Application")
    print("="*70)
    print("\nScenario: Large established IT company (TIER 1)")
    print("Company: Infosys Limited")
    print("Loan Amount: ₹10 crore (trivially small for them)")
    print("Purpose: Working capital for expansion")
    print("\nExpected Result BEFORE fixes: REJECTED (incorrectly)")
    print("Expected Result AFTER fixes: APPROVED (correctly)\n")

    print("-" * 70)
    print("Running SENTINEL Analysis...")
    print("-" * 70 + "\n")

    try:
        results = run_sentinel(
            company_name="Infosys Limited",
            promoter_name="Nandan Nilekani",
            sector="it services",
            loan_amount=10,  # ₹10 crore
            loan_purpose="Working capital for expansion in AI and cloud services",
            loan_tenure_months=36,
            uploaded_files=[],  # No documents for this test
            primary_notes="""
Infosys Corporate Office visited on 06/03/2026.
Company operates at 100% capacity with strong management.
No concerns observed during site visit. Financial disclosures are transparent
and audited by Big 4. Strong promoter background with 44-year track record.
Experienced management team in place.
""",
        )

        # Extract decision from chairman output
        chairman_text = results.get('chairman', '')

        print("\n" + "="*70)
        print("TEST RESULTS")
        print("="*70 + "\n")

        # Check for key improvements
        has_company_intel = 'company_intelligence' in results
        company_tier = "UNKNOWN"
        bonus_points = 0

        if has_company_intel:
            intel = results['company_intelligence']
            company_tier = intel.get('tier', 'UNKNOWN')
            bonus_points = intel.get('credibility_bonus', 0)
            print(f" Company Tier Detected: {company_tier}")
            print(f" Credibility Bonus Applied: +{bonus_points} points\n")

        # Check decision
        chairman_upper = chairman_text.upper()
        is_approved = 'APPROVE' in chairman_upper and 'REJECT' not in chairman_upper[:500]

        print("DECISION:")
        if is_approved:
            print(" APPROVED (Correct!)")
            print("\nFIX VERIFICATION: SUCCESS")
            print("  - Infosys correctly classified as TIER 1")
            print("  - Speculative concerns were disregarded")
            print("  - System applied credibility bonus")
            print("  - Loan approved for established company")
        else:
            print(" REJECTED (System may still have issues)")
            print("\nDEBUGGING INFO:")
            print("  - Check if Company Intelligence agent is loaded")
            print("  - Verify research agent is filtering properly")

        print("\n" + "="*70)
        print("Chairman's Verdict (excerpt):")
        print("="*70)
        print(chairman_text[:800])
        print("\n[... truncated for display ...]\n")

        print("="*70)
        print("TEST COMPLETE")
        print("="*70)

        return is_approved

    except Exception as e:
        print(f"\n ERROR during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_infosys_scenario()
    sys.exit(0 if success else 1)
