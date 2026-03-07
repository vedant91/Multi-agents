#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
INFOSYS LOAN DEMO — Test with mock data (no web searches needed)
This demonstrates the fixed SENTINEL system approving Tier 1 companies correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Override web search to use mock data for demo
import utils.web_search as web_search_module

MOCK_INFOSYS_RESEARCH = """
SEARCH QUERY: Infosys Limited wilful defaulter RBI
===============================================
SUMMARY: No wilful default record found for Infosys Limited.
Infosys is a listed company on BSE (NSE) with clean regulatory record.

INDIVIDUAL RESULTS:

[Result 1]
Title: Infosys Limited - Wikipedia
URL: https://wikipedia.org/wiki/Infosys
Content: Infosys Limited is an Indian multinational corporation providing business 
consulting and technology services. Founded in 1981, Infosys is headquartered in 
Bengaluru, India and has a market capitalization exceeding $2 trillion USD as of 2026.
Published: 2024

[Result 2]
Title: Infosys - BSE Official Page
URL: https://www.bseindia.com/stocks/infosys
Content: Infosys Limited (NSE: INFY, BSE: 500209) is one of India's largest IT services 
companies. The company provides digital consulting, technology, and engineering services 
to Fortune 500 companies across multiple sectors.
Published: 2026

[Result 3]
Title: Infosys 2024 Annual Report
URL: https://www.infosys.com/investors/annual-report-2024.pdf
Content: Total Revenue: $25.2 billion (FY2024). Net Profit: $5.1 billion. 
Auditor: Deloitte Touche Tohmatsu (Big 4). Dividend paid: 2500% of profit. 
CIOs and CFOs commended management stability.
Published: 2025

════════════════════════════════════════════════════════════

SEARCH QUERY: Infosys Limited NCLT insolvency IBC 2016
===============================================
SUMMARY: No insolvency proceedings initiated against Infosys.

[Result 1]
Content: Infosys is a highly profitable company with strong liquidity.
No insolvency risk identified. Company has consistently paid dividends to shareholders.
Published: 2025

════════════════════════════════════════════════════════════

SEARCH QUERY: Nandan Nilekani SEBI order debarment fraud
===============================================
SUMMARY: No debarment order against Nandan Nilekani.

[Result 1]
Content: Nandan Nilekani is Co-Founder of Infosys and reputed business leader.
He served as Chairman and Managing Director for multiple years.
No regulatory debarment or fraud charges found.
Published: 2025

════════════════════════════════════════════════════════════

SEARCH QUERY: Infosys Limited GST evasion raid fake invoice
===============================================
SUMMARY: No GST fraud or fake invoice issues found.

[Result 1]
Content: Infosys has robust GST compliance framework. GST returns filed accurately.
No raids or investigations by GST authorities reported.
Published: 2025

════════════════════════════════════════════════════════════

SEARCH QUERY: Infosys Limited NPA bank fraud DRT SARFAESI
===============================================
SUMMARY: No bank NPA or fraud proceedings.

[Result 1]
Content: Infosys maintains deposits with leading Indian and international banks.
No default or NPA status recorded.
Published: 2025

════════════════════════════════════════════════════════════

SEARCH QUERY: Nandan Nilekani ED CBI SFIO investigation
===============================================
SUMMARY: No investigation against Nandan Nilekali by ED, CBI, or SFIO.

[Result 1]
Content: Nandan Nilekani is a respected technologist and entrepreneur with clean record.
Published: 2025

════════════════════════════════════════════════════════════

SEARCH QUERY: Infosys Limited latest news 2024 2025
===============================================
SUMMARY: Recent news highlights growth and expansion.

[Result 1]
Title: Infosys Reports Strong Q3 2024 Results
Content: Infosys reported revenue growth of 8.2% in Q3 2024.
Digital services segment grew 12.5%. Company guides for 4-6% growth in FY2025.
Published: 2025

[Result 2]
Title: Infosys Expands AI Capability Centers
Content: Infosys opened new AI and Cloud centers in Hyderabad and Pune
to support digital transformation for global clients.
Published: 2025

════════════════════════════════════════════════════════════

SEARCH QUERY: Infosys Limited court case litigation
===============================================
SUMMARY: No material litigation found.

[Result 1]
Content: Infosys handles standard commercial disputes through normal legal process.
No extraordinary or material litigations affecting operations.
Published: 2025

════════════════════════════════════════════════════════════

SEARCH QUERY: Nandan Nilekani other companies director
===============================================
SUMMARY: Nandan Nilekani is founder of Infosys.

[Result 1]
Content: Nandan Nilekani is Co-Founder and former MD of Infosys.
He founded AADHAR initiative as Unique Identification Authority of India (UIDAI) Chairman.
Published: 2025

════════════════════════════════════════════════════════════

SEARCH QUERY: it services RBI stressed sector NPA 2024 India
===============================================
SUMMARY: IT services sector remains robust and healthy.

[Result 1]
Content: IT Services sector NPA is only 0.3%, lowest among all sectors in India.
Industry guidance remains positive for FY2025-2026.
Major companies reporting double-digit growth.
Published: 2025

════════════════════════════════════════════════════════════

SEARCH QUERY: Infosys plant shutdown labour dispute
===============================================
SUMMARY: No plant shutdowns or labor disputes reported.

[Result 1]
Content: Infosys operates with strong employee relations and competitive benefits.
Multiple awards for best workplace. No significant labor disputes.
Published: 2025

════════════════════════════════════════════════════════════

SEARCH QUERY: Infosys management exit CEO CFO resignation
===============================================
SUMMARY: Stable management team in place.

[Result 1]
Content: Infosys appointed Vishal Sikka as CEO in recent years.
Management team is experienced with 20+ years in IT industry.
No unexpected exits reported in recent quarters.
Published: 2025

════════════════════════════════════════════════════════════
"""

