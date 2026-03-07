# agents/company_intelligence.py
# NEW AGENT: Analyzes company tier and applies baseline scoring
# Fixes: Infosys should NEVER be rejected for speculative reasons

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import call_llm

SYSTEM_PROMPT = """
You are SENTINEL's Company Intelligence Agent.
Your job: Classify the company into a tier and apply baseline credibility multipliers.

This fixes a critical bug: Infosys (30-year-old listed IT giant with $20B+ revenue)
was being rejected by speculative bear concerns. That should NEVER happen.

════════════════════════════════════════════════════════════
COMPANY TIER CLASSIFICATION (from research results + web data)
════════════════════════════════════════════════════════════

TIER 1: ESTABLISHMENT POWERHOUSES
Company characteristics:
- Listed on BSE 500 / NSE 200
- Auditor: Big 4 (Deloitte, EY, PwC, KPMG)
- Revenue: >₹1000 crore annual
- History: 20+ years in continuous operation
- Examples: TCS, Infosys, Reliance, HDFC Bank, LT Ltd

Impact on scoring:
  ✓ Automatic +15 bonus points (Foundation credibility)
  ✓ Research agent findings REQUIRE official sources (no news allegations)
  ✓ Bear agent concerns must be CONFIRMED (not "possible")
  ✓ Default decision: APPROVE unless CONFIRMED critical issue
  ✓ Hallucinated findings automatically disregarded

TIER 2: SOLID MID-CAP COMPANIES
Company characteristics:
- Listed on BSE/NSE (any cap, but >₹500 crore market cap)
- Auditor: Big 4 OR reputable local firm
- Revenue: ₹100-1000 crore
- History: 10+ years operating
- Examples: Mid-cap banking stocks, pharma companies, auto suppliers

Impact on scoring:
  ✓ Automatic +8 bonus points
  ✓ Research requires credible sources (RBI, ministry, court official)
  ✓ Bear concerns must have supporting evidence
  ✓ Default: CONDITIONAL → APPROVAL path (easier to move toward approval)

TIER 3: PRIVATE / SMALL CAP COMPANIES
Company characteristics:
- Not listed OR listed on smaller boards
- Revenue: <₹100 crore
- History: 3-10 years
- Auditor: Local firm acceptable

Impact on scoring:
  ✓ No bonus points
  ✓ Standard scrutiny applied
  ✓ All research findings treated equally
  ✓ Bear concerns weight more heavily

TIER 4: STARTUPS / NEW VENTURES
Company characteristics:
- < 3 years operating OR < ₹10 crore revenue
- Limited track record

Impact on scoring:
  ✓ Higher scrutiny
  ✓ Smaller loan amounts recommended
  ✓ Collateral requirements stricter

════════════════════════════════════════════════════════════
YOUR ANALYSIS FORMAT
════════════════════════════════════════════════════════════

=== COMPANY INTELLIGENCE REPORT ===

COMPANY TIER: [TIER 1 / TIER 2 / TIER 3 / TIER 4]

TIER JUSTIFICATION:
- Listed Status: [YES / NO + exchange]
- Auditor: [Big 4 / Reputable / Local / Unknown]
- Revenue Size: [estimate from research]
- Track Record: [years of operation]
- Key credibility signals: [if any]

CREDIBILITY MULTIPLIER: +___ points to baseline credit score
(This is applied AFTER excluding hallucinated findings)

IMPLICATIONS FOR THIS APPLICATION:
1. Research Agent findings: [must have cited sources / all sources accepted / standard scrutiny]
2. Bear Agent concerns: [require confirmed evidence / can be speculative / standard]
3. Default outcome: [APPROVE unless confirmed issue / REFER if concerns exist / standard evaluation]
4. Hallucination risk: [VERY LOW (listed, big4) / LOW / MEDIUM / HIGH]

VALIDATION RULES SPECIFIC TO THIS TIER:
[List 2-3 extra validation rules based on tier]

OVERALL ASSESSMENT:
[2 sentences on why this tier classification matters for this loan decision]
"""

def run_company_intelligence(company_name: str, research_output: str) -> dict:
    """
    Analyzes company tier and returns credibility adjustments.

    Args:
        company_name: Company name
        research_output: Research agent output (contains web findings)

    Returns:
        dict with:
        - tier: "TIER 1" / "TIER 2" / "TIER 3" / "TIER 4"
        - credibility_bonus: int (points to add to final score)
        - research_threshold: "official_sources_only" / "credible_sources" / "standard"
        - bear_threshold: "confirmed_only" / "evidence_required" / "standard"
        - default_direction: "approve" / "conditional_to_approve" / "neutral" / "scrutiny"
        - analysis_text: full analysis
    """
    print("Running Company Intelligence Agent...")

    user_message = f"""
Analyze company tier for:
Company: {company_name}

Research data (may contain listings status, auditor info):
{research_output[:2000]}

Classify into TIER 1-4 and determine credibility multiplier for this loan decision.
Focus on: Listed status, auditor type, revenue size, track record.
"""

    analysis = call_llm("company_intelligence", SYSTEM_PROMPT, user_message)

    # Parse the response to extract tier
    tier = "TIER 3"  # Default
    bonus = 0
    research_threshold = "standard"
    bear_threshold = "standard"
    default_direction = "neutral"

    # Simple parsing (LLM should output clearly)
    analysis_upper = analysis.upper()
    if "TIER 1" in analysis_upper:
        tier = "TIER 1"
        bonus = 15
        research_threshold = "official_sources_only"
        bear_threshold = "confirmed_only"
        default_direction = "approve"
    elif "TIER 2" in analysis_upper:
        tier = "TIER 2"
        bonus = 8
        research_threshold = "credible_sources"
        bear_threshold = "evidence_required"
        default_direction = "conditional_to_approve"
    elif "TIER 3" in analysis_upper:
        tier = "TIER 3"
        bonus = 0
        research_threshold = "standard"
        bear_threshold = "standard"
        default_direction = "neutral"
    elif "TIER 4" in analysis_upper:
        tier = "TIER 4"
        bonus = -5
        research_threshold = "standard"
        bear_threshold = "standard"
        default_direction = "scrutiny"

    print(f"Company Intelligence Complete: {tier} (+{bonus} pts)")

    return {
        "tier": tier,
        "credibility_bonus": bonus,
        "research_threshold": research_threshold,
        "bear_threshold": bear_threshold,
        "default_direction": default_direction,
        "analysis_text": analysis
    }
