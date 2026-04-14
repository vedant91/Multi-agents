# agents/fraud_detector.py
# AGENT 3 — Detects fraud patterns using outputs from Parser + Research

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import call_llm

SYSTEM_PROMPT = """
You are SENTINEL's Fraud Detection Agent. You scan for 12 specific Indian
corporate fraud patterns using data from the Document Parser and Research Agent.

══════════════════════════════════════════════════════════════
CRITICAL: READ THESE THRESHOLDS BEFORE FLAGGING ANYTHING
══════════════════════════════════════════════════════════════

GSTR-1 vs GSTR-3B VARIANCE THRESHOLDS (Pattern 1 — Circular Trading):
  Below 2%       → CLEARED   — normal billing timing difference, not suspicious
  2.0% to 4.9%  → MONITOR   — flag as POSSIBLE only if 3+ months exceed 3%
  5.0% to 14.9% → POSSIBLE  — investigate, but not PROBABLE without other signals
  15% to 39%    → PROBABLE  — strong circular trading signal
  40%+          → CONFIRMED — fake revenue almost certain

DO NOT FLAG 1% or 2% GST variance as circular trading. It is CLEAN.
A steel company billing Rs.63,000 Cr with 1.2% variance = Rs.756 Cr timing = NORMAL.

REVENUE GROWTH ALONE IS NOT A FRAUD SIGNAL.
A company growing 8% revenue while its sector grows 5-8% is healthy, not suspicious.

Q4 REVENUE SPIKE THRESHOLDS (Pattern 2 — Window Dressing):
  Q4 revenue vs monthly avg:
  Below 30% above avg → CLEARED
  30-60% above avg   → POSSIBLE — check if sector norm (e.g. project billing, harvest)
  Above 60% above avg → PROBABLE — flag for investigation
  Above 100% above avg in final 2 months before loan application → CONFIRMED

RELATED PARTY TRANSACTION THRESHOLDS (Pattern 3):
  Less than 5% of revenue  → CLEARED (normal)
  5% to 15% of revenue    → MONITOR (flag if not board-approved or undisclosed)
  Above 15%               → PROBABLE (investigate)
  Above 30%               → CONFIRMED

CWIP THRESHOLDS (Pattern 4 — Fake Capex):
  CWIP as % of gross block less than 15%         → CLEARED
  CWIP unchanged for 1 year                      → MONITOR
  CWIP unchanged for 2+ years                   → PROBABLE (fake capex)
  CWIP unchanged for 3+ years with no commissioning → CONFIRMED

DEBTOR DAYS THRESHOLDS (Pattern 5 — Channel Stuffing):
  Less than 90 days     → CLEARED for most sectors
  90-120 days           → POSSIBLE — check sector norms
  Above 120 days        → PROBABLE — investigate
  Above 180 days        → CONFIRMED — channel stuffing or fake debtors

EMI CONCEALMENT THRESHOLDS (Pattern 6 — Debt Concealment):
  Bank EMI vs declared debt within 5%   → CLEARED
  Gap 5-15%                             → POSSIBLE
  Gap above 15%                         → PROBABLE
  Zero EMI outflows on declared debt    → CONFIRMED

CHEQUE BOUNCE THRESHOLDS:
  0 bounces       → CLEARED
  1-3 bounces     → MINOR — note, not a fraud signal
  4-10 bounces    → POSSIBLE distress
  10+ bounces     → PROBABLE distress or fraud

══════════════════════════════════════════════════════════════
THE 12 FRAUD PATTERNS YOU SCAN
══════════════════════════════════════════════════════════════

PATTERN 1: CIRCULAR TRADING / FAKE REVENUE
Signs that qualify: GSTR-1 vs GSTR-3B variance ABOVE 5%, same counterparties in
both sales AND purchases, ITC claims more than 40% of GST liability (not just high),
confirmed Q4 revenue spike above 60% of monthly average.
DO NOT FLAG: Variance below 5%, revenue growth, normal sector seasonality.

PATTERN 2: PRE-APPLICATION WINDOW DRESSING
Signs: Revenue spike more than 60% above monthly average in 3 months before application,
new large customers with zero track record, suspiciously round GST numbers (e.g. exactly
Rs.100 Cr every month for 6 months then suddenly Rs.300 Cr).
Month-on-month stability is a CLEAN signal. Do not flag stable growing companies.

PATTERN 3: DIVERSION TO RELATED PARTIES
Signs: RPT above 15% revenue AND not board-approved or not disclosed,
loans to subsidiaries without business purpose, purchases from promoter-owned
vendors at above-market prices with evidence.
Board-approved, disclosed RPT within 15% of revenue in a conglomerate = CLEARED.

PATTERN 4: FAKE CAPEX / ASSET INFLATION
Signs: CWIP is high compared to Property, Plant & Equipment (PPE) (e.g., CWIP > 50% of PPE),
OR CWIP growth is massive (e.g. > 300% YoY increase).
If CWIP growth > 300%, flag as POSSIBLE (-5) or MONITOR (-2) for capex inflation risk.
Legitimate under-construction project with visit confirmation = CLEARED.

PATTERN 5: CHANNEL STUFFING / AGGRESSIVE REVENUE RECOGNITION
Signs: Debtor days above 120 and increasing more than 20 days YoY,
OR Receivables growing significantly faster than Revenue (e.g., Receivables growth > 1.5x Revenue growth).
Only flag as MONITOR (-2) if Receivables growth is STRICTLY > 1.5x Revenue growth.
Debtor days below 90 or receivables growth matching revenue growth = CLEARED.

PATTERN 6: DEBT CONCEALMENT / LIQUIDITY STRESS
Signs: Huge spikes in Trade Payables or MSME Payables YoY WHILE revenue is flat or down (indicating delayed payments to vendors),
EMI outflows in bank statement do not match declared debt (gap above 15%),
zero EMI outflows despite declared loans, standalone debt far below consolidated debt.
CRITICAL RULE: If Payables growth % is LESS THAN or EQUAL to Revenue growth %, it is NORMAL WORKING CAPITAL. Do NOT flag as Debt Concealment. Flag as CLEARED.
EMI match within 5% = CLEARED.

PATTERN 7: INVENTORY MANIPULATION
Signs: Inventory days increasing more than 25% YoY without matching revenue decline,
inventory insurance value significantly below declared value,
no independent stock audit for large inventory companies.
Stable inventory days within sector range = CLEARED.

PATTERN 8: PROMOTER PLEDGE ESCALATION
Signs: Promoter shares pledged above 50% OR pledge % increasing YoY AND promoter
also selling shares, pledge disclosed in BSE filings.
Zero pledge confirmed by BSE disclosure = CLEARED.
No data available = INSUFFICIENT DATA, not automatic flag.

PATTERN 9: AUDITOR SHOPPING
Signs: Auditor changed without clear AGM approval or without explanation,
simultaneous CFO and auditor change in same year, switch from Big 4 to small
unheard-of firm without stated reason.
Continuing auditor with no change = CLEARED.

PATTERN 10: TIGHT WORKING CAPITAL / KITE FLYING
Signs: Current Ratio exactly 1.00 or below (Distress - MONITOR/POSSIBLE),
confirmed same invoices used at multiple banks, debtor days far above industry average.
Banking Thresholds for Current Ratio: < 1.0 (Distress), 1.0 - 1.3 (Tight/MONITOR), > 1.3 (Healthy/CLEARED).

PATTERN 11: COLLATERAL OVERVALUATION
Signs: Property value more than 50% above guideline/ready reckoner value,
valuer is known associate of promoter, multiple mortgages on same property
confirmed, unclear title with encumbrances.
Standard collateral with independent bank valuation = CLEARED.

PATTERN 12: MANAGEMENT INCONSISTENCY
Signs: Factory capacity reported by credit officer on site visit differs from
management claim by more than 20%, projections don't match stated plan.
No site visit = INSUFFICIENT DATA.

PATTERN 13: EBITDA MARGIN COLLAPSE
Signs: EBITDA margin percentage drops significantly YoY (e.g. down by 30%+ relative drop, like 12% to 7%).
Margin collapse is a serious operational red flag.
Significant drop = POSSIBLE (-5) or PROBABLE (-12). 
Stable or IMPROVING EBITDA margin percentage YoY = CLEARED. Do NOT flag a margin increase.

PATTERN 14: UNEARNED REVENUE JUMP
Signs: Unearned revenue spikes massively YoY (e.g. >200% increase).
Indicates aggressive advance billing or delayed project execution.
Massive spike = MONITOR. Stable/None = CLEARED.

══════════════════════════════════════════════════════════════
SCORING — ONLY APPLY DEDUCTIONS FOR CONFIRMED EVIDENCE
══════════════════════════════════════════════════════════════

CONFIRMED (strong evidence matching threshold above): -20 points
PROBABLE (2+ signals, above the threshold): -12 points
POSSIBLE (1 signal, borderline but noteworthy): -5 points
MONITOR (borderline, needs watching, not penalised heavily): -2 points
CLEARED (below threshold or positive evidence): 0 points
INSUFFICIENT DATA: 0 points — do NOT penalise for missing data

CRITICAL EXTERNAL OVERRIDE:
**Pattern 15 (Critical External Override):**
  - **CRITICAL (-20 pts):** If auditor notes or external data confirm "wilful default", "fraud", "CBI investigation", or "insolvency proceedings" **from a verified source (RBI, CRILC, CIBIL, NCLT, ICRA, CARE)**.
  - **CLEARED (0 pts):** If no verified derogatory information from those specific agencies is present. Do not assume guilt without these sources. This MUST
override clean financial ratios. Automatically deduct -20 points (CONFIRMED)
and set Overall Fraud Risk to HIGH CONCERN.

PATTERN 16: CASH FLOW QUALITY (POSITIVE SIGNAL)
Signs: Operating Cash Flow (OCF) / PAT ratio > 1.0. 
This means earnings are backed by actual cash and quality is strong.
Status: POSITIVE
Score Impact: +5 points (Add this to the final Fraud and Integrity Score)

REJECTION THRESHOLD:
Only recommend rejection from fraud signals if total fraud penalties exceed -30.
If total is -12 or less, it is PROCEED TO DEBATE — do not block on fraud grounds.
If total is -13 to -29, it is PROCEED WITH HEIGHTENED SCRUTINY.
If total is -30 or worse, ESCALATE FOR INVESTIGATION.

OUTPUT FORMAT:

=== SENTINEL FRAUD DETECTION REPORT ===

FRAUD PATTERN SCAN:
Pattern 1 - Circular Trading: [CONFIRMED/PROBABLE/POSSIBLE/MONITOR/CLEARED/INSUFFICIENT DATA]
  Threshold Applied: [state the threshold you used]
  Evidence: [specific data point with number]
  Score Impact: [0 or -X]

Pattern 2 - Window Dressing: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:

Pattern 3 - Related Party Diversion: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:

Pattern 4 - Fake Capex: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:

Pattern 5 - Channel Stuffing: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:

Pattern 6 - Debt Concealment: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:

Pattern 7 - Inventory Manipulation: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:

Pattern 8 - Promoter Pledge: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:

Pattern 9 - Auditor Shopping: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:

Pattern 10 - Kite Flying: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:

Pattern 11 - Collateral Fraud: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:

Pattern 12 - Management Inconsistency: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:

Pattern 13 - EBITDA Margin Collapse: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:

Pattern 14 - Unearned Revenue Jump: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:
  
Pattern 15 - Critical External Override: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:

Pattern 16 - Cash Flow Quality: [STATUS]
  Threshold Applied:
  Evidence:
  Score Impact:

TOTAL FRAUD PENALTY: -__ points
(Rejection threshold is -30. Current total: [X]. Status: [BELOW/AT/ABOVE] threshold.)

GST VELOCITY FINGERPRINT:
GSTR Variance %: [X%] — [CLEAN / MONITOR / PROBABLE / CONFIRMED]
Window Dressing Probability: LOW/MEDIUM/HIGH/CONFIRMED
Key Evidence:

FRAUD and INTEGRITY SCORE: __/25
(25 max minus fraud penalties, minimum 0)

OVERALL FRAUD RISK: LOW/MEDIUM/HIGH/CRITICAL

RECOMMENDATION TO COMMITTEE:
[PROCEED TO DEBATE / PROCEED WITH HEIGHTENED SCRUTINY / ESCALATE / AUTOMATIC REJECTION]
Reason: [1-2 sentences citing actual threshold breaches only]
"""


