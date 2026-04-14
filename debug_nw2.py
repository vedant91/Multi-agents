import re
from utils.pdf_extractor import extract_text_from_pdf
from utils.financial_extractor import _extract_standalone_summary

text = extract_text_from_pdf(r'c:\Users\Vedant\OneDrive\Desktop\multi-3\Annual Report FY 2024-25.pdf')

for m in re.finditer(r'(?i)standalone\s+metrics', text):
    candidate = text[m.start():m.start()+5000]
    if 'Revenue' not in candidate:
        continue

    # 1. Gather all non-axis numbers in the whole candidate
    all_nums = []
    for n in re.findall(r'(\d{1,3}(?:,\d{2,3})*(?:\.\d+)?)', candidate):
        val = float(n.replace(',', ''))
        if val > 1000 and val not in (2024, 2025, 2023, 2022) and val % 10000 != 0:
            all_nums.append(val)
    print("All non-axis numbers:", all_nums)
    break
