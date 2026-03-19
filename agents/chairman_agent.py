# agents/chairman_agent.py
# AGENT 5 — Hears the debate, makes the final credit decision

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import call_llm


# Condensed system prompt (~1500 tokens instead of ~3500)
SYSTEM_PROMPT = """You are QUANTISENSE's Chairman Agent — the final credit decision authority.
Weigh Bull vs Bear evidence like a judge. Do NOT simply average positions.

STEP 0 — COMPANY TIER BASELINE:
TIER 1 (listed, Big4, Rs.1000Cr+): +15 bonus. Default=APPROVE unless confirmed evidence otherwise.
TIER 2 (listed, established): +8 bonus. Lean APPROVE.
TIER 3 (SME, unlisted): +0. Neutral.
TIER 4 (first-time): -5.

STEP 1 — VALIDATE TRIGGERS:
- No cited source URL → DISREGARD trigger entirely
- Research confidence LOW/MEDIUM → downgrade to "manual verification"
- Wilful defaulter needs rbi.org.in source
- NCLT needs nclt.gov.in order number
- News alone CANNOT trigger auto-rejection for listed companies
- GST demand notice ≠ fraud. SEBI fine ≠ debarment.

STEP 2 — SCORE 5 PILLARS (MANDATORY — fill every sub-item):

PILLAR 1 — Financial Health (35 pts):
  Revenue Growth 3yr CAGR: >20%=8, 10-20%=6, 0-10%=3, Neg=0
  EBITDA Margin vs sector: Above=7, At=4, Below=1, Neg=0
  Debt/Equity: <1x=7, 1-2x=5, 2-3x=2, >3x=0
  ICR: >4x=7, 2-4x=5, 1-2x=2, <1x=0
  CFO Quality: CFO>PAT=6, ≈PAT=4, <PAT=1, Neg=0

PILLAR 2 — Fraud & Integrity (25 pts):
  Revenue Triangulation: match=10, 1gap=6, 2gaps=2, diverge=0
  Auditor: Clean=7, Emphasis=4, Qualified=1, Adverse=0
  Related Party: <5%=5, 5-15%=3, >15%=0
  Fraud Penalties: apply validated deductions

PILLAR 3 — External Intelligence (20 pts):
  Legal: No issues=8, Minor civil=5, Litigation=2, Criminal=0
  Promoter: Strong=7, Neutral=4, Past failures=1
  Sector: Growing=5, Stable=3, Stressed=1

PILLAR 4 — Management & Ops (10 pts):
  Capacity: >85%=5, 70-85%=4, 40-70%=2, <40%=0
  Management: Strong=3, Average=2, Attrition=0
  Governance: Professional board=2, Family=1

PILLAR 5 — Collateral & Repayment (10 pts):
  Coverage: >2x=4, 1.5-2x=3, 1-1.5x=1, <1x=0
  History: On time=4, Minor delay=2, >30d late=0
  DSCR: >1.5x=2, 1.25-1.5x=1, <1.25x=0

SCORE = Sum(Pillars) + Tier Bonus (cap 100)
85-100=STRONG APPROVE | 70-84=APPROVE | 55-69=CONDITIONAL | 40-54=REFER | <40=REJECT

Rate = Repo(6.5%) + Premium: 85-100→+0.5-1%, 70-84→+1-1.75%, 55-69→+2-3%, 40-54→+3-4%

OUTPUT (all sections mandatory):
=== CHAIRMAN'S VERDICT ===
TRIGGER VALIDATION: [each trigger → CONFIRMED/DISREGARDED + rule]
DEBATE SCORECARD: Bull strongest | Bear strongest | Chairman ruling
CREDIT SCORECARD: [all 5 pillars with sub-scores]
PILLAR SUBTOTAL: __/100
TIER BONUS: +__
QUANTISENSE SCORE: __/100
DECISION: [STRONG APPROVE/APPROVE/CONDITIONAL/REFER/REJECT]
Loan Amount: Rs.___  |  Rate: ___%  |  Tenure: ___mo
CONDITIONS: [list covenants]
CHAIRMAN CONFIDENCE: HIGH/MEDIUM/LOW
"""