# Mock the web search function for demo
original_search = web_search_module.search_web
original_run_searches = web_search_module.run_all_research_searches

def mock_search_web(query, max_results=5, timeout_seconds=30):
    """Returns mock data for demo"""
    print(f"    [DEMO MODE] Using mock data for: {query}")
    return MOCK_INFOSYS_RESEARCH

def mock_run_all_research_searches(company_name, promoter_name, sector):
    """Returns all mock research for demo"""
    print("  🔍 [DEMO MODE] Using mock Infosys research data (no web API calls)")
    return MOCK_INFOSYS_RESEARCH

web_search_module.search_web = mock_search_web
web_search_module.run_all_research_searches = mock_run_all_research_searches

from Orchestrator import run_sentinel

def test_infosys_demo():
    """Test Infosys with mock data - should APPROVE"""

    print("\n" + "="*80)
    print("   SENTINEL SYSTEM TEST - Infosys Loan Application (DEMO MODE)")
    print("="*80)
    print("\nScenario: TIER 1 Company (Large established IT giant)")
    print("Company: Infosys Limited (197000 crore, Listed BSE/NSE, Big 4 auditor)")
    print("Loan Amount: 10 crore (0.005% of annual revenue - trivial)")
    print("Purpose: Working capital for expansion")
    print("\n[DEMO MODE] Using mock research data (no web API calls needed)")
    print("[DEMO MODE] This demonstrates the fixed SENTINEL system\n")

    print("-" * 80)
    print("Running SENTINEL Analysis (with Tier 1 fix)...")
    print("-" * 80 + "\n")

    try:
        results = run_sentinel(
            company_name="Infosys Limited",
            promoter_name="Nandan Nilekani",
            sector="IT Services",
            loan_amount=10,  # 10 crore
            loan_purpose="Working capital for expansion in AI and cloud services",
            loan_tenure_months=36,
            uploaded_files=[],  # No documents for this demo
            primary_notes="""
Site Visit Report dated 06/03/2026 — Infosys HQ, Bangalore.

Observations:
✓ Modern 25-story headquarters with state-of-the-art infrastructure
✓ HR reports 320,000+ employees globally, 100,000+ in India
✓ Full capacity operations - expansion underway
✓ Financial team transparent - shared latest quarterly results
✓ Management: CEO Vishal Sikka (20yr+ IT industry), CFO stable

Management Interview:
✓ Company in growth phase, expanding AI/cloud service delivery
✓ Client base: 97% Fortune 500 companies
✓ Contract diversification: No customer >5% of revenue
✓ New AI centers being opened in India

Conclusion: Credit officer assessment = STRONG APPROVAL recommended.
Well-managed company with institutional controls and proven track record.
""",
        )

        # Extract decision from chairman output
        chairman_text = results.get('chairman', '')
        decision = "APPROVED ✅" if "APPROVE" in chairman_text.upper() else "REJECTED ❌"
        
        print("\n" + "="*80)
        print(f"SENTINEL FINAL DECISION: {decision}")
        print("="*80)
        
        # Show key sections
        lines = chairman_text.split('\n')
        for i, line in enumerate(lines):
            if 'DECISION' in line.upper() or 'SCORE' in line.upper():
                # Show context around decision
                start = max(0, i-2)
                end = min(len(lines), i+10)
                print('\n'.join(lines[start:end]))
                break
        
        print("\n" + "="*80)
        print("TEST RESULT")
        print("="*80)
        if "APPROVE" in chairman_text.upper() and "REJECT" not in chairman_text.upper()[:500]:
            print("✅ SUCCESS: Infosys was correctly APPROVED!")
            print("   - Tier 1 classification worked")
            print("   - No hallucinated rejections")
            print("   - System enforced tier-based approval logic")
        else:
            print("❌ FAILED: Infosys was rejected despite Tier 1 status")
            print("   - Review the chairman output below")
        
        print("\n" + "="*80)
        print("FULL CHAIRMAN DECISION:")
        print("="*80)
        print(chairman_text)
        
        print(f"\n✅ Full CAM document saved to: {results.get('cam_doc_path', 'N/A')}")
        
        return "APPROVE" in chairman_text.upper() and "reject" not in chairman_text.lower()[:500]

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_infosys_demo()
    sys.exit(0 if success else 1)
