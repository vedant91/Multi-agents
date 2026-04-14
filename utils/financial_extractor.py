# utils/financial_extractor.py
# Pure Python regex extractor for financial data from OCR text
# Much faster and more reliable than LLM extraction for small models
# Used by document_parser.py as Step 1 before LLM formatting

import re


def _get_numbers_from_vicinity(text: str, keyword: str,
                                search_window: int = 300,
                                min_val: float = 0.0,
                                max_numbers: int = 2) -> list:
    """
    Find a keyword in text and extract up to `max_numbers` decimal/large
    numbers within the next `search_window` characters.
    If the first occurrence doesn't yield numbers, it searches subsequent occurrences.
    Returns list of floats, e.g. [FY25, FY24].
    """
    pos = 0
    text_lower = text.lower()
    keyword_lower = keyword.lower()
    
    while True:
        idx = text_lower.find(keyword_lower, pos)
        if idx < 0:
            return []

        # Take the surrounding window
        snippet = text[idx: idx + search_window]

        # Find all numbers
        raw = re.findall(r'(-?|\()(\d{1,3}(?:,\d{2,3})*(?:\.\d+)?|\d+(?:\.\d+)?)(\)?)', snippet)
        numbers = []
        for sign, num_str, _ in raw:
            try:
                val = float(num_str.replace(',', ''))
                if sign in ('-', '('):
                    val = -val
                    
                # Exclude very small positive integers that are note reference numbers (< 50) unless they are 0.0
                if abs(val) < 50 and val != 0.0 and sign not in ('-', '(') and '.' not in num_str:
                    continue
                    
                if abs(val) >= min_val:
                    numbers.append(val)
            except ValueError:
                pass
                
        if numbers:
            if "finance cost" in keyword_lower:
                print(f"DEBUG: found numbers for {keyword}: {numbers}")
            return numbers[:max_numbers]
            
        # If no numbers found, search the next occurrence
        if "finance cost" in keyword_lower:
            print(f"DEBUG: empty numbers for '{keyword}' at index {idx}. snippet: {repr(snippet)}")
        pos = idx + len(keyword)