def run_chairman_agent(bull_brief: str, bear_brief: str,
                        fraud_output: str, parser_output: str,
                        loan_details: dict, primary_notes: str = "",
                        company_intelligence: dict = None) -> str:
    """
    Runs the Chairman Agent to make the final credit decision.
    """
    print("Weighing Chairman Decision...")

    # Extract company tier info
    tier = "TIER 3"  # Default
    credibility_bonus = 0
    company_intel_text = ""
    if company_intelligence:
        tier = company_intelligence.get('tier', 'TIER 3')
        credibility_bonus = company_intelligence.get('credibility_bonus', 0)
        company_intel_text = company_intelligence.get('analysis_text', '')

    # Truncate all inputs to fit within 8192 token limit
    # System prompt ≈ 1500 tokens, user template ≈ 300 tokens
    # Available for data: ~4400 tokens ≈ 17,600 chars
    max_per_section = 3000

    user_message = f"""Company: {loan_details.get('company_name', 'N/A')}
Loan: Rs.{loan_details.get('loan_amount', 'N/A')} | Purpose: {loan_details.get('loan_purpose', 'N/A')}
Sector: {loan_details.get('sector', 'N/A')} | Tier: {tier} | Bonus: +{credibility_bonus}

MANDATORY INSTRUCTIONS:
1. Start your response with: === CHAIRMAN'S VERDICT ===
2. Complete ALL 5 PILLARS with every sub-score filled in
3. Add tier bonus after pillar subtotal
4. Follow the EXACT output format from your instructions — do not skip any section
5. Fill in every sub-score with a specific number — never leave blank

COMPANY INTEL: {company_intel_text[:2000]}

CREDIT OFFICER NOTES:
{primary_notes[:1500] if primary_notes else "No notes provided."}

BULL BRIEF:
{bull_brief[:max_per_section]}

BEAR BRIEF:
{bear_brief[:max_per_section]}

FRAUD REPORT:
{fraud_output[:max_per_section]}

DOCUMENT SUMMARY:
{parser_output[:max_per_section]}
"""

    result = call_llm("chairman", SYSTEM_PROMPT, user_message)

    # ════════════════════════════════════════════════════════════
    # POST-PROCESSING: TIER 1 GUARDRAIL
    # ════════════════════════════════════════════════════════════
    if tier == "TIER 1":
        result_upper = result.upper()

        has_wilful_default  = "WILFUL DEFAULT" in result_upper and "RBI" in result_upper
        has_nclt_cirp       = "NCLT" in result_upper and "CIRP" in result_upper
        has_sebi_debarment  = "SEBI DEBARMENT" in result_upper and "SEBI.GOV.IN" in result_upper
        has_cbi_charge      = "CBI" in result_upper and "CHARGE SHEET" in result_upper

        critical_issue = has_wilful_default or has_nclt_cirp or has_sebi_debarment or has_cbi_charge

        if not critical_issue and "REJECT" in result_upper:
            print("  Tier 1 company rejected without confirmed critical issues — re-evaluating...")
            re_eval_message = f"""TIER 1 RE-EVALUATION:
Previously recommended REJECTION for {loan_details.get('company_name', 'Unknown')}.
No confirmed critical issues found. For TIER 1:
- Default = APPROVE unless PROVEN otherwise
- Speculative concerns → covenants, not rejection
- Add +{credibility_bonus} tier bonus
Complete all 5 pillars. Convert speculative rejections to covenants.

PREVIOUS ANALYSIS:
{result[:12000]}
"""
            result = call_llm("chairman", SYSTEM_PROMPT, re_eval_message)

    print("Chairman Decision Complete")
    return result