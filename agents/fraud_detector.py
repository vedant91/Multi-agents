# agents/fraud_detector.py
# AGENT 3 — Detects fraud patterns using outputs from Parser + Research
# DETERMINISTIC VERSION: Python computes ALL scores from extracted fields.
# LLM is ONLY used as a fallback for pattern classification when data exists.

import sys, os, re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import call_llm
from utils.indian_number_parser import extract_number as _extract_number, extract_percentage as _extract_percentage

# ═══════════════════════════════════════════════════════════════
# PATTERN DEFINITIONS — Fully deterministic thresholds
# ═══════════════════════════════════════════════════════════════

PATTERN_NAMES = [
    "Circular Trading",
    "Window Dressing",
    "Related Party Diversion",
    "Fake Capex",
    "Channel Stuffing",
    "Debt Concealment",
    "Inventory Manipulation",
    "Promoter Pledge",
    "Auditor Shopping",
    "Kite Flying",
    "Collateral Fraud",
    "Management Inconsistency",
]

SCORE_MAP = {
    "CONFIRMED": -20,
    "PROBABLE": -12,
    "POSSIBLE": -5,
    "MONITOR": 0,
    "CLEARED": 0,
    "INSUFFICIENT DATA": 0,
}


# _extract_number and _extract_percentage are now imported from
# utils.indian_number_parser — centralized, consistent handling
# of ₹, Lakh, Crore, Indian comma formats across ALL agents.


def _get_field_value(parser_output: str, field_name: str) -> str:
    """Extract a field value from the structured parser output."""
    pattern = rf'{re.escape(field_name)}:\s*(.+?)(?:\n|$)'
    match = re.search(pattern, parser_output, re.IGNORECASE)
    if match:
        val = match.group(1).strip()
        if val.upper() not in ("NOT FOUND", "NOT AVAILABLE", "NOT AVAILABLE IN DOCUMENTS"):
            return val
    return ""


def _evaluate_pattern_1_circular_trading(parser_output: str) -> tuple:
    """Pattern 1: Circular Trading — based on GSTR variance."""
    gstr_var_str = _get_field_value(parser_output, "GSTR1_VS_GSTR3B_VARIANCE")
    if not gstr_var_str:
        return "INSUFFICIENT DATA", "No GSTR variance data available in documents"
    
    variance = _extract_percentage(gstr_var_str)
    if variance is None:
        return "INSUFFICIENT DATA", f"Could not parse GSTR variance: {gstr_var_str}"
    
    if variance < 2:
        return "CLEARED", f"GSTR variance {variance}% (< 2% threshold)"
    elif variance < 5:
        return "MONITOR", f"GSTR variance {variance}% (2-5% range)"
    elif variance < 15:
        return "POSSIBLE", f"GSTR variance {variance}% (5-15% range)"
    elif variance < 40:
        return "PROBABLE", f"GSTR variance {variance}% (15-40% range)"
    else:
        return "CONFIRMED", f"GSTR variance {variance}% (> 40%!)"


def _evaluate_pattern_2_window_dressing(parser_output: str) -> tuple:
    """Pattern 2: Window Dressing — based on Q4 revenue spike."""
    # Check if we have quarterly data or monthly GST data
    monthly_turnover = _get_field_value(parser_output, "MONTHLY_GST_TURNOVER")
    if not monthly_turnover:
        return "INSUFFICIENT DATA", "No quarterly/monthly revenue data available for Q4 spike analysis"
    return "MONITOR", f"Monthly GST turnover data found: {monthly_turnover[:100]}. Manual review recommended for Q4 spike."


def _evaluate_pattern_3_related_party(parser_output: str) -> tuple:
    """Pattern 3: Related Party Diversion — based on RPT % of revenue."""
    rpt_str = _get_field_value(parser_output, "RELATED_PARTY_TRANSACTIONS")
    if not rpt_str:
        return "INSUFFICIENT DATA", "No related party transaction data available"
    
    # Try to extract percentage
    pct = _extract_percentage(rpt_str)
    if pct is not None:
        if pct < 5:
            return "CLEARED", f"RPT at {pct}% of revenue (< 5% threshold)"
        elif pct < 15:
            return "MONITOR", f"RPT at {pct}% of revenue (5-15% range)"
        elif pct < 30:
            return "PROBABLE", f"RPT at {pct}% of revenue (15-30% range)"
        else:
            return "CONFIRMED", f"RPT at {pct}% of revenue (> 30%!)"
    
    return "MONITOR", f"RPT data found but percentage not extractable: {rpt_str[:100]}"


