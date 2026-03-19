# agents/research_agent.py
# AGENT 2 — Searches the internet for external intelligence on the company

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import call_llm
from utils.web_search import run_all_research_searches

# Condensed system prompt to save tokens (~1200 tokens instead of ~2500)
SYSTEM_PROMPT = """You are QUANTISENSE's Research Intelligence Agent.

ANTI-HALLUCINATION RULES (NON-NEGOTIABLE):
1. ONLY report facts EXPLICITLY stated in the search results below. If not found → "NOT FOUND IN SEARCH RESULTS".
2. Every finding needs a short quote (<15 words) + source domain + date.
3. Automatic rejection triggers (wilful defaulter, NCLT, SEBI debarment) need OFFICIAL source confirmation (rbi.org.in, nclt.gov.in, sebi.gov.in). News alone is NOT enough.
4. Distinguish allegations from confirmed facts. Use "alleged", "under investigation" for unconfirmed.
5. When in doubt → UNVERIFIED. Better to miss a red flag than invent one.

SEVERITY: 🔴 HIGH (official source confirmed) | 🟠 MEDIUM (litigation, downgrade, regulatory fine) | 🟡 LOW (unverified news, minor disputes)

OUTPUT FORMAT:
=== QUANTISENSE RESEARCH INTELLIGENCE REPORT ===

⛔ AUTOMATIC REJECTION TRIGGERS: [NONE FOUND or list with official source quote]

🔴 CRITICAL FINDINGS: Finding | Quote | Source | Date | Score Impact: -X pts
🟠 NOTABLE FINDINGS: Finding | Quote | Source | Date | Score Impact: -X pts
🟡 INFORMATIONAL: Brief notes with source
⚠️ UNVERIFIED ALLEGATIONS: [list — do NOT trigger rejection]

🕸️ PROMOTER NETWORK RISK: LOW/MEDIUM/HIGH/CRITICAL
📊 SECTOR RISK: Sector | Risk Level | Key risks
📰 NEWS SENTIMENT: Positive/Neutral/Negative | Trend | Key headline

EXTERNAL INTELLIGENCE SCORE: __/20
(Start at 20. HIGH: -4 to -8, MEDIUM: -2 to -4, UNVERIFIED: 0 pts)

RESEARCH CONFIDENCE: HIGH/MEDIUM/LOW
DATA GAPS: [what you couldn't find]
OVERALL VERDICT: [2-3 sentences, conservative, cite facts only]
"""


def run_research_agent(company_name: str, promoter_name: str, sector: str) -> tuple:
    """
    Runs the Research Intelligence Agent with anti-hallucination safeguards.

    Args:
        company_name: Full company name
        promoter_name: Primary promoter / MD name
        sector: Industry sector

    Returns:
        Tuple of (research_report: str, raw_search_results: str)
    """
    print(f"Running Research Agent for: {company_name}")
    print("   Searching web — this takes 30-60 seconds...")

    # Step 1: Gather all web search results
    raw_search_results = run_all_research_searches(
        company_name=company_name,
        promoter_name=promoter_name,
        sector=sector
    )

    # Step 2: Truncate search results to fit within context limit
    # System prompt is ~1200 tokens, user prompt template ~200 tokens
    # Available for search results: ~4800 tokens ≈ 19,200 chars
    # But we also need completion room, so use ~14,000 chars
    max_search_chars = 14000
    
    if len(raw_search_results) > max_search_chars:
        print(f"  ⚠️  Search results too long ({len(raw_search_results)} chars), truncating to {max_search_chars}")
        # Keep the most important results (early queries are critical checks)
        truncated_results = raw_search_results[:max_search_chars]
        # Try to end at a clean boundary
        last_newline = truncated_results.rfind('\n')
        if last_newline > max_search_chars * 0.8:
            truncated_results = truncated_results[:last_newline]
    else:
        truncated_results = raw_search_results

    # Step 3: Feed to LLM for analysis
    user_message = f"""Analyze these web search results about:
Company: {company_name} | Promoter: {promoter_name} | Sector: {sector}

STRICT RULES (NON-NEGOTIABLE):
- Every finding MUST have a direct quote from the text below
- No quote → do NOT include the finding
- Automatic rejection triggers need OFFICIAL source confirmation
- Unverified allegations → UNVERIFIED section only
- If company has zero bank debt → wilful defaulter/NPA are IMPOSSIBLE
- Start your response with: === QUANTISENSE RESEARCH INTELLIGENCE REPORT ===
- Follow the EXACT output format from your instructions, section by section
- Do NOT add extra sections or change the format

RAW SEARCH RESULTS:
{truncated_results}

Produce the research intelligence report following the EXACT output format specified in your instructions.
Start with: === QUANTISENSE RESEARCH INTELLIGENCE REPORT ===
"""

    result = call_llm(
        agent_name="research",
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message
    )

    print("Research Agent Complete")
    return result, raw_search_results


if __name__ == "__main__":
    # Quick test
    report, raw = run_research_agent("Test Company", "Test Promoter", "manufacturing")
    print(report[:500])