import os
from utils.pdf_extractor import extract_text_from_pdf

def main():
    pdf_file = r"c:\Users\Vedant\OneDrive\Desktop\multi-3\VCL Consolidated Financial Statements - FY 24-25.pdf"
    
    print(f"Extracting text from {pdf_file}...")
    text = extract_text_from_pdf(pdf_file)
    
    output_file = "vcl_raw.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(text)
        
    print(f"Text saved to {output_file}")
    
    # Try to find the start of the Balance sheet and P&L
    idx_bs = text.find("ASSETS")
    if idx_bs == -1:
        idx_bs = text.find("Assets")
        
    idx_pl = text.find("INCOME")
    if idx_pl == -1:
        idx_pl = text.find("Income")
        
    print("\n" + "="*40)
    print("BALANCE SHEET SNIPPET:")
    print("="*40)
    if idx_bs != -1:
        print(text[idx_bs:idx_bs+1500])
    else:
        print("ASSETS not found.")

if __name__ == "__main__":
    main()