def _evaluate_pattern_4_fake_capex(parser_output: str) -> tuple:
    """Pattern 4: Fake Capex — CWIP as percentage of gross block."""
    cwip_pct_str = _get_field_value(parser_output, "CWIP_PERCENT_GROSS_BLOCK")
    cwip_str = _get_field_value(parser_output, "CWIP")
    gross_str = _get_field_value(parser_output, "GROSS_BLOCK")
    cwip_not_cap = _get_field_value(parser_output, "CWIP_NOT_CAPITALIZED")
    
    # Try direct percentage first
    pct = _extract_percentage(cwip_pct_str)
    
    # If not available, compute from CWIP and Gross Block
    if pct is None and cwip_str and gross_str:
        cwip_val = _extract_number(cwip_str)
        gross_val = _extract_number(gross_str)
        if cwip_val is not None and gross_val is not None and gross_val > 0:
            pct = (cwip_val / gross_val) * 100
    
    if pct is None:
        return "INSUFFICIENT DATA", "No CWIP or Gross Block data available"
    
    evidence = f"CWIP is {pct:.1f}% of Gross Block"
    
    # Check if CWIP has not been capitalized
    if cwip_not_cap and "YES" in cwip_not_cap.upper():
        if "3" in cwip_not_cap or "4" in cwip_not_cap or "5" in cwip_not_cap:
            return "CONFIRMED", f"{evidence}. CWIP not capitalized for 3+ years"
        elif "2" in cwip_not_cap:
            return "PROBABLE", f"{evidence}. CWIP not capitalized for 2 years"
        else:
            return "MONITOR", f"{evidence}. CWIP not being capitalized"
    
    if pct < 15:
        return "CLEARED", f"{evidence} (< 15% threshold)"
    else:
        return "MONITOR", f"{evidence} (>= 15%, needs capitalization timeline review)"


def _evaluate_pattern_5_channel_stuffing(parser_output: str) -> tuple:
    """Pattern 5: Channel Stuffing — based on debtor days."""
    debtor_str = _get_field_value(parser_output, "DEBTOR_DAYS")
    if not debtor_str:
        return "INSUFFICIENT DATA", "No debtor days data available"
    
    days = _extract_number(debtor_str)
    if days is None:
        return "INSUFFICIENT DATA", f"Could not parse debtor days: {debtor_str}"
    
    if days < 90:
        return "CLEARED", f"Debtor days at {days:.0f} (< 90 threshold)"
    elif days < 120:
        return "POSSIBLE", f"Debtor days at {days:.0f} (90-120 range)"
    elif days < 180:
        return "PROBABLE", f"Debtor days at {days:.0f} (120-180 range)"
    else:
        return "CONFIRMED", f"Debtor days at {days:.0f} (> 180!)"


def _evaluate_pattern_6_debt_concealment(parser_output: str) -> tuple:
    """Pattern 6: Debt Concealment — EMI gap."""
    emi_str = _get_field_value(parser_output, "DEBT_EMI_VS_DECLARED")
    undisclosed = _get_field_value(parser_output, "UNDISCLOSED_EMI")
    
    if undisclosed:
        emi_val = _extract_number(undisclosed)
        if emi_val is not None and emi_val > 0:
            return "PROBABLE", f"Undisclosed EMI detected: {undisclosed}"
    
    if not emi_str:
        return "INSUFFICIENT DATA", "No EMI gap data available"
    
    if "match" in emi_str.lower() or "clear" in emi_str.lower():
        return "CLEARED", f"EMI data matches declared debt: {emi_str[:100]}"
    elif "mismatch" in emi_str.lower() or "gap" in emi_str.lower():
        return "POSSIBLE", f"EMI gap detected: {emi_str[:100]}"
    
    return "MONITOR", f"EMI data: {emi_str[:100]}"


def _evaluate_pattern_7_inventory(parser_output: str) -> tuple:
    """Pattern 7: Inventory Manipulation — based on inventory days."""
    inv_str = _get_field_value(parser_output, "INVENTORY_DAYS")
    if not inv_str:
        return "INSUFFICIENT DATA", "No inventory days data available"
    
    days = _extract_number(inv_str)
    if days is None:
        return "INSUFFICIENT DATA", f"Could not parse inventory days: {inv_str}"
    
    # Simple threshold check (without YoY comparison since we may not have prior year)
    if days < 60:
        return "CLEARED", f"Inventory days at {days:.0f} (within normal range)"
    elif days < 120:
        return "MONITOR", f"Inventory days at {days:.0f} (elevated, monitor)"
    elif days < 180:
        return "POSSIBLE", f"Inventory days at {days:.0f} (high, needs review)"
    else:
        return "PROBABLE", f"Inventory days at {days:.0f} (very high!)"


