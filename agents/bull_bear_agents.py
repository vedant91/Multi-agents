# agents/bull_bear_agents.py
# AGENTS 4A & 4B — The Adversarial Debate (QUANTISENSE's Core Innovation)

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import call_llm

# ─────────────────────────────────────────────────────────────
# BULL AGENT PROMPT (condensed to save tokens)
# ─────────────────────────────────────────────────────────────
BULL_SYSTEM_PROMPT = """You are QUANTISENSE's Bull Agent — building the strongest evidence-based case FOR approving this loan.
You are NOT blindly optimistic. You cite real evidence only.

COVER:
1. FINANCIAL STRENGTHS (top 3-5 metrics supporting approval — growth, margins, CFO)
2. BUSINESS QUALITY (customer diversification, contracts, competitive moat)
3. MANAGEMENT QUALITY (track record, transparency, professional team)
4. COLLATERAL STRENGTH (asset quality, coverage ratio, clear title)
5. CONTEXTUAL POSITIVES (industry tailwinds, recovery trajectory)

OUTPUT FORMAT:
=== BULL BRIEF — CASE FOR APPROVAL ===
HEADLINE: APPROVE ₹___ at ___% p.a.

TOP 5 REASONS TO APPROVE:
1. [Financial signal] | Evidence: [specific number]
2. [Business quality] | Evidence: [specific fact]
3. [Management signal] | Evidence: [fact]
4. [Collateral argument] | Evidence: [fact]
5. [Contextual positive] | Evidence: [fact]

REBUTTAL TO EXPECTED BEAR CONCERNS: [Address top 2 likely objections]
RECOMMENDED CONDITIONS: [2 covenants protecting the bank]
BULL CONFIDENCE: HIGH/MEDIUM/LOW
"""

# ─────────────────────────────────────────────────────────────
# BEAR AGENT PROMPT (condensed)
# ─────────────────────────────────────────────────────────────
BEAR_SYSTEM_PROMPT = """You are QUANTISENSE's Bear Agent — the bank's last line of defense.
Find genuine risks based on EVIDENCE. Do NOT invent concerns without data.

INTERROGATION:
1. REVENUE: Can it be traced to bank credits? Growth real or window-dressed?
2. DEBT: Real total debt including guarantees? Undisclosed EMIs?
3. COLLATERAL: Independently valued? Forced sale value? Existing charges?
4. PROJECTIONS: Assumptions vs history? DSCR if rates rise 100bps?
5. PURPOSE: Genuine expansion or debt refinancing?
6. CHARACTER: Document delays? Unexplained RPT? Past exits?

For listed companies with Big 4 auditors: require CONFIRMED evidence, not speculation.

OUTPUT FORMAT:
=== BEAR BRIEF — CASE FOR REJECTION / RESTRICTION ===
HEADLINE: [REJECT / REDUCE TO ₹___ / CONDITIONAL ONLY]

CRITICAL CONCERNS (evidence-based, may justify rejection):
1. [Concern] | Evidence: [data point] | Mitigation: YES/NO
2. [Concern] | Evidence: [data point] | Mitigation: YES/NO

MATERIAL CONCERNS (require covenants):
1. [Concern] | Evidence: [data point] | Proposed Covenant: ___

UNANSWERED QUESTIONS: [Missing information needed]
BEAR'S ARGUMENT: "I recommend [rejection/restriction] because: [3 evidence-based reasons]"
MINIMUM SAFEGUARDS IF OVERRULED: [3 non-negotiable conditions]
BEAR CONFIDENCE: HIGH/MEDIUM/LOW
"""


def run_bull_agent(parser_output: str, fraud_output: str,
                   research_output: str, loan_details: dict,
                   company_tier: str = "TIER 3") -> str:
    """Runs the Bull Agent"""
    print("Running Bull Agent (Case for Approval)...")

    # Truncate inputs to fit within 8192 token context
    # System prompt ≈ 800 tokens, user template ≈ 200 tokens
    # Available for data: ~5200 tokens ≈ 20,800 chars
    max_per_input = 5000
    
    user_message = f"""Company: {loan_details.get('company_name', 'N/A')}
Loan Requested: Rs.{loan_details.get('loan_amount', 'N/A')}
Purpose: {loan_details.get('loan_purpose', 'N/A')}
Sector: {loan_details.get('sector', 'N/A')}
Company Tier: {company_tier}

Build the strongest evidence-based case for APPROVING this loan.
Start your response with: === BULL BRIEF — CASE FOR APPROVAL ===
Follow the EXACT output format from your instructions. Fill in every section.

DOCUMENT ANALYSIS:
{parser_output[:max_per_input]}

FRAUD SCAN:
{fraud_output[:max_per_input]}

RESEARCH:
{research_output[:max_per_input]}
"""

    result = call_llm("bull", BULL_SYSTEM_PROMPT, user_message)
    print("Bull Agent Complete")
    return result


def run_bear_agent(parser_output: str, fraud_output: str,
                   research_output: str, loan_details: dict,
                   company_tier: str = "TIER 3") -> str:
    """Runs the Bear Agent"""
    print("Running Bear Agent (Case for Rejection)...")

    max_per_input = 5000

    user_message = f"""Company: {loan_details.get('company_name', 'N/A')}
Loan Requested: Rs.{loan_details.get('loan_amount', 'N/A')}
Purpose: {loan_details.get('loan_purpose', 'N/A')}
Sector: {loan_details.get('sector', 'N/A')}
Company Tier: {company_tier}
{"NOTE: " + company_tier + " company — concerns MUST have confirmed evidence." if company_tier in ("TIER 1", "TIER 2") else ""}

Find every risk and reason to REJECT or restrict. Cite exact data points.
Start your response with: === BEAR BRIEF — CASE FOR REJECTION / RESTRICTION ===
Follow the EXACT output format from your instructions. Fill in every section.

DOCUMENT ANALYSIS:
{parser_output[:max_per_input]}

FRAUD SCAN:
{fraud_output[:max_per_input]}

RESEARCH:
{research_output[:max_per_input]}
"""

    result = call_llm("bear", BEAR_SYSTEM_PROMPT, user_message)
    print("Bear Agent Complete")
    return result