import os
import pickle
from utils.pdf_extractor import extract_text_from_multiple_pdfs, combine_all_documents
from agents.document_parser import run_document_parser

def main():
    pdf_files = [
        r"c:\Users\Vedant\OneDrive\Desktop\multi-3\Annual Report FY 2024-25.pdf",
        r"c:\Users\Vedant\OneDrive\Desktop\multi-3\VCL Consolidated Financial Statements - FY 24-25.pdf"
    ]
    cache_file = "vcl_text_cache.pkl"
    
    if os.path.exists(cache_file):
        print("Loading text from cache...")
        with open(cache_file, "rb") as f:
            extracted_docs = pickle.load(f)
    else:
        print("Extracting text from PDFs...")
        extracted_docs = extract_text_from_multiple_pdfs(pdf_files)
        with open(cache_file, "wb") as f:
            pickle.dump(extracted_docs, f)
            
    # Save the VCL specific text to a readable file
    vcl_text = extracted_docs["VCL Consolidated Financial Statements - FY 24-25.pdf"]
    with open("vcl_raw_text.txt", "w", encoding="utf-8") as f:
        f.write(vcl_text)
        
    print("VCL text saved to vcl_raw_text.txt")
    print("Done")

if __name__ == "__main__":
    main()
