# utils/pdf_extractor.py
# Extracts text from uploaded PDFs for feeding into agents
# ENHANCED: Hybrid detection (text vs scanned), OCR fallback,
#           structured table→DataFrame conversion, efficient page-level extraction

import pdfplumber
import pandas as pd
import os
import re

# ── OCR Support (graceful fallback if not installed) ──────────
try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# STEP 1: PDF TYPE DETECTION
# ═══════════════════════════════════════════════════════════════

def detect_pdf_type(file_path: str) -> str:
    """
    Detect if PDF is text-based or scanned (image-based).
    Samples first 3 pages — if cumulative text < 50 chars, it's a scan.
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            sample_text = ""
            for page in pdf.pages[:3]:
                text = page.extract_text() or ""
                sample_text += text
            if len(sample_text.strip()) < 50:
                return "SCANNED"
            return "TEXT"
    except Exception:
        return "UNKNOWN"


# ═══════════════════════════════════════════════════════════════
# STEP 2: TABLE → STRUCTURED TEXT (DataFrame conversion)
# ═══════════════════════════════════════════════════════════════

def _table_to_structured_text(table: list, page_num: int, table_idx: int) -> str:
    """
    Convert a raw pdfplumber table into clean structured text.
    Uses pandas DataFrame for alignment and deduplication.
    """
    if not table or len(table) < 2:
        return ""

    # Clean None values and filter empty rows
    clean_rows = []
    for row in table:
        if row:
            clean_row = [str(cell).strip() if cell else "" for cell in row]
            if any(c for c in clean_row):
                clean_rows.append(clean_row)

    if len(clean_rows) < 2:
        return ""

    try:
        # Normalize column count (pad short rows)
        max_cols = max(len(r) for r in clean_rows)
        padded = [r + [""] * (max_cols - len(r)) for r in clean_rows]

        # First row as header, rest as data
        header = padded[0]
        data = padded[1:]

        # Deduplicate empty headers
        seen = {}
        for i, h in enumerate(header):
            if not h:
                header[i] = f"col_{i}"
            elif h in seen:
                header[i] = f"{h}_{seen[h]}"
                seen[h] += 1
            else:
                seen[h] = 1

        df = pd.DataFrame(data, columns=header)

        # Drop columns that are entirely empty
        df = df.loc[:, (df != '').any()]

        if df.empty:
            return ""

        result = f"\n--- TABLE {table_idx} ON PAGE {page_num} ---\n"
        result += df.to_string(index=False) + "\n"
        return result

    except Exception:
        # Fallback to pipe-separated format
        result = f"\n--- TABLE {table_idx} ON PAGE {page_num} ---\n"
        for row in clean_rows:
            result += " | ".join(row) + "\n"
        return result


# ═══════════════════════════════════════════════════════════════
# STEP 3: TEXT-BASED PDF EXTRACTION (pdfplumber — primary path)
# ═══════════════════════════════════════════════════════════════

def _extract_text_pdfplumber(file_path: str) -> str:
    """
    High-quality text extraction from digital PDFs.
    Extracts: text blocks + layout text + tables as DataFrames.
    """
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"    📄 {os.path.basename(file_path)}: {total_pages} pages (text-based)")

            for i, page in enumerate(pdf.pages):
                page_content = ""

                # ── Primary text extraction ──
                page_text = page.extract_text()
                if page_text:
                    page_content += page_text + "\n"

                # ── Layout extraction (catches misaligned text) ──
                try:
                    page_text_layout = page.extract_text(layout=True)
                    if page_text_layout and page_text_layout != page_text:
                        # Only add if substantially more content
                        if len(page_text_layout) > len(page_text or "") * 1.2:
                            page_content += "\n--- LAYOUT EXTRACTION ---\n"
                            page_content += page_text_layout + "\n"
                except Exception:
                    pass

                # ── Table extraction → DataFrame conversion ──
                tables = page.extract_tables()
                for t_idx, table in enumerate(tables):
                    structured = _table_to_structured_text(table, i + 1, t_idx + 1)
                    if structured:
                        page_content += structured

                # Only add page if there's content
                if page_content.strip():
                    page_header = f"\n{'='*40}\n--- PAGE {i+1} of {total_pages} ---\n{'='*40}\n"
                    text += page_header + page_content

    except Exception as e:
        text = f"[PDF EXTRACTION ERROR for {os.path.basename(file_path)}]: {str(e)}"

    return text


# ═══════════════════════════════════════════════════════════════
# STEP 4: OCR EXTRACTION (for scanned PDFs)
# ═══════════════════════════════════════════════════════════════

def _extract_text_ocr(file_path: str) -> str:
    """
    Extract text from scanned/image-based PDFs using OCR.
    Requires: pip install pdf2image pytesseract
    System deps: brew install tesseract poppler (macOS)
    """
    if not OCR_AVAILABLE:
        return (
            f"[OCR NOT AVAILABLE for {os.path.basename(file_path)}]: "
            "This appears to be a scanned PDF but OCR libraries are not installed. "
            "Install: pip install pdf2image pytesseract && brew install tesseract poppler"
        )

    text = ""
    try:
        images = convert_from_path(file_path, dpi=300)
        total_pages = len(images)
        print(f"    🔍 OCR: {os.path.basename(file_path)}: {total_pages} pages at 300 DPI")

        for i, img in enumerate(images):
            page_text = pytesseract.image_to_string(img, lang='eng')
            if page_text.strip():
                page_header = f"\n{'='*40}\n--- PAGE {i+1} of {total_pages} (OCR) ---\n{'='*40}\n"
                text += page_header + page_text + "\n"

    except Exception as e:
        text = f"[OCR ERROR for {os.path.basename(file_path)}]: {str(e)}"

    return text


# ═══════════════════════════════════════════════════════════════
# STEP 5: MAIN ENTRY POINT — Hybrid extraction
# ═══════════════════════════════════════════════════════════════

def extract_text_from_pdf(file_path: str) -> str:
    """
    HYBRID extraction pipeline:
    1. Detect if PDF is text-based or scanned
    2. Use pdfplumber for text PDFs (fast, accurate)
    3. Fall back to OCR for scanned PDFs
    4. Tables are converted to DataFrames for clean structure
    """
    pdf_type = detect_pdf_type(file_path)
    print(f"    📋 {os.path.basename(file_path)} → Detected type: {pdf_type}")

    if pdf_type == "SCANNED":
        text = _extract_text_ocr(file_path)
    else:
        text = _extract_text_pdfplumber(file_path)

    print(f"    📊 Extracted {len(text):,} characters from {os.path.basename(file_path)}")
    return text


def extract_text_from_multiple_pdfs(file_paths: list) -> dict:
    """
    Process multiple uploaded files.
    Returns dict: {filename: extracted_text}
    """
    results = {}
    total_chars = 0
    for path in file_paths:
        filename = os.path.basename(path)
        print(f"  📥 Extracting: {filename}")
        extracted = extract_text_from_pdf(path)
        results[filename] = extracted
        total_chars += len(extracted)

    print(f"  📊 Total extraction: {total_chars:,} characters from {len(file_paths)} file(s)")
    return results


def combine_all_documents(extracted_docs: dict) -> str:
    """
    Combines all extracted documents into one string for the parser agent.
    No truncation — sends the full document content.
    """
    combined = ""
    for filename, text in extracted_docs.items():
        combined += f"\n\n{'='*60}\n"
        combined += f"DOCUMENT: {filename}\n"
        combined += f"{'='*60}\n"
        combined += text

    print(f"  📊 Combined document text: {len(combined):,} characters")
    return combined