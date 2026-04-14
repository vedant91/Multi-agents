import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from agents.bull_bear_agents import run_bull_agent

parser_output = "Company shows strong revenue growth of 30% from FY24 to FY25."
fraud_output = "No fraud detected."
research_output = "Company is a market leader in automated parking systems."
loan_details = {
    'company_name': 'WOHR Parking',
    'loan_amount': 1000000000.0,
    'loan_purpose': 'Working Capital',
    'sector': 'Manufacturing'
}

print("Running Bull Agent...")
result = run_bull_agent(parser_output, fraud_output, research_output, loan_details)
print("\n=== BULL AGENT OUTPUT ===")
print(result)
