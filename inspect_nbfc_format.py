import os
from utils.pdf_extractor import extract_text_from_pdf

def main():
    pdf_file = r"c:\Users\Vedant\OneDrive\Desktop\multi-3\VCL Consolidated Financial Statements - FY 24-25.pdf"
    
    # Extract text from the consolidated financial statements
    text = extract_text_from_pdf(pdf_file)
    
    # We want to find the balance sheet and P&L. 
    # Usually they follow "ASSETS", "EQUITY AND LIABILITIES", "INCOME", "EXPENSES"
    
    idx_bs = text.find("ASSETS")
    if idx_bs == -1:
        idx_bs = text.find("Assets")
        
    idx_pl = text.find("INCOME")
    if idx_pl == -1:
        idx_pl = text.find("Income")
        
    print("="*40)
    print("BALANCE SHEET SNIPPET:")
    print("="*40)
    if idx_bs != -1:
        print(text[idx_bs:idx_bs+2000])
    else:
        print("ASSETS not found.")
        
    print("\n" + "="*40)
    print("PROFIT & LOSS SNIPPET:")
    print("="*40)
    if idx_pl != -1:
        print(text[idx_pl:idx_pl+2000])
    else:
        print("INCOME not found.")

if __name__ == "__main__":
    main()
