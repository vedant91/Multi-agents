# agents/fact_checker.py
# Filters hallucinated findings before they reach the Fraud Detector

from utils.llm_client import call_llm

SYSTEM_PROMPT = """
You are a fact-checking agent. You receive research findings and raw search results.
Your job: Remove any finding NOT supported by actual search result text.

For each finding in the research output:
1. Find the supporting quote in the raw search results
2. If quote exists → KEEP the finding
3. If no quote exists → REMOVE it and mark as HALLUCINATED

This is critical. Downstream agents will REJECT loan applications based on your output.
False positives destroy legitimate businesses. Be strict.

Output format:
VERIFIED FINDINGS: [only findings with supporting quotes]
REMOVED AS UNVERIFIED: [findings you removed and why]
HALLUCINATION RISK: LOW / MEDIUM / HIGH
"""

def run_fact_checker(research_output: str, raw_search_results: str) -> str:
    print("🔍 Running Fact Checker...")
    result = call_llm("fact_checker", SYSTEM_PROMPT, f"""
    RESEARCH OUTPUT TO CHECK:
    {research_output[:6000]}
    
    RAW SEARCH RESULTS (ground truth):
    {raw_search_results[:14000]}
    
    Remove any finding in the research output that cannot be directly 
    quoted from the raw search results above.
    """)
    return result