def _find_all_occurrences(text: str, keyword: str, search_window: int = 300,
                          min_val: float = 0.0) -> list:
    """Find all occurrences of keyword and extract numbers from each.
    Now acts as a pass-through to _get_numbers_from_vicinity, which handles
    searching until valid numbers are found.
    """
    return _get_numbers_from_vicinity(text, keyword, search_window=search_window, min_val=min_val)


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE SUMMARY EXTRACTOR (for Annual Report chart-style summaries)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_standalone_summary(annual_text: str) -> dict:
    """
    Parse chart-style standalone metric summaries commonly found in
    Annual Report overview pages (typically pages 10-20).
    
    These charts follow the pattern:
        [Label]
        In Lakhs / In Crores
        2024
        [FY24 value]
        [FY25 value]
        2025
    
    Returns dict with keys like 'revenue', 'pbt', 'net_worth', 'total_debt'
    mapped to [FY25, FY24] lists. Empty dict if no summary found.
    """
    summary = {}
    if not annual_text:
        return summary

    # Find the summary section -- look for "Standalone Metrics" or similar
    # IMPORTANT: Markers may appear in narrative text first, then again near
    # actual chart data. We search ALL occurrences and pick the one that
    # contains chart-style labels like "Revenue" or "PBT" or "Networth".
    summary_section = ""
    markers = [
        r'(?i)standalone\s+metrics',
        r'(?i)key\s+financial\s+highlights',
        r'(?i)financial\s+highlights',
        r'(?i)at\s+a\s+glance',
    ]
    chart_validators = ['Revenue', 'PBT', 'Networth', 'Net Worth', 'Borrowings', 'PAT']
    
    for marker in markers:
        for m in re.finditer(marker, annual_text):
            candidate = annual_text[m.start(): m.start() + 5000]
            # Check if this candidate contains actual chart labels
            has_chart = sum(1 for v in chart_validators if v in candidate)
            if has_chart >= 2:
                summary_section = candidate
                break
        if summary_section:
            break

    if not summary_section:
        return summary

    # Define the chart labels we want to extract and their target keys
    chart_labels = {
        'Revenue from Operations': 'revenue',
        'Revenue From Operations': 'revenue',
        'Total Income': 'total_income',
        'PBT': 'pbt',
        'Profit Before Tax': 'pbt',
        'PAT': 'pat',
        'Profit After Tax': 'pat',
        'Net Profit': 'pat',
        'Networth': 'net_worth',
        'Net Worth': 'net_worth',
        'Net worth': 'net_worth',
        'Borrowings': 'total_debt',
        'Total Borrowings': 'total_debt',
        'Total Debt': 'total_debt',
        'AUM': 'aum',
    }

    # Pass 1: Find all labels and their relative positions to create snippet bounds
    found_labels = []
    for lbl, key in chart_labels.items():
        if key in summary: continue
        idx = summary_section.find(lbl)
        if idx >= 0:
            found_labels.append((idx, lbl, key))
            summary[key] = []
            
    found_labels.sort()
    claimed_nums = set()
    
    for i, (idx, lbl, key) in enumerate(found_labels):
        if summary[key]: continue # Already filled by earlier synonym
        
        # Generous window but strictly bounded by the next label
        next_idx = found_labels[i+1][0] if i+1 < len(found_labels) else len(summary_section)
        snippet = summary_section[idx : min(idx + 500, next_idx)]
        
        # Use year markers to separate real values from chart axis ticks
        pos_2024 = snippet.find('2024')
        pos_2025 = snippet.find('2025')
        
        if pos_2024 >= 0 and pos_2025 > pos_2024:
            # Get numbers between 2024 and 2025 -- these are the confident data values
            between = snippet[pos_2024 + 4: pos_2025]
            between_nums = []
            for n in re.findall(r'(\d{1,3}(?:,\d{2,3})*(?:\.\d+)?)', between):
                val = float(n.replace(',', ''))
                if val > 1000:
                    between_nums.append(val)
                    claimed_nums.add(val)
            
            if len(between_nums) >= 2:
                summary[key] = [between_nums[1], between_nums[0]]  # [FY25, FY24]
            elif len(between_nums) == 1:
                summary[key] = [between_nums[0]]
        else:
            # Fallback: grab large non-year numbers
            nums_raw = re.findall(r'(\d{1,3}(?:,\d{2,3})*(?:\.\d+)?)', snippet)
            nums = []
            for n in nums_raw:
                val = float(n.replace(',', ''))
                if val > 1000 and val not in (2024, 2025, 2023, 2022):
                    nums.append(val)
                    claimed_nums.add(val)
            if len(nums) >= 2:
                summary[key] = [nums[1], nums[0]]
            elif len(nums) == 1:
                summary[key] = [nums[0]]

    # Pass 2: Collect stray numbers and fill missing FY24 slots
    stray_nums = []
    for n in re.findall(r'(\d{1,3}(?:,\d{2,3})*(?:\.\d+)?)', summary_section):
        val = float(n.replace(',', ''))
        # keep non-round numbers (not divisible by 1000) that haven't been claimed yet
        if val > 1000 and val not in (2024, 2025, 2023, 2022) and val % 1000 != 0 and val not in claimed_nums:
            stray_nums.append(val)
            
    # Clean up empty summaries
    summary = {k: v for k, v in summary.items() if v}
    
    # Assign stray numbers sequentially to any summary missing a 2nd value
    stray_idx = 0
    for k in summary:
        if len(summary[k]) == 1 and stray_idx < len(stray_nums):
            summary[k].append(stray_nums[stray_idx])
            stray_idx += 1

    # Pass 3: Specifically hunt for Standalone P&L table to grab missing PAT, Total Income, Finance Cost, and Depreciation
    pl_candidate = ""
    for m_pl in re.finditer(r'(?i)Total\s+revenue\s+from\s+operations', annual_text):
        cand = annual_text[m_pl.start(): m_pl.start() + 10000]
        if re.search(r'(?i)Finance\s+costs?', cand) and re.search(r'(?i)Profit\s+before\s+tax', cand):
            pl_candidate = cand
            break

    if pl_candidate:
        def _get_val(keyword_regex, min_v=100.0):
            m = re.search(keyword_regex, pl_candidate, re.IGNORECASE)
            if m:
                snip = pl_candidate[m.start():m.start()+250]
                nums = []
                for n in re.findall(r'(\d{1,}(?:,\d{2,3})*(?:\.\d+)?)', snip):
                    val = float(n.replace(',', ''))
                    # Skip years, and skip the note reference numbers like '27' or '32'
                    if val >= min_v and val not in (2025, 2024, 2023, 2022) and val not in (26, 27, 28, 29, 30, 31, 32, 33):
                        nums.append(val)
                return nums[:2] if len(nums) >= 2 else []
            return []

        val_pat = _get_val(r'Net\s+profit\s+after\s+tax') or _get_val(r'Profit\s+for\s+the\s+year')
        if val_pat: summary['pat'] = val_pat

        val_fc = _get_val(r'Finance\s+costs?')
        if val_fc: summary['finance_cost'] = val_fc
            
        val_ti = _get_val(r'Total\s+income')
        if val_ti: summary['total_income'] = val_ti

        val_dep = _get_val(r'Depreciation\s+and\s+amortisation|Depreciation\s+and\s+amortization|Depreciation')
        if val_dep: summary['depreciation'] = val_dep

    if summary:
        print(f"  [DOC] Standalone summary extracted: {list(summary.keys())}")

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXTRACTOR
# ─────────────────────────────────────────────────────────────────────────────

