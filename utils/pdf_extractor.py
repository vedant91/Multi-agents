# utils/pdf_extractor.py
# Extracts text from uploaded PDFs for feeding into agents.
#
# ENHANCED for large (200-page) Indian financial documents:
#   • PyMuPDF (fitz) as primary extractor  — fast, accurate, handles complex layouts
#   • pdfplumber as secondary extractor    — structured table extraction
#   • Per-page scan detection              — only OCR pages that lack embedded text
#   • Batch page processing (20 pages)     — memory-efficient for large files
#   • Improved OCR config for Indian text  — Hindi + English Tesseract language pack
#   • Structured table → DataFrame         — pdfplumber table extraction preserved

import os
import re
import pandas as pd

# ── PyMuPDF (primary extractor) ───────────────────────────────
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# ── pdfplumber (secondary / table extractor) ──────────────────
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# ── OCR Support (graceful fallback if not installed) ──────────
try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Number of pages processed per memory batch for large PDFs
PAGE_BATCH_SIZE = 20

# Minimum embedded-text chars on a page before we consider it "text-based"
MIN_PAGE_TEXT_CHARS = 30

# OCR settings for Indian financial documents
OCR_DPI = 300               # Resolution for OCR rendering (300 DPI = good quality)
POINTS_PER_INCH = 72        # PDF internal unit (1 pt = 1/72 inch)
TESSERACT_LANGUAGES = "eng+hin"  # English + Hindi/Devanagari for Indian documents


# ═══════════════════════════════════════════════════════════════
# STEP 1: TABLE → STRUCTURED TEXT (DataFrame conversion)
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
        max_cols = max(len(r) for r in clean_rows)
        padded = [r + [""] * (max_cols - len(r)) for r in clean_rows]

        header = padded[0]
        data = padded[1:]

        seen: dict[str, int] = {}
        for i, h in enumerate(header):
            if not h:
                header[i] = f"col_{i}"
            elif h in seen:
                header[i] = f"{h}_{seen[h]}"
                seen[h] += 1
            else:
                seen[h] = 1

        df = pd.DataFrame(data, columns=header)
        df = df.loc[:, (df != '').any()]

        if df.empty:
            return ""

        result = f"\n--- TABLE {table_idx} ON PAGE {page_num} ---\n"
        result += df.to_string(index=False) + "\n"
        return result

    except Exception:
        result = f"\n--- TABLE {table_idx} ON PAGE {page_num} ---\n"
        for row in clean_rows:
            result += " | ".join(row) + "\n"
        return result


# ═══════════════════════════════════════════════════════════════
# STEP 2: PyMuPDF EXTRACTION (primary path — fast, accurate)
# ═══════════════════════════════════════════════════════════════

def _extract_page_pymupdf(page) -> str:
    """Extract text from a single PyMuPDF page using layout-preserving mode."""
    # "blocks" mode keeps reading order and preserves table-like column alignment
    try:
        text = page.get_text("text")
        if not text:
            text = ""
    except Exception:
        text = ""
    return text


def _extract_text_pymupdf(file_path: str) -> str:
    """
    Primary extraction path using PyMuPDF (fitz).

    Advantages over pdfplumber for large Indian financial PDFs:
      - 5-10× faster on large files
      - Better Unicode / Devanagari glyph handling
      - More reliable column layout reconstruction
      - Per-page OCR decision (only scanned pages get OCR)
      - Batch processing avoids loading all pages into RAM at once
    """
    text = ""
    try:
        doc = fitz.open(file_path)
        total_pages = len(doc)
        print(f"    📄 {os.path.basename(file_path)}: {total_pages} pages (PyMuPDF)")

        for batch_start in range(0, total_pages, PAGE_BATCH_SIZE):
            batch_end = min(batch_start + PAGE_BATCH_SIZE, total_pages)

            for page_num in range(batch_start, batch_end):
                page = doc[page_num]
                page_text = _extract_page_pymupdf(page)

                # Per-page scan detection: if embedded text is too short → OCR
                if len(page_text.strip()) < MIN_PAGE_TEXT_CHARS:
                    page_text = _ocr_single_page_pymupdf(page, page_num + 1, file_path)

                if page_text.strip():
                    page_header = (
                        f"\n{'='*40}\n"
                        f"--- PAGE {page_num + 1} of {total_pages} ---\n"
                        f"{'='*40}\n"
                    )
                    text += page_header + page_text + "\n"

        doc.close()

    except Exception as e:
        text = f"[PDF EXTRACTION ERROR for {os.path.basename(file_path)}]: {str(e)}"

    return text