def _evaluate_pattern_8_promoter_pledge(parser_output: str) -> tuple:
    """Pattern 8: Promoter Pledge."""
    pledge_str = _get_field_value(parser_output, "PROMOTER_PLEDGE")
    shareholding_str = _get_field_value(parser_output, "PROMOTER_SHAREHOLDING")
    
    if not pledge_str and not shareholding_str:
        return "INSUFFICIENT DATA", "No promoter shareholding/pledge data available"
    
    if pledge_str:
        pct = _extract_percentage(pledge_str)
        if pct is not None:
            if pct < 10:
                return "CLEARED", f"Promoter pledge at {pct}% (< 10%)"
            elif pct < 50:
                return "MONITOR", f"Promoter pledge at {pct}% (10-50% range)"
            else:
                return "PROBABLE", f"Promoter pledge at {pct}% (> 50%!)"
        # Check for keywords
        if "nil" in pledge_str.lower() or "zero" in pledge_str.lower() or "0%" in pledge_str:
            return "CLEARED", f"No promoter pledge: {pledge_str[:100]}"
    
    if shareholding_str:
        return "MONITOR", f"Promoter shareholding: {shareholding_str[:100]}. Pledge data not separately available."
    
    return "INSUFFICIENT DATA", "Promoter pledge percentage not extractable"


def _evaluate_pattern_9_auditor_shopping(parser_output: str) -> tuple:
    """Pattern 9: Auditor Shopping."""
    auditor_opinion = _get_field_value(parser_output, "AUDITOR_OPINION")
    auditor_name = _get_field_value(parser_output, "AUDITOR_NAME")
    
    if not auditor_opinion and not auditor_name:
        return "INSUFFICIENT DATA", "No auditor data available"
    
    evidence_parts = []
    if auditor_name:
        evidence_parts.append(f"Auditor: {auditor_name}")
    if auditor_opinion:
        evidence_parts.append(f"Opinion: {auditor_opinion}")
    
    evidence = "; ".join(evidence_parts)
    
    if auditor_opinion:
        opinion_lower = auditor_opinion.lower()
        if "adverse" in opinion_lower:
            return "CONFIRMED", f"Adverse audit opinion. {evidence}"
        elif "qualified" in opinion_lower or "qualification" in opinion_lower:
            return "POSSIBLE", f"Qualified audit opinion. {evidence}"
        elif "emphasis" in opinion_lower:
            return "MONITOR", f"Emphasis of matter in audit. {evidence}"
        elif "clean" in opinion_lower or "unqualified" in opinion_lower or "unmodified" in opinion_lower:
            return "CLEARED", f"Clean audit opinion. {evidence}"
    
    return "MONITOR", evidence


def _evaluate_pattern_10_kite_flying(parser_output: str) -> tuple:
    """Pattern 10: Kite Flying — WC utilization."""
    fund_rotation = _get_field_value(parser_output, "FUND_ROTATION_FLAG")
    
    if fund_rotation:
        if "YES" in fund_rotation.upper():
            return "PROBABLE", f"Fund rotation flag raised: {fund_rotation[:100]}"
        elif "NO" in fund_rotation.upper():
            return "CLEARED", "No fund rotation detected in bank statements"
    
    return "INSUFFICIENT DATA", "No WC utilization or fund rotation data available"


def _evaluate_pattern_11_collateral_fraud(parser_output: str) -> tuple:
    """Pattern 11: Collateral Fraud."""
    insurance_str = _get_field_value(parser_output, "INSURANCE_COVERAGE")
    
    if not insurance_str:
        return "INSUFFICIENT DATA", "No collateral/insurance data available"
    
    return "MONITOR", f"Insurance/collateral data: {insurance_str[:100]}. Manual valuation verification needed."


def _evaluate_pattern_12_management_inconsistency(parser_output: str) -> tuple:
    """Pattern 12: Management Inconsistency — Capacity utilization."""
    cap_util_str = _get_field_value(parser_output, "CAPACITY_UTILIZATION")
    emp_vs_salary = _get_field_value(parser_output, "EMPLOYEE_VS_SALARY")
    
    evidence_parts = []
    if cap_util_str:
        evidence_parts.append(f"Capacity utilization: {cap_util_str}")
    if emp_vs_salary:
        evidence_parts.append(f"Employee vs salary: {emp_vs_salary}")
    
    if not evidence_parts:
        return "INSUFFICIENT DATA", "No capacity utilization or employee data available for verification"
    
    evidence = "; ".join(evidence_parts)
    
    if cap_util_str:
        pct = _extract_percentage(cap_util_str)
        if pct is not None:
            if pct < 20:
                return "POSSIBLE", f"Very low capacity utilization at {pct}%. {evidence}"
            elif pct > 100:
                return "POSSIBLE", f"Capacity utilization exceeds 100% ({pct}%). {evidence}"
    
    return "MONITOR", evidence


