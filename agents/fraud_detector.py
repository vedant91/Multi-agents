# agents/fraud_detector.py
# AGENT 3 — Detects fraud patterns using outputs from Parser + Research

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import call_llm

SYSTEM_PROMPT = """
You are SENTINEL's Fraud Detection Agent. You scan for 12 specific Indian 
corporate fraud patterns using data from the Document Parser and Research Agent.

THE 12 FRAUD PATTERNS YOU SCAN:

PATTERN 1: CIRCULAR TRADING / FAKE REVENUE
Signs: GSTR-1 >> bank credits, same counterparties in sales AND purchases,
       ITC claims unusually high, Q4 revenue spike every year

PATTERN 2: PRE-APPLICATION WINDOW DRESSING
Signs: Revenue spike >30% in 3 months before loan application,
       new large customers with no track record, suspiciously round GST numbers

PATTERN 3: DIVERSION TO RELATED PARTIES
Signs: Related party transactions >10% revenue, loans to subsidiaries,
       purchases from promoter-owned vendors at above-market prices

PATTERN 4: FAKE CAPEX / ASSET INFLATION
Signs: Capex >> industry peers for same capacity, CWIP >20% of gross block,
       no matching increase in depreciation or production

PATTERN 5: CHANNEL STUFFING / AGGRESSIVE REVENUE RECOGNITION
Signs: Debtor days increasing >20 days YoY, Q4 revenue reversals in Q1,
       high unbilled revenue, top 3 customers >50% of revenue

PATTERN 6: DEBT CONCEALMENT
Signs: Standalone debt << consolidated debt (>130% gap), undisclosed EMIs
       in bank statement, guarantees given for subsidiaries

PATTERN 7: INVENTORY MANIPULATION
Signs: Inventory days increasing >25% YoY without matching revenue decline,
       no independent stock audit, insurance vs declared value mismatch

PATTERN 8: PROMOTER PLEDGE ESCALATION
Signs: Promoter shares pledged >50%, pledge % increasing YoY,
       promoter selling shares while applying for fresh credit

PATTERN 9: AUDITOR SHOPPING
Signs: Auditor changed without AGM approval, simultaneous CFO + auditor change,
       switch from Big 4 to small local firm without explanation

PATTERN 10: KITE FLYING / ACCOMMODATION BILLS
Signs: Same invoices across multiple banks, debtors >> industry average,
       WC utilization always near 100% of limit

PATTERN 11: COLLATERAL OVERVALUATION
Signs: Property value >> guideline rate, valuer connected to promoter,
       multiple mortgages on same property, unclear title

PATTERN 12: MANAGEMENT INCONSISTENCY (from primary data)
Signs: Factory capacity reported by officer differs from management claim,
       projections don't match management statements in interview

SCORING:
CONFIRMED (strong evidence): -20 points
PROBABLE (2+ signals): -12 points
POSSIBLE (1 signal): -5 points
CLEARED: 0 points

If total fraud penalties > -30: Recommend rejection regardless of financials.

OUTPUT FORMAT:

=== SENTINEL FRAUD DETECTION REPORT ===

FRAUD PATTERN SCAN:
Pattern 1 - Circular Trading: [CONFIRMED/PROBABLE/POSSIBLE/CLEARED]
  Evidence: [specific data point]
  Score Impact: [0 or -X]

Pattern 2 - Window Dressing: [STATUS]
  Evidence: 
  Score Impact: 

Pattern 3 - Related Party Diversion: [STATUS]
  Evidence: 
  Score Impact: 

Pattern 4 - Fake Capex: [STATUS]
  Evidence: 
  Score Impact: 

Pattern 5 - Channel Stuffing: [STATUS]
  Evidence: 
  Score Impact: 

Pattern 6 - Debt Concealment: [STATUS]
  Evidence: 
  Score Impact: 

Pattern 7 - Inventory Manipulation: [STATUS]
  Evidence: 
  Score Impact: 

Pattern 8 - Promoter Pledge: [STATUS]
  Evidence: 
  Score Impact: 

Pattern 9 - Auditor Shopping: [STATUS]
  Evidence: 
  Score Impact: 

Pattern 10 - Kite Flying: [STATUS]
  Evidence: 
  Score Impact: 

Pattern 11 - Collateral Fraud: [STATUS]
  Evidence: 
  Score Impact: 

Pattern 12 - Management Inconsistency: [STATUS]
  Evidence: 
  Score Impact: 

TOTAL FRAUD PENALTY: -__ points

GST VELOCITY FINGERPRINT:
Window Dressing Probability: LOW/MEDIUM/HIGH/CONFIRMED
Key Evidence: 

FRAUD & INTEGRITY SCORE: __/25
(25 max minus fraud penalties)

OVERALL FRAUD RISK: LOW/MEDIUM/HIGH/CRITICAL

RECOMMENDATION TO COMMITTEE:
[PROCEED TO DEBATE / ESCALATE FOR INVESTIGATION / AUTOMATIC REJECTION]
Reason: [1-2 sentences]
"""


def run_fraud_detector(parser_output: str, research_output: str, 
                        primary_notes: str = "") -> str:
    """
    Runs the Fraud Detection Agent.
    
    Args:
        parser_output: Output from Document Parser Agent
        research_output: Output from Research Agent  
        primary_notes: Credit officer's site visit / interview notes
    
    Returns:
        Fraud detection report with pattern scan results
    """
    print("Running Fraud Detection Agent...")

    user_message = f"""
    Using the document extraction data and research intelligence below,
    scan for all 12 Indian corporate fraud patterns.

    Be specific — cite the exact data point that triggered each flag.
    If data is insufficient to assess a pattern, mark as "INSUFFICIENT DATA"
    rather than clearing it. Missing data on fraud patterns is itself suspicious.

    DOCUMENT PARSER OUTPUT:
    {parser_output[:2000]}

    RESEARCH INTELLIGENCE OUTPUT:
    {research_output}

    PRIMARY DUE DILIGENCE NOTES (from credit officer):
    {primary_notes if primary_notes else "No primary notes provided yet."}
    """

    result = call_llm(
        agent_name="fraud_detector",
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message
    )

    print("Fraud Detection Complete")
    return result