def _ocr_single_page_pymupdf(page, page_num: int, file_path: str) -> str:
    """
    OCR a single scanned page rendered via PyMuPDF (no external poppler needed).
    Falls back to pytesseract-only message if OCR libs unavailable.
    """
    if not OCR_AVAILABLE:
        return (
            f"[PAGE {page_num} — SCANNED, OCR NOT AVAILABLE]: "
            "Install: pip install pdf2image pytesseract && "
            "apt-get install tesseract-ocr tesseract-ocr-hin"
        )

    try:
        # Render at OCR_DPI via PyMuPDF (avoids poppler dependency)
        mat = fitz.Matrix(OCR_DPI / POINTS_PER_INCH, OCR_DPI / POINTS_PER_INCH)  # scale to OCR_DPI
        pix = page.get_pixmap(matrix=mat)
        from PIL import Image
        import io
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))

        # Use both English and Hindi (Devanagari) for Indian documents
        # Falls back gracefully to 'eng' if 'hin' language pack not installed
        try:
            ocr_text = pytesseract.image_to_string(img, lang=TESSERACT_LANGUAGES)
        except pytesseract.TesseractError:
            ocr_text = pytesseract.image_to_string(img, lang="eng")

        return ocr_text

    except Exception as e:
        return f"[OCR ERROR on page {page_num}]: {str(e)}"


# ═══════════════════════════════════════════════════════════════
# STEP 3: pdfplumber EXTRACTION (fallback + table extraction)
# ═══════════════════════════════════════════════════════════════

def _extract_text_pdfplumber(file_path: str) -> str:
    """
    Fallback extraction using pdfplumber.
    Also used to enrich PyMuPDF output with structured table data.
    Processes pages in batches for memory efficiency.
    """
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            print(
                f"    📄 {os.path.basename(file_path)}: "
                f"{total_pages} pages (pdfplumber fallback)"
            )

            for batch_start in range(0, total_pages, PAGE_BATCH_SIZE):
                batch_end = min(batch_start + PAGE_BATCH_SIZE, total_pages)

                for i in range(batch_start, batch_end):
                    page = pdf.pages[i]
                    page_content = ""

                    # Primary text
                    page_text = page.extract_text()
                    if page_text:
                        page_content += page_text + "\n"

                    # Layout extraction for misaligned text
                    try:
                        page_text_layout = page.extract_text(layout=True)
                        if page_text_layout and page_text_layout != page_text:
                            if len(page_text_layout) > len(page_text or "") * 1.2:
                                page_content += (
                                    "\n--- LAYOUT EXTRACTION ---\n"
                                    + page_text_layout + "\n"
                                )
                    except Exception:
                        pass

                    # Table extraction → DataFrame
                    tables = page.extract_tables()
                    for t_idx, table in enumerate(tables):
                        structured = _table_to_structured_text(table, i + 1, t_idx + 1)
                        if structured:
                            page_content += structured

                    if page_content.strip():
                        page_header = (
                            f"\n{'='*40}\n"
                            f"--- PAGE {i+1} of {total_pages} ---\n"
                            f"{'='*40}\n"
                        )
                        text += page_header + page_content

    except Exception as e:
        text = (
            f"[PDF EXTRACTION ERROR for {os.path.basename(file_path)}]: {str(e)}"
        )

    return text


# ═══════════════════════════════════════════════════════════════
# STEP 4: FULL-DOCUMENT OCR (only when no text extractor works)
# ═══════════════════════════════════════════════════════════════

def _extract_text_ocr_full(file_path: str) -> str:
    """
    Full-document OCR fallback (entire PDF is scanned / image-based).
    Uses pdf2image + pytesseract with batch page processing.
    Requires: pip install pdf2image pytesseract
    System: apt-get install tesseract-ocr tesseract-ocr-hin poppler-utils
    """
    if not OCR_AVAILABLE:
        return (
            f"[OCR NOT AVAILABLE for {os.path.basename(file_path)}]: "
            "Install: pip install pdf2image pytesseract && "
            "apt-get install tesseract-ocr tesseract-ocr-hin poppler-utils"
        )

    text = ""
    try:
        # Get total page count without loading all images
        from pdf2image import pdfinfo_from_path
        try:
            info = pdfinfo_from_path(file_path)
            total_pages = info["Pages"]
        except Exception:
            total_pages = None

        total_label = str(total_pages) if total_pages else "?"
        print(
            f"    🔍 OCR: {os.path.basename(file_path)}: "
            f"{total_label} pages at {OCR_DPI} DPI (batched)"
        )

        # Process in batches to avoid loading all pages into RAM
        batch_start = 1
        page_counter = 0
        while True:
            batch_end = batch_start + PAGE_BATCH_SIZE - 1
            images = convert_from_path(
                file_path,
                dpi=OCR_DPI,
                first_page=batch_start,
                last_page=batch_end,
            )
            if not images:
                break

            for img in images:
                page_counter += 1
                try:
                    page_text = pytesseract.image_to_string(img, lang=TESSERACT_LANGUAGES)
                except pytesseract.TesseractError:
                    page_text = pytesseract.image_to_string(img, lang="eng")

                if page_text.strip():
                    page_header = (
                        f"\n{'='*40}\n"
                        f"--- PAGE {page_counter} of {total_label} (OCR) ---\n"
                        f"{'='*40}\n"
                    )
                    text += page_header + page_text + "\n"

            if len(images) < PAGE_BATCH_SIZE:
                break  # Last batch was smaller → reached end of document
            batch_start += PAGE_BATCH_SIZE

    except Exception as e:
        text = f"[OCR ERROR for {os.path.basename(file_path)}]: {str(e)}"

    return text


