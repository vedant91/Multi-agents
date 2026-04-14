import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.pdf_extractor import extract_text_from_multiple_pdfs, combine_all_documents
from agents.document_parser import run_document_parser

def main():
    pdf_files = [
        r"c:\Users\Vedant\OneDrive\Desktop\multi-3\Annual Report FY 2024-25.pdf",
        r"c:\Users\Vedant\OneDrive\Desktop\multi-3\VCL Consolidated Financial Statements - FY 24-25.pdf"
    ]
    
    # 1. Extract text
    print("Extracting text from PDFs...")
    extracted_docs = extract_text_from_multiple_pdfs(pdf_files)
    combined_text = combine_all_documents(extracted_docs)
    
    # 2. Parse text
    print("\nRunning document parser...")
    parsed_report = run_document_parser(combined_text, extracted_docs)
    
    # 3. Print report
    print("\n" + "="*80)
    print("FINAL EXTRACTED REPORT:")
    print("="*80)
    print(parsed_report)
    print("="*80)

if __name__ == "__main__":
    main()
