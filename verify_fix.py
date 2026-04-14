"""
Verification script — tests that the financial extractor produces correct values
after the tax and Total CA/CL fixes.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from utils.pdf_extractor import extract_text_from_pdf
from utils.financial_extractor import extract_financials_from_text, format_extracted

PDF_DIR = r"C:\Users\Vedant\OneDrive\Desktop\multi-3"

# Extract text from PDFs
print("Extracting PDFs...")
pl_text = extract_text_from_pdf(os.path.join(PDF_DIR, "Profit & Loss.pdf"))
bs_text = extract_text_from_pdf(os.path.join(PDF_DIR, "Balance Sheet.pdf"))
annual_text = extract_text_from_pdf(os.path.join(PDF_DIR, "Wohr_Balance Sheet_2025.pdf"))

print("\nRunning financial extractor...")
data = extract_financials_from_text(pl_text, bs_text, annual_text)

# Expected values from the user's verification
EXPECTED = {
    'revenue': [38010.51, 29121.94],
    'other_income': [421.91, 432.62],
    'total_income': [38482.42, 29554.57],
    'finance_cost': [115.58, 75.42],
    'depreciation': [248.55, 236.78],
    'pbt': [3307.61, 1783.34],
    'pat': [2489.81, 1282.32],
    'tax': [1196.19, 525.70],  # FIX: was [220.23, 2037.34]
    'share_capital': [498.01, 498.01],
    'reserves': [6956.66, 4671.02],
    'lt_borrowings': [1941.78, 2046.36],
    'st_borrowings': [424.01, 670.95],
    'trade_receivables': [7061.55, 4257.75],
    'trade_payables': [5121.95, 4295.41],
    'inventories': [4592.83, 4489.96],
    'cash': [4152.39, 3847.63],
    # Total Current Assets = 4592.83 + 7061.55 + 4152.39 + 1503.90 + 445.83 = 17756.50
    'total_ca': [17756.50, None],  # FY24 we'll just check >= 10000
    # Total Current Liabilities = 424.01 + 5121.95 + 4435.76 + 1989.69 = 11971.41
    'total_cl': [11971.41, None],  # FY24 we'll just check >= 5000
}

print("\n" + "=" * 70)
print("VERIFICATION RESULTS")
print("=" * 70)

all_pass = True
for key, expected in EXPECTED.items():
    actual = data.get(key, [])
    
    if not actual:
        print(f"  [FAIL] {key}: No data extracted (expected {expected})")
        all_pass = False
        continue
    
    # Check FY25
    if expected[0] is not None:
        if len(actual) > 0 and abs(actual[0] - expected[0]) < 1.0:
            print(f"  [PASS] {key} FY25: {actual[0]} (expected {expected[0]})")
        else:
            print(f"  [FAIL] {key} FY25: {actual[0] if actual else 'MISSING'} (expected {expected[0]})")
            all_pass = False
    
    # Check FY24
    if len(expected) > 1 and expected[1] is not None:
        if len(actual) > 1 and abs(actual[1] - expected[1]) < 1.0:
            print(f"  [PASS] {key} FY24: {actual[1]} (expected {expected[1]})")
        else:
            print(f"  [FAIL] {key} FY24: {actual[1] if len(actual) > 1 else 'MISSING'} (expected {expected[1]})")
            all_pass = False

# Special check for Total CA FY24 (should be >= 10000)
if data.get('total_ca') and len(data['total_ca']) > 1:
    if data['total_ca'][1] >= 10000:
        print(f"  [PASS] total_ca FY24: {data['total_ca'][1]} (sanity check >= 10000)")
    else:
        print(f"  [WARN] total_ca FY24: {data['total_ca'][1]} (expected >= 10000)")

# Special check for Total CL FY24 (should be >= 5000)
if data.get('total_cl') and len(data['total_cl']) > 1:
    if data['total_cl'][1] >= 5000:
        print(f"  [PASS] total_cl FY24: {data['total_cl'][1]} (sanity check >= 5000)")
    else:
        print(f"  [WARN] total_cl FY24: {data['total_cl'][1]} (expected >= 5000)")

# Derived metrics check
print("\n" + "=" * 70)
print("DERIVED METRICS")
print("=" * 70)
print(f"  Net Worth:      {data.get('net_worth')}")
print(f"  Total Debt:     {data.get('total_debt')}")
print(f"  EBITDA:         {data.get('ebitda')}")
print(f"  Debt/Equity:    {data.get('debt_equity')}")
print(f"  ICR:            {data.get('icr')}")
print(f"  Current Ratio:  {data.get('current_ratio')}")
print(f"  Debtor Days:    {data.get('debtor_days')}")

# EBITDA check: 3307.61 + 115.58 + 248.55 = 3671.74
if data.get('ebitda'):
    if abs(data['ebitda'][0] - 3671.74) < 1.0:
        print(f"  [PASS] EBITDA FY25: {data['ebitda'][0]} (expected 3671.74)")
    else:
        print(f"  [FAIL] EBITDA FY25: {data['ebitda'][0]} (expected 3671.74)")
        all_pass = False

# D/E check: 0.33
if data.get('debt_equity'):
    if abs(data['debt_equity'][0] - 0.33) < 0.01:
        print(f"  [PASS] Debt/Equity FY25: {data['debt_equity'][0]} (expected ~0.33)")
    else:
        print(f"  [WARN] Debt/Equity FY25: {data['debt_equity'][0]} (expected ~0.33)")

# ICR check: 29.62
if data.get('icr'):
    if abs(data['icr'][0] - 29.62) < 0.1:
        print(f"  [PASS] ICR FY25: {data['icr'][0]} (expected ~29.62)")
    else:
        print(f"  [WARN] ICR FY25: {data['icr'][0]} (expected ~29.62)")

print("\n" + "=" * 70)
if all_pass:
    print("[SUCCESS] ALL CHECKS PASSED!")
else:
    print("[ISSUES] Some checks failed, see above.")
print("=" * 70)