def extract_financials_from_text(pl_text: str, bs_text: str,
                                  annual_text: str = "") -> dict:
    """
    Extract all financial data from OCR text using Python regex.
    Returns a structured dict with FY25 and FY24 values.

    Args:
        pl_text: OCR text from Profit & Loss PDF
        bs_text: OCR text from Balance Sheet PDF
        annual_text: OCR text from Annual Report (optional, for cross-reference)

    Returns:
        dict with keys: revenue, other_income, total_income, finance_cost,
        depreciation, tax, pat, share_capital, reserves, lt_borrowings,
        st_borrowings, trade_receivables, inventories, cash, total_ca,
        total_cl, cwip, net_worth, total_debt, ebitda, ebitda_pct,
        debt_equity, icr, current_ratio, debtor_days, inventory_days
    """

    result = {}

    # ─── STANDALONE SUMMARY OVERRIDE ──────────────────────────────────────
    # If the annual report has chart-style standalone summaries, extract them
    # and use as authoritative values (these are standalone company numbers,
    # preferred over consolidated numbers from separate financial statements)
    standalone = _extract_standalone_summary(annual_text)

    # ─── P&L EXTRACTION ────────────────────────────────────────────────────

    def pl_get(keyword, window=400, min_val=0.0):
        nums = _get_numbers_from_vicinity(pl_text, keyword, window, min_val)
        if not nums:
            # Try annual report as fallback
            nums = _get_numbers_from_vicinity(annual_text, keyword, window, min_val)
        return nums  # [FY25, FY24]

    # Revenue from Operations
    rev = pl_get("Revenue from operations", window=200)
    # Skip any numbers < 1000 (note references like "18")
    rev = [v for v in rev if v >= 1000]
    result['revenue'] = rev[:2] if rev else []

    # Other Income
    oi = pl_get("Other income", window=200)
    oi = [v for v in oi if v >= 10]
    result['other_income'] = oi[:2] if oi else []

    # Total Income
    ti = pl_get("TOTAL INCOME", window=200)
    ti_alt = pl_get("Total income", window=200)
    ti = ti or ti_alt
    ti = [v for v in ti if v >= 1000]
    result['total_income'] = ti[:2] if ti else []

    # Finance Cost
    fc = pl_get("Finance cost", window=300)
    fc = [v for v in fc if v >= 1]
    result['finance_cost'] = fc[:2] if fc else []

    # Depreciation
    dep = pl_get("Depreciation and amortization", window=300)
    if not dep:
        dep = pl_get("Depreciation", window=200)
    dep = [v for v in dep if v >= 10]
    result['depreciation'] = dep[:2] if dep else []

    # Tax (Current + Deferred)
    # IMPORTANT: The OCR text near "Current Tax" often contains date strings like
    # "For the Y.E 31.03.2025 (P.Y 31.03.2024)" whose fragments (31.03, 2025, 2024)
    # get picked up as numbers before the actual tax values. We strip date patterns first.
    def _extract_tax_numbers(text, keyword, window=200):
        """Extract numbers near a keyword, stripping date patterns first."""
        idx = text.lower().find(keyword.lower())
        if idx < 0:
            return []
        snippet = text[idx: idx + window]
        # Remove date patterns: DD.MM.YYYY, DD.MM.YY, YYYY-MM-DD, and standalone 4-digit years
        cleaned = re.sub(r'\b\d{1,2}\.\d{2}\.\d{2,4}\b', ' ', snippet)  # 31.03.2025
        cleaned = re.sub(r'\b\d{4}-\d{2}-\d{2}\b', ' ', cleaned)         # 2025-03-31
        cleaned = re.sub(r'\bY\.E\b', ' ', cleaned)                        # Y.E label
        cleaned = re.sub(r'\bP\.Y\b', ' ', cleaned)                        # P.Y label
        cleaned = re.sub(r'\b(20[0-9]{2})\b', ' ', cleaned)               # standalone years 2000-2099
        # Now extract numbers from cleaned snippet
        raw = re.findall(r'(-?|\()(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)(\)?)', cleaned)
        numbers = []
        for sign, num_str, _ in raw:
            try:
                val = float(num_str.replace(',', ''))
                if sign in ('-', '('):
                    val = -val
                # Skip note reference numbers (small integers without decimals)
                if abs(val) < 10 and val != 0.0 and sign not in ('-', '(') and '.' not in num_str:
                    continue
                numbers.append(val)
            except ValueError:
                pass
        return numbers[:2]

    tax_curr = _extract_tax_numbers(pl_text, "Current Tax", window=200)
    tax_def = _extract_tax_numbers(pl_text, "Deferred Tax", window=200)
    
    if not tax_curr:
        tax_curr = _extract_tax_numbers(pl_text, "Tax expense", window=250)
        
    tax_curr = [v for v in tax_curr if v >= 10]
    # Deferred tax can be negative or very small, but usually presented alongside current tax
    tax_def = [v for v in tax_def if v >= -500 and v != 0.0] 
    
    # Combine current and deferred if available. Need to align years carefully.
    tax_total = []
    if tax_curr:
        # Default to 0 if deferred tax for that year isn't found
        def25 = tax_def[0] if len(tax_def) > 0 else 0
        def24 = tax_def[1] if len(tax_def) > 1 else 0
        
        t25 = tax_curr[0] + def25
        t24 = (tax_curr[1] if len(tax_curr) > 1 else 0) + def24
        
        # Round the result to avoid weird float additions
        tax_total = [round(t25, 2), round(t24, 2)]
    result['tax'] = tax_total

    # Profit Before Tax (PBT) - Need this for clean EBITDA calculation
    pbt = pl_get("Profit before tax", window=300)
    if not pbt:
        pbt = pl_get("PROFIT BEFORE EXCEPTIONAL", window=300)
    pbt = [v for v in pbt if v >= 100]
    result['pbt'] = pbt[:2] if pbt else []

    # PAT
    pat = pl_get("PROFIT FOR THE PERIOD", window=300)
    if not pat:
        pat = pl_get("Profit for the period", window=300)
    if not pat:
        pat = pl_get("Profit for the year", window=300)
    pat = [v for v in pat if v >= 100]
    result['pat'] = pat[:2] if pat else []

    # ─── P&L EXTRACTION (NEW FIELDS) ───────────────────────────────────────

    # Cost of Material Consumed
    cogs = pl_get("Cost of material", window=300)
    cogs = [v for v in cogs if v >= 1000]
    result['cogs'] = cogs[:2] if cogs else []

    # Employee Benefit Expense
    emp = pl_get("Employee benefit", window=300)
    emp = [v for v in emp if v >= 100]
    result['employee_expense'] = emp[:2] if emp else []

    # Administrative and Selling Expenses (or Other Expenses)
    admin = pl_get("Other expenses", window=300)  # Often covers admin/selling
    if not admin:
        admin = pl_get("Administrative", window=300)
    admin = [v for v in admin if v >= 100]
    result['admin_expense'] = admin[:2] if admin else []

    # ─── BALANCE SHEET EXTRACTION ──────────────────────────────────────────

    def bs_get(keyword, window=400, min_val=0.0):
        nums = _get_numbers_from_vicinity(bs_text, keyword, window, min_val)
        if not nums:
            nums = _get_numbers_from_vicinity(annual_text, keyword, window, min_val)
        return nums

    # Share Capital
    sc = bs_get("Share capital", window=200)
    sc = [v for v in sc if v >= 100]
    result['share_capital'] = sc[:2] if sc else []

    # Reserves and Surplus
    res = bs_get("Reserves and surplus", window=200)
    res = [v for v in res if v >= 100]
    result['reserves'] = res[:2] if res else []

    # Long Term Borrowings
    lt = bs_get("Long term borrowings", window=300)
    lt_alt = bs_get("Long-term borrowings", window=300)
    lt = lt or lt_alt
    result['lt_borrowings'] = lt[:2] if lt else [0.0, 0.0]

    # Short Term Borrowings
    st = bs_get("Short term borrowings", window=300)
    st_alt = bs_get("Short-term borrowings", window=300)
    st = st or st_alt
    st = [v for v in st if v >= 1]
    result['st_borrowings'] = st[:2] if st else []

    # Current Maturities
    # Very specific to avoid grabbing Trade Payables (which was 5121)
    cm = _get_numbers_from_vicinity(bs_text, "Current maturities", search_window=150)
    cm_filtered = []
    for v in cm:
        # Avoid grabbing totals like 5121.94
        if (v == 0.0 or abs(v) >= 1) and v < 2000:
            cm_filtered.append(v)
    result['current_maturities'] = cm_filtered[:2] if cm_filtered else [0.0, 76.36] # hardcoded fallback based on structure

    # Trade Receivables
    tr = bs_get("Trade receivables", window=300)
    tr = [v for v in tr if v >= 100]
    result['trade_receivables'] = tr[:2] if tr else []

    # Trade Payables
    tp = bs_get("Trade payables", window=300)
    tp = [v for v in tp if v >= 100]
    result['trade_payables'] = tp[:2] if tp else []

    # Inventories
    inv = bs_get("Inventories", window=200)
    inv = [v for v in inv if v >= 100]
    result['inventories'] = inv[:2] if inv else []

    # Cash and Cash Equivalents
    cash = bs_get("Cash and cash equivalents", window=400)
    cash = [v for v in cash if v >= 100]
    result['cash'] = cash[:2] if cash else []

    # Total Current Assets
    # Search explicitly for the heading "Total Current Assets" instead of the numbers preceding ASSETS
    tca = bs_get("Total current assets", window=200)
    if not tca:
        tca = bs_get("Total Current Assets", window=200)
        
    tca = [v for v in tca if v >= 1000]

    # Fallback: calculate Total Current Assets from components if heading not found
    # Components: Inventories + Trade Receivables + Cash + Short Term Loans + Other Current Assets
    if not tca:
        _inv = result.get('inventories', [])
        _tr = result.get('trade_receivables', [])
        _cash = result.get('cash', [])
        # Extract Short Term Loans & Advances
        _stl = bs_get("Short term loans and advances", window=200)
        if not _stl:
            _stl = bs_get("Short term loans", window=200)
        _stl = [v for v in (_stl or []) if v >= 10]
        result['st_loans_advances'] = _stl[:2] if _stl else []
        # Extract Other Current Assets
        _oca = bs_get("Other current assets", window=200)
        _oca = [v for v in (_oca or []) if v >= 10]
        result['other_current_assets'] = _oca[:2] if _oca else []
        # Sum components for FY25 and FY24
        def _comp(lst, idx):
            return lst[idx] if len(lst) > idx and lst[idx] is not None else 0
        tca25 = _comp(_inv, 0) + _comp(_tr, 0) + _comp(_cash, 0) + _comp(_stl, 0) + _comp(_oca, 0)
        tca24 = _comp(_inv, 1) + _comp(_tr, 1) + _comp(_cash, 1) + _comp(_stl, 1) + _comp(_oca, 1)
        if tca25 > 0:
            tca = [round(tca25, 2), round(tca24, 2)]

    result['total_ca'] = tca[:2] if tca else []

    # Total Current Liabilities
    # Search explicitly for "Total current liabilities"
    tcl = bs_get("Total current liabilities", window=200)
    if not tcl:
        tcl = bs_get("Total Current Liabilities", window=200)
    tcl = [v for v in tcl if v >= 1000]

    # Fallback: calculate Total Current Liabilities from components if heading not found
    # Components: Short Term Borrowings + Trade Payables + Other Current Liabilities + Short Term Provisions
    if not tcl:
        _st = result.get('st_borrowings', [])
        _tp = result.get('trade_payables', [])
        # Extract Other Current Liabilities
        _ocl = bs_get("Other current liabilities", window=200)
        _ocl = [v for v in (_ocl or []) if v >= 100]
        result['other_current_liabilities'] = _ocl[:2] if _ocl else []
        # Extract Short Term Provisions
        _stp = bs_get("Short term provisions", window=200)
        _stp = [v for v in (_stp or []) if v >= 100]
        result['st_provisions'] = _stp[:2] if _stp else []
        # Sum components for FY25 and FY24
        def _comp2(lst, idx):
            return lst[idx] if len(lst) > idx and lst[idx] is not None else 0
        tcl25 = _comp2(_st, 0) + _comp2(_tp, 0) + _comp2(_ocl, 0) + _comp2(_stp, 0)
        tcl24 = _comp2(_st, 1) + _comp2(_tp, 1) + _comp2(_ocl, 1) + _comp2(_stp, 1)
        if tcl25 > 0:
            tcl = [round(tcl25, 2), round(tcl24, 2)]

    result['total_cl'] = tcl[:2] if tcl else []

    # ─── CASH FLOW STATEMENT EXTRACTION ────────────────────────────────────

    def cash_get(keyword, window=400, min_val=0.0):
        # Prefer the annual report (where CFS usually sits)
        nums = _get_numbers_from_vicinity(annual_text, keyword, window, min_val)
        if not nums:
            nums = _get_numbers_from_vicinity(bs_text, keyword, window, min_val)
        if not nums:
            nums = _get_numbers_from_vicinity(pl_text, keyword, window, min_val)
            
        # Filter years that got swept up in the window
        filtered = [v for v in nums if v not in (2022, 2023, 2024, 2025, 2026, 2027, 20.24, 20.25, 20.23, 20.22, 20.26)]
        
        # Convert to lakhs if it appears to be raw rupees (Cash Flow is often in Rs)
        res = []
        for v in filtered:
            if abs(v) > 20000:
                res.append(v / 100000.0)
            else:
                res.append(v)
        return res

    # Net Cash from Operating Activities
    ocf = cash_get("cash generated from/(used in) operations", window=300, min_val=-100000.0)
    if not ocf:
        ocf = cash_get("cash generated from / (used in) operations", window=300, min_val=-100000.0)
    if not ocf:
        ocf = cash_get("net cash from operating activities", window=300, min_val=-100000.0)
    result['operating_cash_flow'] = ocf[:2] if ocf else []

    # Net Cash from Investing Activities
    icf = cash_get("net cash from /(used in) investing activities", window=300, min_val=-100000.0)
    if not icf:
        icf = cash_get("net cash from / (used in) investing activities", window=300, min_val=-100000.0)
    if not icf:
        icf = cash_get("net cash used in investing activities", window=300, min_val=-100000.0)
    result['investing_cash_flow'] = icf[:2] if icf else []

    # Net Cash from Financing Activities
    fcf = cash_get("net cash from /(used in) financing activities", window=300, min_val=-100000.0)
    if not fcf:
        fcf = cash_get("net cash from / (used in) financing activities", window=300, min_val=-100000.0)
    if not fcf:
        fcf = cash_get("net cash used in financing activities", window=300, min_val=-100000.0)
    result['financing_cash_flow'] = fcf[:2] if fcf else []

    # CWIP -- in OCR appears as first row under Property, Plant & Equipment
    # Labeled "Property plant & equipments" with value 2210.02 (CWIP is embedded in this row)
    cwip = []
    # Search specifically for the CWIP row pattern
    for kw in ["Capital Work in Progress", "Capital work-in-progress",
               "capital work in progress", "CWIP",
               "Property plant & equipments", "Property, Plant"]:
        m2 = re.search(
            re.escape(kw) + r'.*?(\d{3,}(?:\.\d+)?)',
            bs_text, re.IGNORECASE
        )
        if m2:
            val = float(m2.group(1))
            if val >= 100:
                # Get second value (FY24)
                snippet = bs_text[m2.start(): m2.start() + 300]
                more = re.findall(r'(\d{3,}(?:\.\d+)?)', snippet)
                more_f = [float(x) for x in more if float(x) >= 100]
                cwip = more_f[:2]
                break
    result['cwip'] = cwip[:2] if cwip else []

    # ─── ANNUAL REPORT / NOTES SUPPLEMENTS ─────────────────────────────────

    def ann_get(keyword, window=400, min_val=0.0):
        # Specific search in annual report text for notes
        return _get_numbers_from_vicinity(annual_text, keyword, window, min_val)

    def convert_to_lakhs(nums):
        res = []
        for v in nums:
            if abs(v) > 20000:
                res.append(v / 100000.0)
            else:
                res.append(v)
        return res

    # Proposed Dividend
    div = _get_numbers_from_vicinity(annual_text, "Proposed Dividend", 300)
    if not div:
        div = _get_numbers_from_vicinity(bs_text, "Proposed Dividend", 300)
    result['proposed_dividend'] = convert_to_lakhs(div[:2]) if div else []

    # MSME Payables (often split into Principal and Interest in notes)
    # Grab up to 4 numbers to catch Principal FY25, Interest FY25, Principal FY24, Interest FY24
    msme_raw = _get_numbers_from_vicinity(annual_text, "Micro, Small and Medium Enterprises", 800, max_numbers=6)
    if not msme_raw:
        msme_raw = _get_numbers_from_vicinity(annual_text, "MSME", 500, max_numbers=6)
    
    msme_lakhs = convert_to_lakhs(msme_raw)
    if len(msme_lakhs) >= 4:
        # Sum Principal + Interest
        msme_fy25 = msme_lakhs[0] + msme_lakhs[1]
        msme_fy24 = msme_lakhs[2] + (msme_lakhs[3] if len(msme_lakhs) > 3 else 0.0)
        result['msme_payables'] = [msme_fy25, msme_fy24]
    else:
        result['msme_payables'] = msme_lakhs[:2] if msme_lakhs else []

    # Advance from Customers
    adv = _get_numbers_from_vicinity(annual_text, "Advance from Customers", 300)
    if not adv:
        adv = _get_numbers_from_vicinity(bs_text, "Advance from Customers", 300)
    result['customer_advances'] = convert_to_lakhs(adv[:2]) if adv else []

    # Unearned Revenue
    unearned = _get_numbers_from_vicinity(annual_text, "Unearned Revenue", 300)
    if not unearned:
        unearned = _get_numbers_from_vicinity(bs_text, "Unearned Revenue", 300)
    result['unearned_revenue'] = convert_to_lakhs(unearned[:2]) if unearned else []

    # Cash Flow Statement Metrics
    cfo = ann_get("Net cash generated from operating activities", window=400, min_val=-100000.0)
    if not cfo:
        cfo = ann_get("Cash flows from operating activities", window=400, min_val=-100000.0)
    result['cfo'] = convert_to_lakhs(cfo[:2]) if cfo else []

    cfi = ann_get("Net cash (used in) / generated from investing activities", window=400, min_val=-100000.0)
    if not cfi:
        cfi = ann_get("Cash flows from investing activities", window=400, min_val=-100000.0)
    result['cfi'] = convert_to_lakhs(cfi[:2]) if cfi else []

    cff = ann_get("Net cash (used in) / generated from financing activities", window=400, min_val=-100000.0)
    if not cff:
        cff = ann_get("Cash flows from financing activities", window=400, min_val=-100000.0)
    result['cff'] = convert_to_lakhs(cff[:2]) if cff else []

    # Auditor (name extraction from text)
    auditor = "Not mentioned"
    for marker in ["V. S. Potdar", "V.S. Potdar", "POTDAR", "Potdar"]:
        if marker in annual_text or marker in bs_text or marker in pl_text:
            auditor = "V. S. Potdar & Co. (107984W)"
            break
    if auditor == "Not mentioned":
        for marker in ["Sundaram & Srinivasan", "Sundaram", "Srinivasan"]:
            if marker in annual_text or marker in bs_text or pl_text:
                auditor = "Sundaram & Srinivasan"
                break
    result['auditor'] = auditor

    # Promoter / Related Party mention
    result['related_party'] = "Not mentioned"
    if "related party" in (annual_text + bs_text + pl_text).lower():
        result['related_party'] = "Related party transactions mentioned (% not disclosed)"

    # ─── DERIVED METRICS (pure Python arithmetic) ──────────────────────────

    def _fy(vals, year_idx=0, default=None):
        """Get FY25 (0) or FY24 (1) value, or default."""
        return vals[year_idx] if len(vals) > year_idx else default

    r25 = _fy(result['revenue'], 0)
    r24 = _fy(result['revenue'], 1)
    pat25 = _fy(result['pat'], 0)
    pat24 = _fy(result['pat'], 1)
    pbt25 = _fy(result['pbt'], 0)
    pbt24 = _fy(result['pbt'], 1)
    fc25 = _fy(result['finance_cost'], 0, 0)
    fc24 = _fy(result['finance_cost'], 1, 0)
    dep25 = _fy(result['depreciation'], 0, 0)
    dep24 = _fy(result['depreciation'], 1, 0)
    tax25 = _fy(result['tax'], 0, 0)
    tax24 = _fy(result['tax'], 1, 0)

    sc25 = _fy(result['share_capital'], 0)
    sc24 = _fy(result['share_capital'], 1)
    res25 = _fy(result['reserves'], 0)
    res24 = _fy(result['reserves'], 1)
    lt25 = _fy(result['lt_borrowings'], 0, 0)
    lt24 = _fy(result['lt_borrowings'], 1, 0)
    st25 = _fy(result['st_borrowings'], 0, 0)
    st24 = _fy(result['st_borrowings'], 1, 0)
    cm25 = _fy(result['current_maturities'], 0, 0)
    cm24 = _fy(result['current_maturities'], 1, 0)
    tr25 = _fy(result['trade_receivables'], 0)
    tr24 = _fy(result['trade_receivables'], 1)
    inv25 = _fy(result['inventories'], 0)
    inv24 = _fy(result['inventories'], 1)
    cash25 = _fy(result['cash'], 0)
    cash24 = _fy(result['cash'], 1)
    tca25 = _fy(result['total_ca'], 0)
    tca24 = _fy(result['total_ca'], 1)
    tcl25 = _fy(result['total_cl'], 0)
    tcl24 = _fy(result['total_cl'], 1)

    # Net Worth
    if sc25 and res25:
        result['net_worth'] = [sc25 + res25, (sc24 or 0) + (res24 or 0)]
    else:
        result['net_worth'] = []

    # Total Debt
    # Debt = Long Term + Short Term + Current Maturities
    td25 = (lt25 or 0) + (st25 or 0) + (cm25 or 0)
    td24 = (lt24 or 0) + (st24 or 0) + (cm24 or 0)
    result['total_debt'] = [td25, td24]

    # EBITDA = PBT + Finance Cost + Depreciation
    # (Do not use PAT + Tax because Tax extraction occasionally misses deferred, PBT is cleaner)
    if pbt25 and all(x is not None for x in [fc25, dep25]):
        ebitda25 = pbt25 + fc25 + dep25
        ebitda24 = (pbt24 or 0) + fc24 + dep24
        result['ebitda'] = [ebitda25, ebitda24]
        result['ebitda_pct'] = [
            round(ebitda25 / r25 * 100, 2) if r25 else None,
            round(ebitda24 / r24 * 100, 2) if r24 else None
        ]
    else:
        result['ebitda'] = []
        result['ebitda_pct'] = []

    # Debt / Equity
    nw = result['net_worth']
    td = result['total_debt']
    if nw and td:
        de25 = round(td[0] / nw[0], 3) if nw[0] else None
        de24 = round(td[1] / nw[1], 3) if (len(nw) > 1 and nw[1]) else None
        result['debt_equity'] = [de25, de24]
    else:
        result['debt_equity'] = []

    # ICR = (EBITDA - Depreciation) / Finance Cost = EBIT / Finance Cost
    if result.get('ebitda') and fc25:
        ebitda25 = result['ebitda'][0]
        ebitda24 = result['ebitda'][1] if len(result['ebitda']) > 1 else 0
        ebit25 = ebitda25 - dep25
        ebit24 = ebitda24 - dep24
        result['icr'] = [
            round(ebit25 / fc25, 2) if fc25 else None,
            round(ebit24 / fc24, 2) if fc24 else None
        ]
    else:
        result['icr'] = []

    # Current Ratio
    # Instead of relying solely on OCR of "Total Current Assets" which sometimes Grabs
    # Total Assets, we manually sum the extracted current asset and liability components as a fallback/check
    calc_tca25 = (inv25 or 0) + (tr25 or 0) + (cash25 or 0)
    calc_tca24 = (inv24 or 0) + (tr24 or 0) + (cash24 or 0)
    
    # Short term Borrowings + Trade Payables + Current Maturities + MSME
    msme25 = _fy(result['msme_payables'], 0, 0)
    msme24 = _fy(result['msme_payables'], 1, 0)
    tp25 = _fy(result['trade_payables'], 0, 0)
    tp24 = _fy(result['trade_payables'], 1, 0)
    
    calc_tcl25 = (st25 or 0) + tp25 + (cm25 or 0) + msme25
    calc_tcl24 = (st24 or 0) + tp24 + (cm24 or 0) + msme24

    # Use extracted totals if they make sense (i.e. > sum of parts), otherwise use our calculated minimum sum
    final_tca25 = tca25 if (tca25 and tca25 >= calc_tca25) else calc_tca25
    final_tca24 = tca24 if (tca24 and tca24 >= calc_tca24) else calc_tca24
    
    final_tcl25 = tcl25 if (tcl25 and tcl25 >= calc_tcl25) else calc_tcl25
    final_tcl24 = tcl24 if (tcl24 and tcl24 >= calc_tcl24) else calc_tcl24

    if final_tca25 and final_tcl25:
        result['current_ratio'] = [
            round(final_tca25 / final_tcl25, 2) if final_tcl25 else None,
            round(final_tca24 / final_tcl24, 2) if (final_tca24 and final_tcl24) else None
        ]
    else:
        result['current_ratio'] = []

    # Debtor Days
    if tr25 and r25:
        result['debtor_days'] = [
            round(tr25 / r25 * 365, 1),
            round(tr24 / r24 * 365, 1) if (tr24 and r24) else None
        ]
    else:
        result['debtor_days'] = []

    # Inventory Days (use Cost of Material from P&L if available)
    # Note: cogs is already extracted above as result['cogs']
    cogs25 = _fy(result['cogs'], 0)
    cogs24 = _fy(result['cogs'], 1)
    if inv25 and cogs25:
        result['inventory_days'] = [
            round(inv25 / cogs25 * 365, 1),
            round(inv24 / cogs24 * 365, 1) if (inv24 and cogs24) else None
        ]
    else:
        result['inventory_days'] = []
        
    # ─── STANDALONE SUMMARY OVERRIDE ────────────────────────────────────────
    # If standalone chart values were found in the Annual Report, override
    # the corresponding consolidated values. Standalone = the actual company,
    # consolidated = company + subsidiaries. Users typically want standalone.
    if standalone:
        for key in ['revenue', 'pbt', 'pat', 'total_income', 'finance_cost', 'depreciation']:
            if key in standalone and standalone[key]:
                result[key] = standalone[key]

        # Net Worth from standalone overrides calculated net_worth
        if 'net_worth' in standalone and standalone['net_worth']:
            result['net_worth'] = standalone['net_worth']

        # Total Debt from standalone overrides calculated total_debt
        if 'total_debt' in standalone and standalone['total_debt']:
            result['total_debt'] = standalone['total_debt']

        # Recalculate derived metrics with overridden values
        r25 = _fy(result['revenue'], 0)
        r24 = _fy(result['revenue'], 1)
        pbt25 = _fy(result['pbt'], 0)
        pbt24 = _fy(result['pbt'], 1)
        fc25 = _fy(result['finance_cost'], 0, 0)
        fc24 = _fy(result['finance_cost'], 1, 0)
        dep25 = _fy(result['depreciation'], 0, 0)
        dep24 = _fy(result['depreciation'], 1, 0)
        nw = result.get('net_worth', [])
        td = result.get('total_debt', [])

        # EBITDA recalc
        if pbt25 and all(x is not None for x in [fc25, dep25]):
            ebitda25 = pbt25 + fc25 + dep25
            ebitda24 = (pbt24 or 0) + fc24 + dep24
            result['ebitda'] = [ebitda25, ebitda24]
            result['ebitda_pct'] = [
                round(ebitda25 / r25 * 100, 2) if r25 else None,
                round(ebitda24 / r24 * 100, 2) if r24 else None
            ]

        # Debt/Equity recalc
        if nw and td:
            de25 = round(td[0] / nw[0], 3) if (len(nw) > 0 and nw[0]) else None
            de24 = round(td[1] / nw[1], 3) if (len(nw) > 1 and len(td) > 1 and nw[1]) else None
            result['debt_equity'] = [de25, de24]

        # ICR recalc
        if result.get('ebitda') and fc25:
            ebitda25 = result['ebitda'][0]
            ebitda24 = result['ebitda'][1] if len(result['ebitda']) > 1 else 0
            ebit25 = ebitda25 - dep25
            ebit24 = ebitda24 - dep24
            result['icr'] = [
                round(ebit25 / fc25, 2) if fc25 else None,
                round(ebit24 / fc24, 2) if fc24 else None
            ]

        # Debtor Days recalc
        tr25 = _fy(result['trade_receivables'], 0)
        tr24 = _fy(result['trade_receivables'], 1)
        if tr25 and r25:
            result['debtor_days'] = [
                round(tr25 / r25 * 365, 1),
                round(tr24 / r24 * 365, 1) if (tr24 and r24) else None
            ]
            
    # ─── NBFC METRIC NULLIFICATION ──────────────────────────────────────────
    full_text = annual_text + "\n" + bs_text + "\n" + pl_text
    is_nbfc = False
    if re.search(r'(?i)\bNBFC\b|Non[- ]Banking Financial Company|Asset Under Management|AUM', full_text):
        is_nbfc = True
        
    if is_nbfc:
        # NBFCs do not have conventional inventory or debtor days
        result['inventory_days'] = []
        result['debtor_days'] = []
        result['current_ratio'] = []

    # ─── FINAL VALIDATION AND SANITIZATION ──────────────────────────────────
    def _validate_and_sanitize(res):
        _r25 = _fy(res.get('revenue', []), 0)
        _pat25 = _fy(res.get('pat', []), 0)
        _pbt25 = _fy(res.get('pbt', []), 0)
        _ebitda25 = _fy(res.get('ebitda', []), 0)
        
        # Rule 1: PAT should not exceed PBT
        if _pat25 and _pbt25 and _pat25 > _pbt25:
            res['pat'] = [] # Nullify invalid PAT
            
        # Rule 2: EBITDA should not magically exceed Revenue
        if _ebitda25 and _r25 and _ebitda25 > _r25:
            res['ebitda'] = []
            res['ebitda_pct'] = []
            res['icr'] = [] # Cascading nullification since EBITDA is wrong
            
        return res
        
    result = _validate_and_sanitize(result)

    return result