# Map pattern index to evaluation function
PATTERN_EVALUATORS = {
    0: _evaluate_pattern_1_circular_trading,
    1: _evaluate_pattern_2_window_dressing,
    2: _evaluate_pattern_3_related_party,
    3: _evaluate_pattern_4_fake_capex,
    4: _evaluate_pattern_5_channel_stuffing,
    5: _evaluate_pattern_6_debt_concealment,
    6: _evaluate_pattern_7_inventory,
    7: _evaluate_pattern_8_promoter_pledge,
    8: _evaluate_pattern_9_auditor_shopping,
    9: _evaluate_pattern_10_kite_flying,
    10: _evaluate_pattern_11_collateral_fraud,
    11: _evaluate_pattern_12_management_inconsistency,
}


def format_fraud_report(parsed: dict) -> str:
    """Format the parsed fraud results into a clean report."""
    lines = ["=== QUANTISENSE FRAUD DETECTION REPORT ===\n"]
    lines.append("FRAUD PATTERN SCAN:\n")
    
    for i, p in enumerate(parsed["patterns"], 1):
        lines.append(f"Pattern {i} - {p['name']}: {p['status']}")
        lines.append(f"  Evidence: {p['evidence']}")
        lines.append(f"  Score Impact: {p['score_impact']}\n")
    
    lines.append(f"TOTAL FRAUD PENALTY: {parsed['total_penalty']} points")
    threshold_status = "ABOVE" if parsed['total_penalty'] <= -30 else "BELOW"
    lines.append(f"(Rejection threshold is -30. Current total: {parsed['total_penalty']}. Status: {threshold_status} threshold.)\n")
    
    lines.append(f"FRAUD and INTEGRITY SCORE: {parsed['fraud_score']}/25")
    lines.append(f"OVERALL FRAUD RISK: {parsed['overall_risk']}\n")
    lines.append(f"RECOMMENDATION TO COMMITTEE: {parsed['recommendation']}")
    
    return "\n".join(lines)


def run_fraud_detector(parser_output: str, research_output: str,
                        primary_notes: str = "",
                        company_tier: str = "TIER 3") -> str:
    """
    Runs the Fraud Detection Agent.
    
    100% DETERMINISTIC: All scoring is done by Python functions using
    extracted field values. No LLM is used for scoring.
    This ensures identical results for identical inputs, every time.
    """
    print("Running Fraud Detection Agent...")

    patterns = []
    total_penalty = 0
    
    # Evaluate each pattern using deterministic Python functions
    for i, name in enumerate(PATTERN_NAMES):
        evaluator = PATTERN_EVALUATORS[i]
        status, evidence = evaluator(parser_output)
        
        # For TIER 1/2, be more lenient — don't act on MONITOR-level signals
        if company_tier in ("TIER 1", "TIER 2"):
            if status == "POSSIBLE":
                # Downgrade POSSIBLE to MONITOR for established companies
                # unless it's a really serious pattern
                if i not in [0, 2, 5]:  # Keep POSSIBLE for circular trading, RPT, debt concealment
                    status = "MONITOR"
                    evidence += f" [Downgraded from POSSIBLE for {company_tier} company]"
        
        score_impact = SCORE_MAP.get(status, 0)
        total_penalty += score_impact
        
        patterns.append({
            "name": name,
            "status": status,
            "evidence": evidence,
            "score_impact": score_impact
        })
    
    # Compute fraud score (25 max, minimum 0)
    fraud_score = max(0, 25 + total_penalty)
    
    # Determine risk level
    if total_penalty <= -30:
        overall_risk = "CRITICAL"
        recommendation = "ESCALATE FOR INVESTIGATION"
    elif total_penalty <= -13:
        overall_risk = "HIGH"
        recommendation = "PROCEED WITH HEIGHTENED SCRUTINY"
    elif total_penalty <= -5:
        overall_risk = "MEDIUM"
        recommendation = "PROCEED TO DEBATE"
    else:
        overall_risk = "LOW"
        recommendation = "PROCEED TO DEBATE"
    
    parsed = {
        "patterns": patterns,
        "total_penalty": total_penalty,
        "fraud_score": fraud_score,
        "overall_risk": overall_risk,
        "recommendation": recommendation,
    }
    
    report = format_fraud_report(parsed)
    
    print(f"  📊 Fraud Penalty: {total_penalty}, Score: {fraud_score}/25, Risk: {overall_risk}")
    print("Fraud Detection Complete")
    return report