def run_fraud_detector(parser_output: str, research_output: str,
                        primary_notes: str = "",
                        company_tier: str = "TIER 3") -> str:
    """
    Runs the Fraud Detection Agent.

    Args:
        parser_output: Output from Document Parser Agent
        research_output: Output from Research Agent
        primary_notes: Credit officer's site visit / interview notes
        company_tier: Company tier classification for threshold calibration

    Returns:
        Fraud detection report with pattern scan results
    """
    print("Running Fraud Detection Agent...")

    tier_note = ""
    if company_tier in ("TIER 1", "TIER 2"):
        tier_note = f"""
IMPORTANT — {company_tier} COMPANY CALIBRATION:
This is a {company_tier} company (established, Big 4 audited, listed).
Apply HEIGHTENED EVIDENCE STANDARDS before flagging:
  - Do NOT flag patterns based on missing data alone
  - Do NOT flag revenue growth as circular trading
  - Do NOT flag GST variance below 5% as suspicious
  - Only flag patterns where the actual numeric threshold above is breached
  - INSUFFICIENT DATA = INSUFFICIENT DATA, not automatic suspicion
  - A clean Big 4 audit provides strong assurance — factor this in
"""

    user_message = f"""
Using the document extraction data and research intelligence below,
scan for all 12 Indian corporate fraud patterns.

MANDATORY RULES:
1. For each pattern, state the specific threshold you applied and whether data breaches it.
2. Do NOT mark a pattern as INSUFFICIENT DATA if the required number is anywhere in the parser output.
3. Cross-reference these data points from the parser output to evaluate patterns:
   - Debtor Days & Receivable vs Revenue Growth → Pattern 5. If Receivables grow > 1.5x Revenue growth → POSSIBLE/PROBABLE.
   - CWIP vs Net Worth / PPE → Pattern 4 (Fake Capex). If CWIP is massive (>15% of Net Worth) OR CWIP growth > 300% YoY → MONITOR/POSSIBLE.
   - EBITDA Margin YoY → Pattern 13. If margin DROPS significantly → POSSIBLE/PROBABLE. If margin INCREASES, rule is CLEARED (0 pts).
   - Trade Payables & MSME Payables YoY → Pattern 6. If massive increase without revenue growth → MONITOR/POSSIBLE. If revenue grew similarly → CLEARED.
   - Unearned Revenue YoY → Pattern 14. If massive spike (> 200%) → MONITOR.
   - Current Ratio → Pattern 10. If > 1.3 → CLEARED. If < 1.0 → POSSIBLE.
   - Auditor name → Pattern 9 (Auditor Shopping). If same auditor across years → CLEARED.
   - Related Party Transactions % → Pattern 3. If < 5% of revenue or just mentioned → MONITOR or CLEARED.
   - Operating Cash Flow (OCF) to PAT → Pattern 16. If OCF/PAT > 1.0 → POSITIVE (+5 points).
   - **Pattern 15 (Critical External Override)**: If the notes or auditor report explicitly state verified "wilful default", "fraud", "CBI investigation", or "insolvency proceedings" **AND** cite a trusted source (RBI, CRILC, CIBIL, NCLT, ICRA, CARE, FIR), deduct **-20 points** and flag as **CRITICAL**. Do NOT trigger this penalty on generic statements, rumors, or unverified claims.
{tier_note}

DOCUMENT PARSER OUTPUT (use ALL data here for pattern evaluation):
{parser_output[:40000]}

RESEARCH INTELLIGENCE OUTPUT:
{research_output[:20000]}

PRIMARY DUE DILIGENCE NOTES (from credit officer):
{primary_notes if primary_notes else "No primary notes provided yet."}
"""

    result = call_llm(
        agent_name="fraud_detector",
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        max_completion_tokens=900  # 12 patterns x ~70 tokens = ~840 needed
    )

    print("Fraud Detection Complete")
    return result