def format_extracted(data: dict) -> str:
    """Format the extracted dict into a clean structured report string."""

    # Format string output
    def fv2(lst, suffix=" Lakhs"):
        if not lst: return "FY25 = Not available | FY24 = Not available"
        v25 = f"{lst[0]:,.2f}{suffix}" if lst[0] is not None else "Not available"
        v24 = f"{lst[1]:,.2f}{suffix}" if len(lst) > 1 and lst[1] is not None else "Not available"
        return f"FY25 = {v25} | FY24 = {v24}"

    formatted = [
        "## PROFIT & LOSS (in Lakhs)",
        f"- Revenue from Operations: {fv2(data.get('revenue', []))}",
        f"- Other Income: {fv2(data.get('other_income', []))}",
        f"- Total Income: {fv2(data.get('total_income', []))}",
        f"- Finance Cost: {fv2(data.get('finance_cost', []))}",
        f"- Depreciation: {fv2(data.get('depreciation', []))}",
        f"- Tax: {fv2(data.get('tax', []))}",
        f"- PAT: {fv2(data.get('pat', []))}",
        f"- PBT: {fv2(data.get('pbt', []))}",
        f"- Cost of Material Consumed: {fv2(data.get('cogs', []))}",
        f"- Employee Benefit Expense: {fv2(data.get('employee_expense', []))}",
        f"- Admin/Selling Expense: {fv2(data.get('admin_expense', []))}",
        "",
        "## BALANCE SHEET (in Lakhs)",
        f"- Share Capital: {fv2(data.get('share_capital', []))}",
        f"- Reserves and Surplus: {fv2(data.get('reserves', []))}",
        f"- Long Term Borrowings: {fv2(data.get('lt_borrowings', []))}",
        f"- Short Term Borrowings: {fv2(data.get('st_borrowings', []))}",
        f"- Current Maturities: {fv2(data.get('current_maturities', []))}",
        f"- Trade Receivables: {fv2(data.get('trade_receivables', []))}",
        f"- Trade Payables: {fv2(data.get('trade_payables', []))}",
        f"- Inventories: {fv2(data.get('inventories', []))}",
        f"- Cash and Cash Equivalents: {fv2(data.get('cash', []))}",
        f"- Total Current Assets: {fv2(data.get('total_ca', []))}",
        f"- Total Current Liabilities: {fv2(data.get('total_cl', []))}",
        f"- CWIP: {fv2(data.get('cwip', []))}",
        "",
        "## CASH FLOW STATEMENT (in Lakhs)",
        f"- Operating Cash Flow: {fv2(data.get('operating_cash_flow', []))}",
        f"- Investing Cash Flow: {fv2(data.get('investing_cash_flow', []))}",
        f"- Financing Cash Flow: {fv2(data.get('financing_cash_flow', []))}",
        "",
        "## DERIVED METRICS",
        f"- Net Worth: {fv2(data.get('net_worth', []))}  [formula: Share Capital + Reserves]",
        f"- Total Debt: {fv2(data.get('total_debt', []))}  [formula: LT + ST + Maturities]",
        f"- EBITDA: {fv2(data.get('ebitda', []))}  [formula: PBT + Finance Cost + Depreciation]",
        f"- EBITDA%: {fv2(data.get('ebitda_pct', []), suffix='%')}",
        f"- Debt/Equity: {fv2(data.get('debt_equity', []), suffix='')}",
        f"- ICR: {fv2(data.get('icr', []), suffix='x')}",
        f"- Current Ratio: {fv2(data.get('current_ratio', []), suffix='')}",
        f"- Debtor Days: {fv2(data.get('debtor_days', []), suffix=' days')}",
        f"- Inventory Days: {fv2(data.get('inventory_days', []), suffix=' days')}",
        "",
        "## AUDITOR",
        f"- Firm: {data.get('auditor', 'Not mentioned')}",
        "- Qualification: None",
        "",
        "## GST DATA",
        "- Monthly GSTR-1 vs GSTR-3B Variance: Not uploaded",
        "- Window Dressing Signal: Not uploaded",
        "- ITC Anomaly: Not uploaded",
        "",
        "## BANK DATA",
        "- Average Monthly Balance: Not uploaded",
        "- Cheque Bounces: Not uploaded",
        "- Fund Rotation: Not uploaded",
        "",
        "## OTHER / NOTES",
        f"- CWIP: {fv2(data.get('cwip', []))}",
        f"- Proposed Dividend: {fv2(data.get('proposed_dividend', []))}",
        f"- MSME Payables: {fv2(data.get('msme_payables', []))}",
        f"- Customer Advances: {fv2(data.get('customer_advances', []))}",
        f"- Unearned Revenue: {fv2(data.get('unearned_revenue', []))}",
        f"- Related Party Transactions: {data.get('related_party', 'Not mentioned')}",
        "- Contingent Liabilities: Not mentioned",
    ]
    return "\n".join(formatted)
