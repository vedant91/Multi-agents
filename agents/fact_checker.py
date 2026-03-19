# agents/fact_checker.py
# Filters hallucinated findings before they reach downstream agents
# DETERMINISTIC VERSION: Structured output + strict verification rules

from utils.llm_client import call_llm

SYSTEM_PROMPT = """You are a fact-checking agent. You receive research findings and raw search results.
Your job: Remove any finding NOT supported by actual search result text.

For each finding in the research output:
1. Find the EXACT supporting quote in the raw search results
2. If a direct quote exists → KEEP the finding and cite the quote
3. If no direct quote exists → REMOVE it and mark as HALLUCINATED

YOU MUST output in this EXACT format:

=== FACT CHECK RESULTS ===

VERIFIED_FINDINGS_COUNT: [number]
REMOVED_FINDINGS_COUNT: [number]
HALLUCINATION_RISK: [LOW / MEDIUM / HIGH]

VERIFIED FINDINGS:
1. [Finding] | Quote: "[exact quote from search results]" | Source: [domain]
2. [Finding] | Quote: "[exact quote]" | Source: [domain]
(list all verified findings)

REMOVED AS UNVERIFIED:
1. [Finding] | Reason: No supporting quote found in search results
(list all removed findings, or "NONE" if all verified)

FACT CHECK CONFIDENCE: [HIGH / MEDIUM / LOW]
"""

def run_fact_checker(research_output: str, raw_search_results: str) -> str:
    print("🔍 Running Fact Checker...")
    
    # Truncate to fit within 8192 token limit
    max_research = 8000
    max_search = 10000
    
    result = call_llm("fact_checker", SYSTEM_PROMPT, f"""Verify each finding in the research output against the raw search results.
Only KEEP findings with a direct supporting quote from the search results.

RESEARCH OUTPUT TO CHECK:
{research_output[:max_research]}

RAW SEARCH RESULTS (ground truth — only these are valid sources):
{raw_search_results[:max_search]}

Output in the EXACT format specified. Every verified finding MUST have a direct quote.
Every finding without a quote MUST be listed under REMOVED AS UNVERIFIED.
""")
    return result