# agents/document_parser.py
# AGENT 1 — Extracts all financial data from uploaded documents
# ENHANCED: Section-based chunking + confidence scoring + source traceability
# Uses deterministic Python-side merging (no LLM for merge step)

import sys, os, re, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import call_llm
from utils.indian_number_parser import parse_indian_amount, extract_percentage, format_indian_amount

# ═══════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Concise, strict output format
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a financial document analyst for Indian corporate credit appraisal.
Extract ALL financial data from the provided documents. Read every line, table, footnote.

YOU MUST output the data in EXACTLY this structured format — fill in every field.
If a value is not found in the text, write "NOT FOUND" for that field. Do NOT skip any field.

=== FINANCIAL EXTRACTION ===

REVENUE_FY_LATEST: [amount with unit]
REVENUE_FY_MINUS1: [amount with unit]
REVENUE_FY_MINUS2: [amount with unit]
EBITDA_FY_LATEST: [amount with unit]
EBITDA_MARGIN_FY_LATEST: [percentage]
PAT_FY_LATEST: [amount with unit]
PAT_FY_MINUS1: [amount with unit]
TOTAL_DEBT: [amount with unit]
NET_WORTH: [amount with unit]
DEBT_EQUITY_RATIO: [ratio]
INTEREST_COVERAGE_RATIO: [ratio]
CFO_FY_LATEST: [amount with unit]
CFO_PAT_RATIO: [ratio]
DEBTOR_DAYS: [number]
INVENTORY_DAYS: [number]
CURRENT_RATIO: [ratio]
GROSS_BLOCK: [amount with unit]
CWIP: [amount with unit]
CWIP_PERCENT_GROSS_BLOCK: [percentage]
FINANCE_COSTS: [amount with unit]
CASH_BALANCE: [amount with unit]

=== GST DATA ===
GSTR1_VS_GSTR3B_VARIANCE: [percentage or NOT FOUND]
MONTHLY_GST_TURNOVER: [amount with unit or NOT FOUND]
ITC_ANOMALY: [description or NOT FOUND]

=== BANK STATEMENT DATA ===
AVG_MONTHLY_BALANCE: [amount or NOT FOUND]
CHEQUE_BOUNCES: [count/description or NOT FOUND]
UNDISCLOSED_EMI: [amount or NOT FOUND]
FUND_ROTATION_FLAG: [YES/NO or NOT FOUND]

=== RED FLAGS ===
AUDITOR_OPINION: [Clean/Qualified/Adverse/Emphasis of Matter or NOT FOUND]
AUDITOR_NAME: [name or NOT FOUND]
RELATED_PARTY_TRANSACTIONS: [amount and percentage of revenue or NOT FOUND]
CFO_VS_PAT: [CFO > PAT / CFO < PAT / NOT FOUND]
CWIP_NOT_CAPITALIZED: [YES/NO with years or NOT FOUND]
CONTINGENT_LIABILITIES: [amount or NOT FOUND]

=== ADDITIONAL DATA ===
CUSTOMER_CONCENTRATION: [top customer % or NOT FOUND]
SUPPLIER_CONCENTRATION: [top supplier % or NOT FOUND]
EMPLOYEE_COUNT: [number or NOT FOUND]
CAPACITY_UTILIZATION: [percentage or NOT FOUND]
ORDER_BOOK: [amount or NOT FOUND]
PROMOTER_SHAREHOLDING: [percentage or NOT FOUND]
PROMOTER_PLEDGE: [percentage or NOT FOUND]
INSURANCE_COVERAGE: [amount or NOT FOUND]
LEGAL_CASES: [description or NOT FOUND]
TAX_DEMANDS: [amount or NOT FOUND]

=== CROSS CHECKS ===
REVENUE_AR_VS_GST_VS_BANK: [match/mismatch description or NOT FOUND]
DEBT_EMI_VS_DECLARED: [match/mismatch or NOT FOUND]
EMPLOYEE_VS_SALARY: [headcount vs salary bill or NOT FOUND]

