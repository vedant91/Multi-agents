# utils/pdf_extractor.py
# Extracts text from uploaded PDFs for feeding into agents

import pdfplumber
import os


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts all text from a PDF file.
    Works on both digital PDFs and scanned ones (via pdfplumber).
    Returns plain text string.
    """
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- PAGE {i+1} ---\n"
                    text += page_text

            # Also extract tables (financial statements have lots of tables)
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for table in tables:
                    text += f"\n--- TABLE ON PAGE {i+1} ---\n"
                    for row in table:
                        if row:
                            # Clean None values
                            clean_row = [str(cell) if cell else "" for cell in row]
                            text += " | ".join(clean_row) + "\n"

    except Exception as e:
        text = f"[PDF EXTRACTION ERROR]: {str(e)}"

    return text


def extract_text_from_multiple_pdfs(file_paths: list) -> dict:
    """
    Process multiple uploaded files.
    Returns dict: {filename: extracted_text}
    """
    results = {}
    for path in file_paths:
        filename = os.path.basename(path)
        print(f"Extracting: {filename}")
        results[filename] = extract_text_from_pdf(path)
    return results


def combine_all_documents(extracted_docs: dict) -> str:
    """
    Combines all extracted documents into one string for the parser agent.
    """
    combined = ""
    for filename, text in extracted_docs.items():
        combined += f"\n\n{'='*60}\n"
        combined += f"DOCUMENT: {filename}\n"
        combined += f"{'='*60}\n"
        combined += text
    return combined