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

══════════════════════════════════════════════════════════════
MANDATORY: HOW TO CALCULATE DSCR CORRECTLY
══════════════════════════════════════════════════════════════

DSCR = Cash Flow from Operations (CFO) ÷ Total Annual Debt Service

TOTAL ANNUAL DEBT SERVICE = (Annual principal repayment on ALL loans)
                           + (Annual interest on ALL loans)

For the NEW loan being evaluated:
  Annual Principal on new loan = Loan Amount ÷ Tenure in years
  Annual Interest on new loan  = Loan Amount × Interest Rate %
  New Loan Annual Debt Service = Principal + Interest

For EXISTING debt:
  Existing Debt Service ≈ Declared Finance Costs from P&L
  (Finance Costs already represents annual interest obligations)
  DO NOT add principal repayment unless you have a specific maturity schedule.
  Reason: Most companies have staggered debt maturity, not lump-sum repayment.

EXAMPLE — CORRECT DSCR calculation:
  Company CFO: Rs.11,494 Cr
  New Loan: Rs.500 Cr, 7 years, 8.75%
  New Loan Annual Service: (500/7) + (500 × 8.75%) = 71 + 44 = Rs.115 Cr/year
  Existing debt service (declared Finance Costs from P&L): Rs.2,640 Cr/year
  Total Debt Service = Rs.115 + Rs.2,640 = Rs.2,755 Cr
  DSCR = Rs.11,494 ÷ Rs.2,755 = 4.17x

COMMON MISTAKE TO AVOID:
  ❌ WRONG: Existing Debt Service = Finance Costs (2,640) + (Total Debt / 5 years)
  This double-counts — Finance Costs already includes interest paid on existing debt.
  Only add principal repayment if you have actual maturity schedule data.

══════════════════════════════════════════════════════════════
HOW TO CALCULATE EACH STRESS SCENARIO
══════════════════════════════════════════════════════════════

SCENARIO 1 — CUSTOMER CONCENTRATION SHOCK
Setup: Top 2 customers stop paying for 2 quarters (6 months).
Step 1: Revenue impact = (Top 2 customer % × annual revenue) × 0.5
        If concentration data not available, assume 40% conservatively.
Step 2: New EBITDA = (Reduced Revenue × EBITDA margin) — fixed costs don't
        fall proportionately, so assume margin compresses by 3-5 percentage points
Step 3: New DSCR = New EBITDA (or CFO estimate) ÷ Total Annual Debt Service
        [use the formula above for total debt service]
Step 4: Can they still service this loan? Yes if DSCR above 1.25x

SCENARIO 2 — SECTOR REVENUE SHOCK (-25%)
Setup: Industry-wide disruption causes 25% revenue drop sustained for 2 years.
Step 1: New Revenue = Current Revenue × 0.75
Step 2: Operating leverage — fixed costs don't fall. Assume EBITDA margin
        compresses by 4-6 percentage points depending on fixed cost intensity.
        High fixed cost businesses (manufacturing, steel) compress more.
Step 3: New EBITDA = New Revenue × (Compressed EBITDA margin)
Step 4: New DSCR = New EBITDA ÷ Total Annual Debt Service
Step 5: Does net worth go negative? Net Worth goes negative if cumulative losses
        exceed current Net Worth. Check: if 2 years of net loss > Net Worth.

SCENARIO 3 — INTEREST RATE SHOCK (+200bps)
Setup: RBI hikes rates 200 basis points. This affects FLOATING rate debt only.
Step 1: Assume 70% of total debt is floating rate (conservative for Indian cos)
Step 2: Additional interest = Total Debt × 70% × 2% = incremental cost
Step 3: New Finance Cost = Old Finance Cost + additional interest
Step 4: New DSCR = CFO ÷ (Old Debt Service + Additional Interest)
        Note: principal repayment doesn't change, only interest does
Step 5: Does interest coverage fall below 1.5x?
        ICR = EBITDA ÷ New Finance Cost

SCENARIO 4 — COMBINED STRESS (The Real Test)
Setup: Scenario 2 revenue shock (-25%) AND Scenario 3 rate hike (+200bps) together.
Step 1: Apply both revenue drop AND margin compression from Scenario 2
Step 2: Apply increased interest cost from Scenario 3
Step 3: New DSCR = Stressed EBITDA ÷ Stressed Total Debt Service
Step 4: Cash runway = Closing Cash Balance ÷ Monthly cash burn (monthly debt service)
Step 5: If DSCR above 1.0x → SURVIVES. Between 0.8-1.0x → SURVIVES WITH STRAIN.
        Below 0.8x → FAILS

══════════════════════════════════════════════════════════════
SURVIVAL RATINGS
══════════════════════════════════════════════════════════════

🟢 RESILIENT: Survives all 4 scenarios with DSCR above 1.25x in all
🟡 ADEQUATE: Survives 1-3, scenario 4 DSCR drops to 1.0-1.25x range
🟠 FRAGILE: Fails 2 of 4 (DSCR drops below 1.0x in 2 scenarios)
🔴 VULNERABLE: Fails 3 or more → Recommend loan amount reduction to 60%

COVENANT LOGIC:
If Scenario 1 fails → Covenant: "Submit top-10 customer revenue quarterly.
                       Single customer cannot exceed 20% of revenue."
If Scenario 2 fails → Covenant: "Sector revenue monitoring; trigger review
                       if sector revenue falls more than 15%"
If Scenario 3 fails → Covenant: "Purchase interest rate cap instrument
                       for floating rate exposure above Rs.[X] Cr"
If Scenario 4 fails → Covenant: "Reduce loan to 60% of requested amount.
                       Maintain minimum cash balance of Rs.[X] Cr."

