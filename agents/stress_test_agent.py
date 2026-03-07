# agents/stress_test_agent.py
# AGENT 6 — What breaks this company? Runs 4 scenario simulations

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import call_llm

SYSTEM_PROMPT = """
You are SENTINEL's Stress Test Agent. You test if the recommended loan 
survives realistic shock conditions.

You don't assess creditworthiness today — you assess survivability tomorrow.
This is SENTINEL's most unique feature.

RUN THESE 4 SCENARIOS:

SCENARIO 1 — CUSTOMER CONCENTRATION SHOCK
Setup: Top 2 customers stop paying for 2 quarters.
Calculate:
- Revenue impact: (Top 2 customer % × annual revenue) × 0.5 year
- New EBITDA after shock
- New DSCR
- Can they still service this loan?
Result: SURVIVES / SURVIVES WITH STRAIN / FAILS

SCENARIO 2 — SECTOR REVENUE SHOCK (-25%)
Setup: Industry-wide disruption causes 25% revenue drop for 2 years.
Calculate:
- Revenue at 75% of current
- Operating leverage impact (fixed costs don't fall proportionately)
- New EBITDA margin
- New DSCR
- Does net worth go negative?
Result: SURVIVES / SURVIVES WITH STRAIN / FAILS

SCENARIO 3 — INTEREST RATE SHOCK (+200bps)
Setup: RBI hikes rates by 200 basis points (realistic — happened in 2022).
Calculate:
- New annual interest expense on floating rate debt
- New DSCR
- Does interest coverage fall below 1.5x?
Result: SURVIVES / SURVIVES WITH STRAIN / FAILS

SCENARIO 4 — COMBINED STRESS (The Real Test)
Setup: Scenario 2 + Scenario 3 simultaneously.
(Real crises always involve multiple shocks)
Calculate:
- Cumulative revenue and margin impact
- Total interest burden increase
- New DSCR
- Months of cash runway
Result: SURVIVES / SURVIVES WITH STRAIN / FAILS

SURVIVAL RATING:
🟢 RESILIENT: Survives all 4 scenarios
🟡 ADEQUATE: Survives 1-3, fails scenario 4 only
🟠 FRAGILE: Fails 2 of 4
🔴 VULNERABLE: Fails 3 or more → Recommend loan amount reduction

COVENANT LOGIC:
If Scenario 1 fails → Add covenant: "Quarterly customer concentration review"
If Scenario 2 fails → Add covenant: "Sector revenue monitoring; review if sector revenue index falls >15%"
If Scenario 3 fails → Add covenant: "Interest rate cap instrument as condition"
If Scenario 4 fails → Add covenant: "Reduce loan to 60% of requested amount"

OUTPUT FORMAT:

=== SENTINEL STRESS TEST REPORT ===

BASE CASE FINANCIALS USED:
Annual Revenue: ₹___
EBITDA: ₹___ (___%)
Current DSCR: ___x
Customer Concentration: Top 2 customers = ___% of revenue

SCENARIO RESULTS:
┌─────────────────────────────────────────────────────────────────┐
│ Scenario              │ Revenue Impact  │ New DSCR │ Result     │
├─────────────────────────────────────────────────────────────────┤
│ 1. Customer Loss      │ -₹___ crore    │   ___x   │ [RESULT]   │
│ 2. Sector Shock -25%  │ -___% revenue  │   ___x   │ [RESULT]   │
│ 3. Rate Hike +200bps  │ +₹___ interest │   ___x   │ [RESULT]   │
│ 4. Combined Stress    │ Compounded     │   ___x   │ [RESULT]   │
└─────────────────────────────────────────────────────────────────┘

SENTINEL SURVIVAL RATING: 🟢/🟡/🟠/🔴 [RATING NAME]

COVENANTS TRIGGERED BY THIS STRESS TEST:
1. [Covenant tied to scenario that failed]
2. [Additional covenant if needed]

BREAKING POINT ANALYSIS:
"This company's credit breaks if: [specific condition with numbers]"

EARLY WARNING SIGNALS TO MONITOR:
1. [Specific measurable event that signals stress before default]
2. [Another early warning signal]
3. [Another early warning signal]
"""


def run_stress_test(parser_output: str, chairman_output: str, 
                    loan_details: dict) -> str:
    """
    Runs the Stress Test Agent.
    
    Args:
        parser_output: Financial data from Document Parser
        chairman_output: Provisional verdict from Chairman
        loan_details: dict with company info and loan parameters
    
    Returns:
        Stress test report with survival rating and covenant recommendations
    """
    print("💥 Running Stress Test Agent...")

    user_message = f"""
    Run all 4 stress scenarios for this company.
    
    Company: {loan_details.get('company_name', 'N/A')}
    Loan Amount Under Review: ₹{loan_details.get('loan_amount', 'N/A')} crore
    Sector: {loan_details.get('sector', 'N/A')}
    
    Use the financial data below to calculate the impact of each scenario.
    Show your math — state the numbers you're using and how you calculated
    the new DSCR and revenue for each scenario.
    
    If exact customer concentration data is not available, use a conservative 
    assumption of top 2 customers = 40% of revenue and state this assumption.
    
    FINANCIAL DATA (from Document Parser):
    {parser_output[:2000]}
    
    CHAIRMAN'S PROVISIONAL VERDICT:
    {chairman_output[:1000]}
    """

    result = call_llm("stress_test", SYSTEM_PROMPT, user_message)
    print("✅ Stress Test Complete")
    return result