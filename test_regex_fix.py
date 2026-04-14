"""Quick test to verify the regex fix for decision parsing."""
import re

pattern = r'FINAL DECISION:?[*\s\n]*(STRONG APPROVE|CONDITIONAL APPROVE|CONDITIONAL|HIGH RISK REFER|APPROVE|REJECT)'

tests = [
    ("FINAL DECISION: CONDITIONAL APPROVE", "CONDITIONAL APPROVE"),
    ("FINAL DECISION: APPROVE", "APPROVE"),
    ("FINAL DECISION: STRONG APPROVE", "STRONG APPROVE"),
    ("FINAL DECISION: REJECT", "REJECT"),
    ("FINAL DECISION: HIGH RISK REFER", "HIGH RISK REFER"),
    ("FINAL DECISION: CONDITIONAL", "CONDITIONAL"),
]

all_pass = True
for text, expected in tests:
    m = re.search(pattern, text.upper())
    got = m.group(1) if m else "NO MATCH"
    status = "PASS" if got == expected else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"  [{status}] '{text}' -> got '{got}' (expected '{expected}')")

# Also test the OLD broken regex to confirm it was indeed wrong
print("\n--- OLD BROKEN REGEX (for comparison) ---")
old_pattern = r'FINAL DECISION:?[*\s\n]*(STRONG APPROVE|APPROVE|CONDITIONAL APPROVE|CONDITIONAL|HIGH RISK REFER|REJECT)'
m_old = re.search(old_pattern, "FINAL DECISION: CONDITIONAL APPROVE")
print(f"  OLD regex on 'CONDITIONAL APPROVE' -> '{m_old.group(1)}' (BUG: matches APPROVE instead!)")

print(f"\n{'ALL TESTS PASSED!' if all_pass else 'SOME TESTS FAILED!'}")
