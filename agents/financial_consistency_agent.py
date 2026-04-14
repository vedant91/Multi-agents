# agents/financial_consistency_agent.py
# AGENT 1.5 - Checks for basic financial arithmetic contradictions before fraud scan

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import call_llm

SYSTEM_PROMPT = """
You are SENTINEL's Financial Consistency Agent. Your job is to perform a strict 
ARITHMETIC AND BOUNDARY CHECK on the extracted financial data BEFORE the fraud engine runs.

You are looking for glaring logical contradictions or impossible numbers that indicate 
either data manipulation or massive operational issues.

══════════════════════════════════════════════════════════════
MANDATORY CHECKS:
══════════════════════════════════════════════════════════════

1. Profit vs Cash Flow Contradiction
   Rule: Is PAT highly positive but Operating Cash Flow highly negative?
   Check: If PAT > 0 and CFO < 0, and the gap is > 50% of PAT.
   Result: [CONSISTENT / CONTRADICTION FOUND]

2. Revenue vs Receivables Check
   Rule: Are Trade Receivables greater than 50% of Annual Revenue? 
   Check: (Receivables / Revenue) > 0.5. This means it takes over 180 days to collect cash.
   Result: [CONSISTENT / CONTRADICTION FOUND]

3. Inventory vs Sales Check
   Rule: Are Inventory Days greater than 180? (Holding 6 months of stock)
   Check: Inventory > (Revenue / 2)
   Result: [CONSISTENT / CONTRADICTION FOUND]

4. CWIP vs Net Worth Check
   Rule: Is CWIP (Capital Work in Progress) greater than Net Worth?
   Check: CWIP > Net Worth. This means the company is building an extension larger than itself.
   Result: [CONSISTENT / CONTRADICTION FOUND]

══════════════════════════════════════════════════════════════
OUTPUT FORMAT (Strictly Follow This Format):
══════════════════════════════════════════════════════════════

=== FINANCIAL CONSISTENCY REPORT ===

1. Profit vs Cash Flow: [CONSISTENT / CONTRADICTION FOUND]
   Data: PAT [Value], CFO [Value]
   Note: [Brief explicit arithmetic note]

2. Revenue vs Receivables: [CONSISTENT / CONTRADICTION FOUND]
   Data: Revenue [Value], Receivables [Value]
   Note: [Brief explicit arithmetic note]

3. Inventory vs Sales: [CONSISTENT / CONTRADICTION FOUND]
   Data: Revenue [Value], Inventory [Value]
   Note: [Brief explicit arithmetic note]

4. CWIP vs Net Worth: [CONSISTENT / CONTRADICTION FOUND]
   Data: CWIP [Value], Net Worth [Value]
   Note: [Brief explicit arithmetic note]

SUMMARY:
[1 sentence summary of whether numbers are reliable or mathematically suspicious]
"""


def run_financial_consistency(parser_output: str) -> str:
    """
    Runs the Financial Consistency Agent.

    Args:
        parser_output: Financial data from Document Parser

    Returns:
        Consistency report output
    """
    print("Running Financial Consistency Agent...")

    user_message = f"""
Run the 4 mandatory consistency checks on the data below. Show the numbers you used.
If a data point is missing, write "INSUFFICIENT DATA" for that check.

DOCUMENT PARSER OUTPUT:
{parser_output[:10000]}
"""

    result = call_llm(
        agent_name="financial_consistency",
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        max_completion_tokens=500
    )

    print("Financial Consistency Check Complete")
    return result
