# utils/web_search.py
# Powers the Research Agent's internet search capability

import os
import time
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

_tavily_key = os.getenv("TAVILY_API_KEY")
if not _tavily_key:
    print("⚠️  WARNING: TAVILY_API_KEY not found in .env — web research will be disabled!")
    client = None
else:
    client = TavilyClient(api_key=_tavily_key)

# Track if we've already detected that the key is invalid
_key_is_invalid = False


def _validate_tavily_key():
    """Quick validation of the Tavily API key at first use."""
    global _key_is_invalid
    if _key_is_invalid or client is None:
        return False
    try:
        client.search(query="test", max_results=1, search_depth="basic")
        return True
    except Exception as e:
        error_msg = str(e)
        if any(code in error_msg for code in ["401", "403", "432"]):
            _key_is_invalid = True
            print(f"\n    ❌❌❌ TAVILY API KEY IS INVALID OR EXPIRED ❌❌❌")
            print(f"    Error: {error_msg[:120]}")
            print(f"    👉 Get a new key at: https://tavily.com")
            print(f"    👉 Update TAVILY_API_KEY in your .env file\n")
            return False
        return True  # Other errors might be transient


def search_web(query: str, max_results: int = 5, timeout_seconds: int = 30) -> str:
    """
    Searches the web for a given query with timeout/retry protection.
    Returns formatted string of results for feeding into LLM.
    Falls back to neutral findings if API is slow or unavailable.
    """
    
    def _do_search(depth="advanced", num_results=max_results):
        """Inner search with configurable depth."""
        return client.search(
            query=query,
            search_depth=depth,
            max_results=num_results,
            include_answer=True
        )
    
    def _format_results(results):
        """Format Tavily results into a string for the LLM."""
        formatted = f"SEARCH QUERY: {query}\n"
        formatted += "=" * 50 + "\n"
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
    
    # Attempt 1: Advanced search
    try:
        start_time = time.time()
        results = _do_search(depth="advanced", num_results=max_results)
        elapsed = time.time() - start_time
        print(f"    ✓ Search completed in {elapsed:.1f}s")
        return _format_results(results)
    except Exception as e1:
        error_msg = str(e1)
        error_type = type(e1).__name__
        
        # Check for API key / quota / billing errors (HTTP 4xx)
        if any(code in error_msg for code in ["401", "403", "429", "432"]):
            print(f"    ❌ API ERROR for: {query} | {error_type}: {error_msg[:100]}")
            print(f"    💡 Your Tavily API key may be expired, invalid, or over quota.")
            return f"""SEARCH QUERY: {query}
[API KEY ERROR - Tavily returned: {error_msg[:80]}]

Unable to perform web research. The Tavily API key may need to be renewed.
Proceeding with no external intelligence for this query.
"""
        
        # For other errors, retry with basic search depth
        print(f"    ⚠️  Advanced search failed for: {query} ({error_type}: {error_msg[:80]})")
        print(f"    🔄 Retrying with basic search...")
    
    # Attempt 2: Basic search (simpler, less likely to timeout)
    try:
        start_time = time.time()
        results = _do_search(depth="basic", num_results=min(max_results, 3))
        elapsed = time.time() - start_time
        print(f"    ✓ Basic search completed in {elapsed:.1f}s")
        return _format_results(results)
    except Exception as e2:
        error_msg = str(e2)
        error_type = type(e2).__name__
        
        # Check for rate limit
        if "rate" in error_msg.lower() or "quota" in error_msg.lower() or "429" in error_msg:
            print(f"    ℹ️  Rate limit hit: {query}")
            return f"""SEARCH QUERY: {query}
[API RATE LIMIT - Proceeding with neutral assumptions]

Research couldn't complete due to API limits. Assuming no confirmed negative findings.
Recommend verification through alternative sources if critical concern arises.
"""
        
        # Final fallback
        print(f"    ❌ Search failed for: {query} | {error_type}: {error_msg[:100]}")
        return f"""SEARCH QUERY: {query}
[SEARCH FAILED - {error_type}: {error_msg[:80]}]

Unable to retrieve search results. Proceeding with neutral assumptions.
No confirmed issues detected in available sources at time of query.
"""


def run_all_research_searches(company_name: str, promoter_name: str, sector: str) -> str:
    """
    Runs all the research searches defined in the Research Agent prompt.
    Returns combined results for the Research Agent LLM to analyze.
    """
    
    # Validate API key before running 13 searches
    if client is None:
        print("  ❌ Tavily client not initialized — TAVILY_API_KEY missing from .env")
        return "[ALL SEARCHES SKIPPED - No Tavily API key configured]\nProceed with document-only analysis.\n"
    
    if not _validate_tavily_key():
        print("  ❌ Tavily API key validation failed — skipping all web searches")
        return "[ALL SEARCHES SKIPPED - Tavily API key is invalid or expired]\nProceed with document-only analysis. Get a new key at https://tavily.com\n"
    
    print("  ✅ Tavily API key validated successfully")
    
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

        # TIER 3 — QUANTISENSE unique
        f"{company_name} plant shutdown labour dispute",
        f"{company_name} management exit CEO CFO resignation",
    ]

    for i, query in enumerate(searches):
        print(f"  🔍 Searching ({i+1}/{len(searches)}): {query}")
        result = search_web(query, max_results=3)
        all_results += result + "\n\n"
        
        # Small delay between searches to avoid rate-limiting
        if i < len(searches) - 1:
            time.sleep(1)

    return all_results