# ═══════════════════════════════════════════════════════════════
# STEP 5: TABLE ENRICHMENT — merge pdfplumber tables into PyMuPDF output
# ═══════════════════════════════════════════════════════════════

def _enrich_with_tables(pymupdf_text: str, file_path: str) -> str:
    """
    Extract structured tables via pdfplumber and append them to PyMuPDF text.
    This combines PyMuPDF's superior text layout with pdfplumber's table parser.
    Only runs if pdfplumber is installed.
    """
    if not PDFPLUMBER_AVAILABLE:
        return pymupdf_text

    table_sections = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                for t_idx, table in enumerate(tables):
                    structured = _table_to_structured_text(table, i + 1, t_idx + 1)
                    if structured:
                        table_sections.append(structured)
    except Exception:
        pass  # Non-critical: PyMuPDF text is already useful

    if table_sections:
        return pymupdf_text + "\n\n=== STRUCTURED TABLES (pdfplumber) ===\n" + "\n".join(table_sections)
    return pymupdf_text


# ═══════════════════════════════════════════════════════════════
# STEP 6: MAIN ENTRY POINT — Hybrid extraction pipeline
# ═══════════════════════════════════════════════════════════════

def extract_text_from_pdf(file_path: str) -> str:
    """
    HYBRID extraction pipeline for large Indian financial PDFs:

    1. Try PyMuPDF (fitz) — fastest, best layout, per-page OCR for scanned pages
    2. Fall back to pdfplumber if PyMuPDF is not installed
    3. Fall back to full OCR if neither text extractor yields content
    4. Enrich with pdfplumber table extraction when PyMuPDF is primary

    Handles:
      - 200+ page documents via batch page processing (20 pages at a time)
      - Mixed documents (some pages text, some scanned) via per-page detection
      - Indian financial tables (Balance Sheet, P&L, Schedules)
      - Hindi/Devanagari text via Tesseract language packs
    """
    basename = os.path.basename(file_path)

    if PYMUPDF_AVAILABLE:
        print(f"    📋 {basename} → Using PyMuPDF (primary)")
        extracted = _extract_text_pymupdf(file_path)
        # Enrich with structured tables from pdfplumber
        extracted = _enrich_with_tables(extracted, file_path)
    elif PDFPLUMBER_AVAILABLE:
        print(f"    📋 {basename} → Using pdfplumber (PyMuPDF not installed)")
        extracted = _extract_text_pdfplumber(file_path)
    else:
        print(f"    📋 {basename} → Using full OCR (no text extractor available)")
        extracted = _extract_text_ocr_full(file_path)

    # If extraction yielded almost nothing, try full OCR as last resort
    if len(extracted.strip()) < 200 and OCR_AVAILABLE:
        print(
            f"    ⚠️  Very little text extracted ({len(extracted.strip())} chars). "
            f"Attempting full OCR..."
        )
        ocr_text = _extract_text_ocr_full(file_path)
        if len(ocr_text.strip()) > len(extracted.strip()):
            extracted = ocr_text

    print(f"    📊 Extracted {len(extracted):,} characters from {basename}")
    return extracted


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

    print(
        f"  📊 Total extraction: {total_chars:,} characters "
        f"from {len(file_paths)} file(s)"
    )
    return results


def combine_all_documents(extracted_docs: dict) -> str:
    """
    Combines all extracted documents into one string for the parser agent.
    No truncation — Gemini 1.5 Flash handles up to 1,000,000 tokens.
    """
    combined = ""
    for filename, text in extracted_docs.items():
        combined += f"\n\n{'='*60}\n"
        combined += f"DOCUMENT: {filename}\n"
        combined += f"{'='*60}\n"
        combined += text

    print(f"  📊 Combined document text: {len(combined):,} characters")
    return combined