RULES:
1. Extract EVERY number and data point EXACTLY as found in the text.
2. For EVERY figure, state the unit (Rupees/Lakhs/Crores) as found in text.
3. Only say "NOT FOUND" if data truly does NOT exist in the text.
4. Extract VERBATIM numbers — do not round.
5. If multiple years data exists, include ALL years separated by semicolons.
"""


# ═══════════════════════════════════════════════════════════════
# ALL FIELDS — master list for extraction + merging
# ═══════════════════════════════════════════════════════════════

ALL_FIELDS = [
    # Financials
    "REVENUE_FY_LATEST", "REVENUE_FY_MINUS1", "REVENUE_FY_MINUS2",
    "EBITDA_FY_LATEST", "EBITDA_MARGIN_FY_LATEST",
    "PAT_FY_LATEST", "PAT_FY_MINUS1",
    "TOTAL_DEBT", "NET_WORTH", "DEBT_EQUITY_RATIO", "INTEREST_COVERAGE_RATIO",
    "CFO_FY_LATEST", "CFO_PAT_RATIO",
    "DEBTOR_DAYS", "INVENTORY_DAYS", "CURRENT_RATIO",
    "GROSS_BLOCK", "CWIP", "CWIP_PERCENT_GROSS_BLOCK",
    "FINANCE_COSTS", "CASH_BALANCE",
    # GST
    "GSTR1_VS_GSTR3B_VARIANCE", "MONTHLY_GST_TURNOVER", "ITC_ANOMALY",
    # Bank
    "AVG_MONTHLY_BALANCE", "CHEQUE_BOUNCES", "UNDISCLOSED_EMI", "FUND_ROTATION_FLAG",
    # Red Flags
    "AUDITOR_OPINION", "AUDITOR_NAME", "RELATED_PARTY_TRANSACTIONS",
    "CFO_VS_PAT", "CWIP_NOT_CAPITALIZED", "CONTINGENT_LIABILITIES",
    # Additional
    "CUSTOMER_CONCENTRATION", "SUPPLIER_CONCENTRATION", "EMPLOYEE_COUNT",
    "CAPACITY_UTILIZATION", "ORDER_BOOK", "PROMOTER_SHAREHOLDING",
    "PROMOTER_PLEDGE", "INSURANCE_COVERAGE", "LEGAL_CASES", "TAX_DEMANDS",
    # Cross Checks
    "REVENUE_AR_VS_GST_VS_BANK", "DEBT_EMI_VS_DECLARED", "EMPLOYEE_VS_SALARY",
]

# Section groupings for output formatting
SECTIONS = {
    "FINANCIAL EXTRACTION": [
        "REVENUE_FY_LATEST", "REVENUE_FY_MINUS1", "REVENUE_FY_MINUS2",
        "EBITDA_FY_LATEST", "EBITDA_MARGIN_FY_LATEST",
        "PAT_FY_LATEST", "PAT_FY_MINUS1",
        "TOTAL_DEBT", "NET_WORTH", "DEBT_EQUITY_RATIO", "INTEREST_COVERAGE_RATIO",
        "CFO_FY_LATEST", "CFO_PAT_RATIO",
        "DEBTOR_DAYS", "INVENTORY_DAYS", "CURRENT_RATIO",
        "GROSS_BLOCK", "CWIP", "CWIP_PERCENT_GROSS_BLOCK",
        "FINANCE_COSTS", "CASH_BALANCE",
    ],
    "GST DATA": [
        "GSTR1_VS_GSTR3B_VARIANCE", "MONTHLY_GST_TURNOVER", "ITC_ANOMALY",
    ],
    "BANK STATEMENT DATA": [
        "AVG_MONTHLY_BALANCE", "CHEQUE_BOUNCES", "UNDISCLOSED_EMI", "FUND_ROTATION_FLAG",
    ],
    "RED FLAGS": [
        "AUDITOR_OPINION", "AUDITOR_NAME", "RELATED_PARTY_TRANSACTIONS",
        "CFO_VS_PAT", "CWIP_NOT_CAPITALIZED", "CONTINGENT_LIABILITIES",
    ],
    "ADDITIONAL DATA": [
        "CUSTOMER_CONCENTRATION", "SUPPLIER_CONCENTRATION", "EMPLOYEE_COUNT",
        "CAPACITY_UTILIZATION", "ORDER_BOOK", "PROMOTER_SHAREHOLDING",
        "PROMOTER_PLEDGE", "INSURANCE_COVERAGE", "LEGAL_CASES", "TAX_DEMANDS",
    ],
    "CROSS CHECKS": [
        "REVENUE_AR_VS_GST_VS_BANK", "DEBT_EMI_VS_DECLARED", "EMPLOYEE_VS_SALARY",
    ],
}


# ═══════════════════════════════════════════════════════════════
# SECTION-BASED CHUNKING (replaces character-based splitting)
# ═══════════════════════════════════════════════════════════════

# Natural section boundaries in Indian financial documents
SECTION_MARKERS = [
    "balance sheet", "statement of profit and loss", "profit & loss",
    "profit and loss", "cash flow statement", "notes to accounts",
    "notes forming part", "auditor's report", "auditors' report",
    "independent auditor", "director's report", "directors' report",
    "significant accounting policies", "related party",
    "schedule", "annexure", "gstr", "gst returns",
    "bank statement", "fund flow", "standalone financial",
    "consolidated financial", "management discussion",
]


def _smart_chunk_document(text: str, max_chunk_size: int = 14000) -> list:
    """
    Split document at natural section boundaries instead of arbitrary character counts.
    
    Strategy:
    1. Split by PAGE markers (from pdf_extractor)
    2. Accumulate pages into chunks respecting max_chunk_size
    3. Prefer breaking at section boundaries (Balance Sheet, P&L, etc.)
    4. Fall back to character split for oversized pages
    
    This prevents splitting tables/sections mid-way.
    """
    if not text or not text.strip():
        return [text] if text else []

    # Split by page markers
    page_pattern = re.compile(r'(?=\n={10,}\n---\s*PAGE\s+\d+)')
    pages = page_pattern.split(text)
    pages = [p for p in pages if p.strip()]

    if not pages:
        # No page markers — fall back to character-based
        return [text[i:i + max_chunk_size] for i in range(0, len(text), max_chunk_size)][:15]

    chunks = []
    current_chunk = ""

    for page in pages:
        page_len = len(page)

        # If this single page exceeds max, split it alone
        if page_len > max_chunk_size:
            # Flush current chunk first
            if current_chunk.strip():
                chunks.append(current_chunk)
                current_chunk = ""
            # Split the oversized page
            for i in range(0, page_len, max_chunk_size):
                chunks.append(page[i:i + max_chunk_size])
            continue

        # Check if adding this page would exceed the limit
        if len(current_chunk) + page_len > max_chunk_size:
            # Flush current chunk
            if current_chunk.strip():
                chunks.append(current_chunk)
            current_chunk = page
        else:
            # Check for section marker — start new chunk at key boundaries
            page_lower = page.lower()
            has_section_break = any(marker in page_lower for marker in SECTION_MARKERS)

            if has_section_break and len(current_chunk) > max_chunk_size // 3:
                # We have a meaningful amount in current chunk + we hit a section boundary
                if current_chunk.strip():
                    chunks.append(current_chunk)
                current_chunk = page
            else:
                current_chunk += page

    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk)

    # Cap at 15 chunks (same as before for API cost control)
    return chunks[:15]


# ═══════════════════════════════════════════════════════════════
# FIELD EXTRACTION + MERGING WITH CONFIDENCE
# ═══════════════════════════════════════════════════════════════

def _extract_field(text: str, field_name: str) -> str:
    """Extract a specific field value from structured LLM output."""
    pattern = rf'{re.escape(field_name)}:\s*(.+?)(?:\n|$)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        value = match.group(1).strip()
        if value and value.upper() not in ("NOT FOUND", "NOT AVAILABLE", "NOT AVAILABLE IN DOCUMENTS"):
            return value
    return ""


def _detect_page_reference(chunk_text: str) -> str:
    """Try to extract page number context from a chunk."""
    # Look for page markers like "--- PAGE 12 of 45 ---"
    pages = re.findall(r'PAGE\s+(\d+)', chunk_text[:300])
    if pages:
        if len(pages) == 1:
            return f"page {pages[0]}"
        return f"pages {pages[0]}-{pages[-1]}"
    return ""


def _python_merge_with_confidence(extraction_texts: list, chunk_sources: list) -> tuple:
    """
    Deterministic Python-side merge of multiple chunk extractions.
    
    For each field:
    - Pick the best (most detailed) non-empty value
    - Compute confidence = (chunks that found this) / (total chunks)
    - Track source pages
    
    Returns: (formatted_report_str, confidence_dict)
    """
    confidence_data = {}

    for field in ALL_FIELDS:
        values = []
        sources = []

        for chunk_idx, text in enumerate(extraction_texts):
            value = _extract_field(text, field)
            if value:
                values.append(value)
                source = chunk_sources[chunk_idx] if chunk_idx < len(chunk_sources) else f"chunk {chunk_idx+1}"
                sources.append(source)

        if values:
            best_value = max(values, key=len)
            confidence = round(len(values) / len(extraction_texts), 2)
        else:
            best_value = "Not available in documents"
            confidence = 0.0

        confidence_data[field] = {
            "value": best_value,
            "confidence": confidence,
            "sources": sources,
            "extraction_count": len(values),
            "total_chunks": len(extraction_texts),
        }

    # Build the formatted output (same format as before for downstream compatibility)
    lines = []
    for section_name, fields in SECTIONS.items():
        lines.append(f"\n=== {section_name} ===")
        for field in fields:
            fd = confidence_data[field]
            # Append confidence inline for visibility
            conf_str = f" [confidence: {fd['confidence']:.0%}]" if fd['confidence'] > 0 else ""
            src_str = f" [source: {', '.join(fd['sources'])}]" if fd['sources'] else ""
            lines.append(f"{field}: {fd['value']}{conf_str}{src_str}")

    report = "\n".join(lines)
    return report, confidence_data


# ═══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def run_document_parser(extracted_text: str) -> str:
    """
    Runs the Document Parser Agent on extracted document text.
    
    Enhanced pipeline:
    1. Smart section-based chunking (respects document structure)
    2. LLM extraction per chunk (structured output format)
    3. Deterministic Python-side merge with confidence scoring
    4. Source traceability (page references per field)
    
    Args:
        extracted_text: Combined text from all uploaded PDFs
    
    Returns:
        Structured financial extraction report with confidence scores
    """
    print("🔵 Running Document Parser Agent...")
    print(f"   📊 Total document text length: {len(extracted_text):,} characters")

    # ── Smart chunking at section boundaries ──
    chunks = _smart_chunk_document(extracted_text, max_chunk_size=14000)

    print(f"   📄 Document split into {len(chunks)} chunk(s) (section-aware)")
    for i, c in enumerate(chunks):
        print(f"      Chunk {i+1}: {len(c):,} chars")

    # ── Process each chunk independently ──
    all_extraction_texts = []
    chunk_sources = []

    for i, chunk in enumerate(chunks):
        print(f"  📄 Parsing chunk {i+1}/{len(chunks)} ({len(chunk):,} chars)...")

        # Detect page references in this chunk for source tracking
        page_ref = _detect_page_reference(chunk)
        source_label = f"chunk {i+1}" + (f" ({page_ref})" if page_ref else "")

        user_message = f"""Extract ALL financial data from this document section using the EXACT field format specified.
