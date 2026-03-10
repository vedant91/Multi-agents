# agents/document_parser.py
# AGENT 1 — Extracts all financial data from uploaded documents

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import call_llm

SYSTEM_PROMPT = """
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
CRITICAL: For EVERY financial figure you extract, you MUST explicitly state the unit (Rupees, Lakhs, Crores, Millions, etc.) EXACTLY as found in the text. For example, do not just write '200'; write '200 Crores' or '200 Lakhs' to prevent mathematical mismatches in downstream analysis.
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

    chunk_size = 24000  # Approx 6000 tokens (well within the 8192 limit)
    chunks = [extracted_text[i:i + chunk_size] for i in range(0, max(1, len(extracted_text)), chunk_size)]
    chunks = chunks[:5]  # Process up to 5 chunks ~120,000 characters total

    if len(chunks) == 1:
        user_message = f"""
                 Extract all financial data from these Indian corporate documents.
             Every number mentioned below EXISTS in the documents — find and report it.
    
    DOCUMENTS:
       {chunks[0]}
"""
        result = call_llm(
            agent_name="document_parser",
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message
        )
        print("✅ Document Parser Complete")
        return result

    all_results = []
    for i, chunk in enumerate(chunks):
        print(f"  📄 Parsing chunk {i+1}/{len(chunks)}...")
        user_message = f"""
                 Extract all financial data from these Indian corporate documents.
             Every number mentioned below EXISTS in the documents — find and report it.
    
    DOCUMENTS PART {i+1}:
       {chunk}
"""
        result = call_llm(
            agent_name=f"document_parser_chunk_{i+1}",
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message
        )
        all_results.append(result)

    print("  🔄 Merging extracted data...")
    combined_raw_data = "\n\n--- NEXT CHUNK EXTRACTION ---\n\n".join(all_results)
    
    merge_message = f"""
    The following are partial data extractions from different parts of a company's documents.
    Merge them into a single, complete financial report following the requested format.
    If a value is "Not available" in one section but found in another, use the found value.
    If it's truly not found across any chunk, say "Not available".
    Do not add conversational fluff.
    
    PARTIAL EXTRACTIONS:
    {combined_raw_data[:18000]}
    """
    
    final_result = call_llm(
        agent_name="document_parser_merge",
        system_prompt=SYSTEM_PROMPT,
        user_message=merge_message
    )

    print("✅ Document Parser Complete")
    return final_result


if __name__ == "__main__":
    # Quick test with dummy text
    test_text = """
    XYZ Manufacturing Ltd - Annual Report 2024
    Revenue: Rs 2,500,000,000 (FY24), Rs 2,100,000,000 (FY23), Rs 1,800,000,000 (FY22)
    EBITDA: Rs 350,000,000 (14% margin)
    PAT: Rs 180,000,000
    Total Debt: Rs 850,000,000
    Net Worth: Rs 650,000,000
    Cash from Operations: Rs 120,000,000
    Auditor: S.R. Batliboi & Co. (Clean opinion)
    Related Party Transactions: Rs 80,000,000 (3.2% of revenue)
    """
    result = run_document_parser(test_text)
    print(result)