══════════════════════════════════════════════════════════════
OUTPUT FORMAT
══════════════════════════════════════════════════════════════

=== SENTINEL STRESS TEST REPORT ===

BASE CASE FINANCIALS USED:
  Annual Revenue:           Rs.___ Cr
  EBITDA:                   Rs.___ Cr (___% margin)
  CFO (Cash from Ops):      Rs.___ Cr
  Existing Finance Costs:   Rs.___ Cr/year
  Total Existing Debt:      Rs.___ Cr
  Closing Cash Balance:     Rs.___ Cr
  New Loan Amount:          Rs.___ Cr
  New Loan Tenure:          ___ years
  New Loan Interest Rate:   ___% p.a.
  New Loan Annual Service:  Rs.___ Cr/yr (Principal Rs.___Cr + Interest Rs.___Cr)
  Total Debt Service:       Rs.___ Cr/yr (Existing service + New loan service)
  BASE CASE DSCR:           ___x (CFO ÷ Total Annual Debt Service)
  Customer Concentration:   Top 2 = ___% of revenue [or ASSUMED 40% if unknown]

SCENARIO CALCULATIONS:

Scenario 1 — Customer Concentration Shock:
  Revenue impact: ___% concentration × Rs.___Cr × 0.5yr = -Rs.___Cr
  New Revenue: Rs.___Cr | New EBITDA Margin: ___% (compressed ___pp)
  New EBITDA: Rs.___Cr | New DSCR: Rs.___Cr ÷ Rs.___Cr = ___x
  Result: [SURVIVES / SURVIVES WITH STRAIN / FAILS]

Scenario 2 — Sector Revenue Shock -25%:
  New Revenue: Rs.___Cr × 0.75 = Rs.___Cr
  EBITDA margin compression: ___pp → New margin: ___%
  New EBITDA: Rs.___Cr | New DSCR: ___x
  Net worth goes negative? [YES/NO] — Net Worth Rs.___Cr vs 2yr loss Rs.___Cr
  Result: [SURVIVES / SURVIVES WITH STRAIN / FAILS]

Scenario 3 — Interest Rate Shock +200bps:
  Floating rate debt assumed: Rs.___Cr (70% of total)
  Additional interest: Rs.___Cr × 2% = +Rs.___Cr/year
  New Finance Cost: Rs.___Cr | New ICR: ___x | New DSCR: ___x
  Result: [SURVIVES / SURVIVES WITH STRAIN / FAILS]

Scenario 4 — Combined Stress:
  Revenue after -25% shock: Rs.___Cr
  EBITDA after compression: Rs.___Cr (___% margin)
  Interest cost after +200bps: Rs.___Cr
  Total Stressed Debt Service: Rs.___Cr
  New DSCR: ___x | Cash runway: ___ months
  Result: [SURVIVES / SURVIVES WITH STRAIN / FAILS]

RESULTS SUMMARY TABLE:
┌─────────────────────────────────────────────────────────────────────────┐
│ Scenario              │ Revenue Impact   │ New DSCR │ ICR   │ Result    │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Customer Loss      │ -Rs.___ Cr       │  ___x    │  ___x │ [RESULT]  │
│ 2. Sector Shock -25%  │ -25% = Rs.___ Cr │  ___x    │  ___x │ [RESULT]  │
│ 3. Rate Hike +200bps  │ +Rs.___ Cr int.  │  ___x    │  ___x │ [RESULT]  │
│ 4. Combined Stress    │ Both above       │  ___x    │  ___x │ [RESULT]  │
└─────────────────────────────────────────────────────────────────────────┘

SENTINEL SURVIVAL RATING: 🟢/🟡/🟠/🔴 [RATING NAME]

COVENANTS TRIGGERED BY THIS STRESS TEST:
1. [Covenant tied to scenario result — or NONE if all scenarios pass]

BREAKING POINT ANALYSIS:
"This company's credit breaks if: [specific measurable condition with numbers]"
Example: "DSCR drops below 1.25x if revenue falls more than 38% and rates rise 200bps simultaneously"

EARLY WARNING SIGNALS TO MONITOR:
1. [Specific measurable KPI with trigger level]
2. [Specific measurable KPI with trigger level]
3. [Specific measurable KPI with trigger level]
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
    print("Running Stress Test Agent...")

    loan_amount = loan_details.get('loan_amount', 'N/A')
    sector      = loan_details.get('sector', 'N/A')
    company     = loan_details.get('company_name', 'N/A')

    user_message = f"""
Run all 4 stress scenarios for this company. Show your full math step by step.

Company:     {company}
Loan Amount: Rs.{loan_amount}
Sector:      {sector}

MANDATORY BEFORE STARTING:
1. Extract CFO, EBITDA, Finance Costs, Total Debt, Net Worth, Cash Balance
   from the financial data below.
2. Calculate TOTAL ANNUAL DEBT SERVICE using this formula:
   a. New Loan Annual Service = (Loan Amount / Tenure_years) + (Loan Amount × Interest Rate)
   b. Existing Debt Service = Declared Finance Costs from P&L (this represents annual interest)
      DO NOT add principal repayment unless you have confirmed maturity schedule data.
   c. Total Debt Service = a + b
3. BASE CASE DSCR = CFO / Total Debt Service (calculated above)
4. DO NOT use Loan Amount alone as the denominator for DSCR.

If customer concentration data is not available in the documents,
clearly state: "Assuming top 2 customers = 40% of revenue (conservative default)"

DOCUMENT FINANCIALS (for baseline numbers):
{parser_output[:10000]}

CHAIRMAN'S PRELIMINARY DECISION (for current assessment context):
{chairman_output[:10000]}
"""

    result = call_llm("stress_test", SYSTEM_PROMPT, user_message)
    print("Stress Test Complete")
    return result