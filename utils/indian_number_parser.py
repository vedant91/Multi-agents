# utils/indian_number_parser.py
# Centralized Indian financial number parser
# Handles: ₹, Rs., Lakhs, Crores, Indian comma format (1,23,45,000)
# Single source of truth — used by document_parser, fraud_detector, and all agents

import re
from typing import Optional, Tuple

# ═══════════════════════════════════════════════════════════════
# PATTERNS
# ═══════════════════════════════════════════════════════════════

# Matches: ₹ 1,23,45,000 | Rs. 250 Crore | 12.3 Cr | 45 Lakhs | (1,234.56)
AMOUNT_PATTERN = re.compile(
    r'[₹Rs.()]*\s*'                         # Optional currency prefix or parens
    r'(-?\d[\d,]*\.?\d*)'                    # The number (with Indian/Western commas)
    r'\s*'
    r'(crores?|cr\.?|lakhs?|lacs?|thousands?|k|millions?|mn|billions?|bn)?',
    re.IGNORECASE
)

UNIT_MULTIPLIERS = {
    'crore':    1_00_00_000,
    'crores':   1_00_00_000,
    'cr':       1_00_00_000,
    'cr.':      1_00_00_000,
    'lakh':     1_00_000,
    'lakhs':    1_00_000,
    'lac':      1_00_000,
    'lacs':     1_00_000,
    'thousand': 1_000,
    'thousands':1_000,
    'k':        1_000,
    'million':  10_00_000,
    'millions': 10_00_000,
    'mn':       10_00_000,
    'billion':  1_00_00_00_000,
    'billions': 1_00_00_00_000,
    'bn':       1_00_00_00_000,
}

# Fields that should NOT be treated as monetary amounts
NON_MONETARY_FIELDS = {
    "DEBT_EQUITY_RATIO", "INTEREST_COVERAGE_RATIO", "CFO_PAT_RATIO",
    "CURRENT_RATIO", "EBITDA_MARGIN_FY_LATEST", "DEBTOR_DAYS",
    "INVENTORY_DAYS", "CWIP_PERCENT_GROSS_BLOCK", "EMPLOYEE_COUNT",
    "CAPACITY_UTILIZATION", "PROMOTER_SHAREHOLDING", "PROMOTER_PLEDGE",
    "GSTR1_VS_GSTR3B_VARIANCE",
}


def parse_indian_amount(text: str) -> Optional[Tuple[float, str, str]]:
    """
    Parse Indian financial amount strings into absolute rupee value.

    Returns: (value_in_rupees, original_text, detected_unit) or None

    Examples:
        "₹ 1,23,45,000"      → (12345000.0, ..., "rupees")
        "Rs. 250 Crore"       → (2500000000.0, ..., "crore")
        "12.3 Cr"             → (123000000.0, ..., "cr")
        "45 Lakhs"            → (4500000.0, ..., "lakh")
        "(1,234.56)"          → (-1234.56, ..., "rupees")   # parens = negative
    """
    if not text:
        return None

    cleaned = text.strip()
    if cleaned.upper() in ("NOT FOUND", "NOT AVAILABLE", "NOT AVAILABLE IN DOCUMENTS", "", "-", "N/A", "NA"):
        return None

    match = AMOUNT_PATTERN.search(cleaned)
    if not match:
        return None

    number_str = match.group(1).replace(',', '')
    unit_str = (match.group(2) or '').lower().rstrip('.')

    try:
        value = float(number_str)
    except ValueError:
        return None

    # Parentheses indicate negative in accounting
    if '(' in cleaned and ')' in cleaned:
        value = -abs(value)

    multiplier = UNIT_MULTIPLIERS.get(unit_str, 1)
    unit_label = unit_str if unit_str else "rupees"

    return (value * multiplier, cleaned, unit_label)


def extract_number(text: str) -> Optional[float]:
    """
    Extract the first number from text, handling Indian formats + units.
    Returns value in absolute rupees.
    
    Drop-in replacement for the old _extract_number() in fraud_detector.py
    """
    result = parse_indian_amount(text)
    if result:
        return result[0]
    return None


def extract_percentage(text: str) -> Optional[float]:
    """
    Extract a percentage value from text.
    Handles: "14%", "14.5 %", "14.5 percent", "14.5"
    """
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.upper() in ("NOT FOUND", "NOT AVAILABLE", "NOT AVAILABLE IN DOCUMENTS", "", "-", "N/A", "NA"):
        return None

    match = re.search(r'[-+]?\d+\.?\d*', cleaned)
    if match:
        return float(match.group())
    return None


def normalize_to_crores(text: str) -> Optional[float]:
    """Convert any Indian amount string to Crores for comparison."""
    result = parse_indian_amount(text)
    if result is None:
        return None
    return round(result[0] / 1_00_00_000, 2)


def normalize_to_lakhs(text: str) -> Optional[float]:
    """Convert any Indian amount string to Lakhs for comparison."""
    result = parse_indian_amount(text)
    if result is None:
        return None
    return round(result[0] / 1_00_000, 2)


def format_indian_amount(amount_rupees: float) -> str:
    """
    Format an absolute rupee value into human-readable Indian format.
    Auto-selects Crore/Lakh/Rupees based on magnitude.
    """
    abs_val = abs(amount_rupees)
    sign = "-" if amount_rupees < 0 else ""

    if abs_val >= 1_00_00_000:
        return f"{sign}₹ {abs_val / 1_00_00_000:,.2f} Crore"
    elif abs_val >= 1_00_000:
        return f"{sign}₹ {abs_val / 1_00_000:,.2f} Lakh"
    else:
        return f"{sign}₹ {abs_val:,.0f}"


# ═══════════════════════════════════════════════════════════════
# QUICK TEST
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    test_cases = [
        "₹ 1,23,45,000",
        "Rs. 250 Crore",
        "12.3 Cr",
        "45 Lakhs",
        "Revenue: 2,500,000,000",
        "(1,234.56)",
        "Rs 850,000,000",
        "3.2% margin",
        "NOT FOUND",
        "",
    ]
    print("=== Indian Number Parser Tests ===\n")
    for tc in test_cases:
        result = parse_indian_amount(tc)
        pct = extract_percentage(tc)
        print(f"  Input: {tc!r:40s} → Amount: {result}  |  Pct: {pct}")