Fill in EVERY field. Use "NOT FOUND" only if the data truly does not exist in this text.
This is PART {i+1} of {len(chunks)}.

DOCUMENT TEXT:
{chunk}

OUTPUT EVERY FIELD in the exact format specified in your instructions. Do not skip any field.
"""
        result = call_llm(
            agent_name=f"document_parser_chunk_{i+1}",
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message
        )

        # Backward compatibility: keep both prefixes while some runs may still emit legacy provider-specific errors.
        if not (result.startswith("[CEREBRAS ERROR]") or result.startswith("[LLM ERROR]")):
            all_extraction_texts.append(result)
            chunk_sources.append(source_label)
        else:
            print(f"  ⚠️  Chunk {i+1} had error, skipping: {result[:100]}")

    if not all_extraction_texts:
        return "ERROR: Could not extract data from any document chunk."

    # ── Merge with confidence scoring ──
    print("  🔄 Merging extracted data (deterministic Python merge + confidence scoring)...")
    final_result, confidence_data = _python_merge_with_confidence(all_extraction_texts, chunk_sources)

    # ── Summary stats ──
    found_count = sum(1 for f in ALL_FIELDS if confidence_data[f]["confidence"] > 0)
    high_conf = sum(1 for f in ALL_FIELDS if confidence_data[f]["confidence"] >= 0.5)
    total_fields = len(ALL_FIELDS)

    print(f"   📊 Extraction coverage: {found_count}/{total_fields} fields populated")
    print(f"   📊 High confidence (≥50%): {high_conf}/{total_fields} fields")
    print("✅ Document Parser Complete")

    return final_result


if __name__ == "__main__":
    # Quick test with dummy text
    test_text = """
    ========================================
    --- PAGE 1 of 5 ---
    ========================================
    XYZ Manufacturing Ltd - Annual Report 2024
    Revenue: Rs 2,500,000,000 (FY24), Rs 2,100,000,000 (FY23), Rs 1,800,000,000 (FY22)
    EBITDA: Rs 350,000,000 (14% margin)
    PAT: Rs 180,000,000

    ========================================
    --- PAGE 2 of 5 ---
    ========================================
    Balance Sheet
    Total Debt: Rs 850,000,000
    Net Worth: Rs 650,000,000
    Cash from Operations: Rs 120,000,000
    Auditor: S.R. Batliboi & Co. (Clean opinion)
    Related Party Transactions: Rs 80,000,000 (3.2% of revenue)
    """
    result = run_document_parser(test_text)
    print(result)
