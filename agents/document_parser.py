# agents/document_parser.py
# AGENT 1 — Extracts all financial data from uploaded documents

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import call_llm

SYSTEM_PROMPT =SYSTEM_PROMPT = """
You are a financial document analyst for Indian corporate credit appraisal.
Extract ALL of the following from the provided documents:

FINANCIALS (3 years):
- Revenue, EBITDA%, PAT for FY22, FY23, FY24
- Total Debt (LT + ST), Net Worth, Debt/Equity ratio
- Interest Coverage Ratio (EBIT/Interest expense)
- Cash Flow from Operations (CFO) and CFO/PAT ratio
- Debtor Days, Inventory Days, Current Ratio

GST:
- Monthly GSTR-1 vs GSTR-3B variance %
- Window dressing signal (revenue spike in last 3 months?)
- ITC anomaly flag

BANK:
- Average monthly balance
- Number of cheque bounces
- Fund rotation flag (same-day in/out transactions?)
- Undisclosed EMI outflows vs declared debt

CROSS CHECKS:
- Revenue: Annual Report vs GST vs Bank Credits — PASS/FAIL
- Debt Reality: EMI outflows vs declared debt — PASS/FAIL
- Employee headcount vs salary outflows — PASS/FAIL

RED FLAGS (list each found):
- Auditor qualified opinion or change: YES/NO
- Related party transactions %
- CFO < PAT for 2+ years: YES/NO
- CWIP not capitalized: YES/NO
- Contingent liabilities total

Be specific with numbers. If data exists in documents, extract it.
Do not say NOT FOUND if the number appears anywhere in the text.
"""


def run_document_parser(extracted_text: str) -> str:
    """
    Runs the Document Parser Agent on extracted document text.
    
    Args:
        extracted_text: Combined text from all uploaded PDFs
    
    Returns:
        Structured financial extraction report
    """
    print("🔵 Running Document Parser Agent...")

    user_message = f"""
                 Extract all financial data from these Indian corporate documents.
             Every number mentioned below EXISTS in the documents — find and report it.
    
    DOCUMENTS:
       {extracted_text[:9000]}
"""
    # Note: We limit to 60,00 chars to stay within context.
    # Gemini 1.5 Pro handles up to 1M tokens, so this is very safe.

    result = call_llm(
        agent_name="document_parser",
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message
    )

    print("✅ Document Parser Complete")
    return result


if __name__ == "__main__":
    # Quick test with dummy text
    test_text = """
    XYZ Manufacturing Ltd - Annual Report 2024
    Revenue: Rs 250 crore (FY24), Rs 210 crore (FY23), Rs 180 crore (FY22)
    EBITDA: Rs 35 crore (14% margin)
    PAT: Rs 18 crore
    Total Debt: Rs 85 crore
    Net Worth: Rs 65 crore
    Cash from Operations: Rs 12 crore
    Auditor: S.R. Batliboi & Co. (Clean opinion)
    Related Party Transactions: Rs 8 crore (3.2% of revenue)
    """
    result = run_document_parser(test_text)
    print(result)