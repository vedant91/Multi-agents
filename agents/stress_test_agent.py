# agents/stress_test_agent.py
# AGENT 6 — What breaks this company? Runs 4 scenario simulations

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import call_llm

# Condensed system prompt to fit within 8192 token limit
SYSTEM_PROMPT = """You are QUANTISENSE's Stress Test Agent. Test if the loan survives shock conditions.

DSCR CALCULATION:
DSCR = CFO ÷ Total Annual Debt Service
Total Debt Service = New Loan Service + Existing Finance Costs
New Loan Service = (Loan/Tenure_years) + (Loan × Rate%)
DO NOT add principal repayment to existing debt unless you have maturity data.

4 SCENARIOS:

S1 — Customer Concentration Shock: Top 2 customers stop paying 6 months.
Revenue impact = concentration% × revenue × 0.5. EBITDA margin compressed 3-5pp.
If concentration unknown, assume 40%.

S2 — Sector Revenue Shock -25%: 2 years sustained. EBITDA margin compressed 4-6pp.
Check if net worth goes negative (2yr losses > net worth).

S3 — Interest Rate +200bps: 70% of debt is floating. Additional cost = Debt × 70% × 2%.

S4 — Combined (S2+S3): Both. Cash runway = Cash Balance ÷ Monthly debt service.

RATINGS:
🟢 RESILIENT: All 4 DSCR > 1.25x
🟡 ADEQUATE: S1-S3 pass, S4 DSCR 1.0-1.25x
🟠 FRAGILE: 2 of 4 DSCR < 1.0x
🔴 VULNERABLE: 3+ fail → reduce loan to 60%

OUTPUT: Show calculations for each scenario with:
BASE CASE: Revenue, EBITDA, CFO, Finance Costs, Total Debt, Cash, New Loan details, BASE DSCR
Each scenario: Revenue impact, New EBITDA, New DSCR, Result (SURVIVES/STRAIN/FAILS)
SURVIVAL RATING: 🟢/🟡/🟠/🔴
COVENANTS: triggered by failed scenarios
BREAKING POINT: specific condition that breaks the company
"""


def run_stress_test(parser_output: str, chairman_output: str,
                    loan_details: dict) -> str:
    """
    Runs the Stress Test Agent.
    """
    print("Running Stress Test Agent...")

    loan_amount = loan_details.get('loan_amount', 'N/A')
    sector      = loan_details.get('sector', 'N/A')
    company     = loan_details.get('company_name', 'N/A')

    # Truncate inputs to fit within 8192 token limit
    # System prompt ≈ 900 tokens, user template ≈ 200 tokens
    # Available for data: ~5100 tokens ≈ 20,400 chars
    max_parser = 8000
    max_chairman = 5000

    user_message = f"""Run all 4 stress scenarios for this company. Show your math.

Company: {company} | Loan: Rs.{loan_amount} | Sector: {sector}

MANDATORY INSTRUCTIONS:
1. Extract CFO, EBITDA, Finance Costs, Total Debt, Net Worth, Cash from the data below.
2. Calculate TOTAL ANNUAL DEBT SERVICE correctly (see system prompt formula).
3. If customer concentration unknown, state: "Assuming top 2 = 40% (conservative default)"
4. Show calculations for EVERY scenario with specific numbers.
5. End with SURVIVAL RATING, COVENANTS, and BREAKING POINT.
6. Start your response with: === STRESS TEST RESULTS ===

DOCUMENT FINANCIALS:
{parser_output[:max_parser]}

CHAIRMAN'S DECISION:
{chairman_output[:max_chairman]}
"""

    result = call_llm("stress_test", SYSTEM_PROMPT, user_message)
    print("Stress Test Complete")
    return result