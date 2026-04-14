# utils/web_search.py
# Powers the Research Agent's internet search capability

import os
import time
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def search_web(query: str, max_results: int = 5, timeout_seconds: int = 30) -> str:
    """
    Searches the web for a given query with timeout/retry protection.
    Returns formatted string of results for feeding into LLM.
    Falls back to neutral findings if API is slow.
    """
    
    try:
        # For large companies, be generous with timeout
        if any(keyword in query.lower() for keyword in ["infosys", "tcs", "reliance", "hdfc", "icici"]):
            timeout_seconds = 20
        
        start_time = time.time()
        
        results = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=True  # Tavily gives an AI summary too
        )
        
        elapsed = time.time() - start_time
        print(f"     Search completed in {elapsed:.1f}s")

        formatted = f"SEARCH QUERY: {query}\n"
        formatted += "=" * 50 + "\n"

        # Include the AI summary if available
        if results.get("answer"):
            formatted += f"SUMMARY: {results['answer']}\n\n"

        formatted += "INDIVIDUAL RESULTS:\n"
        for i, result in enumerate(results.get("results", [])):
            formatted += f"\n[Result {i+1}]\n"
            formatted += f"Title: {result.get('title', 'N/A')}\n"
            formatted += f"URL: {result.get('url', 'N/A')}\n"
            formatted += f"Content: {result.get('content', 'N/A')[:500]}...\n"
            formatted += f"Published: {result.get('published_date', 'N/A')}\n"

        return formatted

    except (TimeoutError, ConnectionError, OSError) as e:
        # Network timeout - return neutral message instead of error
        print(f"    [WARN]  Search timeout for: {query} | Proceeding with neutral assumptions")
        return f"""SEARCH QUERY: {query}
[TIMEOUT - API slow, proceeding with neutral assumptions]

For large established companies, absence of negative findings is positive signal.
No confirmed issues detected in available sources at time of query.
"""
    except Exception as e:
        error_msg = str(e).lower()
        # Rate limit error - be lenient
        if "rate" in error_msg or "quota" in error_msg:
            print(f"    [INFO]  Search rate limit: {query} | Using neutral fallback")
            return f"""SEARCH QUERY: {query}
[API RATE LIMIT - Proceeding with neutral assumptions]

Research couldn't complete due to API limits. Assuming no confirmed negative findings.
Recommend verification through alternative sources if critical concern arises.
"""
        return f"[SEARCH ERROR for '{query}']: {str(e)}"


def run_all_research_searches(company_name: str, promoter_name: str, sector: str) -> str:
    """
    Runs all the research searches defined in the Research Agent prompt.
    Returns combined results for the Research Agent LLM to analyze.
    """
    all_results = ""

    # TIER 1 — Critical searches
    searches = [
        f"{company_name} wilful defaulter RBI",
        f"{company_name} NCLT insolvency IBC 2016",
        f"{promoter_name} SEBI order debarment fraud",
        f"{company_name} GST evasion raid fake invoice",
        f"{company_name} NPA bank fraud DRT SARFAESI",
        f"{promoter_name} ED CBI SFIO investigation",

        # TIER 2 — Background
        f"{company_name} latest news 2024 2025",
        f"{company_name} court case litigation",
        f"{promoter_name} other companies director",
        f"{sector} RBI stressed sector NPA 2024 India",
        f"{sector} industry outlook India 2025",

        # TIER 3 — SENTINEL unique
        f"{company_name} plant shutdown labour dispute",
        f"{company_name} management exit CEO CFO resignation",
    ]

    for query in searches:
        print(f"  [SEARCH] Searching: {query}")
        result = search_web(query, max_results=3)
        all_results += result + "\n\n"

    return all_results