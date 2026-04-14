# utils/pdf_extractor.py
# Hybrid PDF extractor:
#   1) PyMuPDF (fitz)  — primary, fast, works for digital PDFs on all platforms
#   2) Tesseract OCR   — fallback for pages with no embedded text (scanned images)

import os

# Tesseract binary search paths (Windows)
_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\Vedant\AppData\Local\Tesseract-OCR\tesseract.exe",
]


def _get_tesseract():
    """Configure and return pytesseract, or None if unavailable."""
    try:
        import pytesseract
        for path in _TESSERACT_PATHS:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
        return pytesseract
    except ImportError:
        return None


def _ocr_page(doc, page_index: int) -> str:
    """
    Render a PDF page as image and run Tesseract OCR.
    Uses 2x scale and light preprocessing for speed + accuracy balance.
    """
    pytesseract = _get_tesseract()
    if not pytesseract:
        return "[OCR unavailable: install pytesseract]"

    try:
        from PIL import Image, ImageEnhance, ImageFilter
        import io

        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=__import__("fitz").Matrix(2, 2))

        # Convert to PIL image
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        # Lightweight preprocessing: grayscale + contrast boost
        img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(2.0)

        # Tesseract: OEM 3 (LSTM), PSM 6 (uniform block)
        text = pytesseract.image_to_string(
            img,
            config=r"--oem 3 --psm 6 -c preserve_interword_spaces=1",
            lang="eng"
        )
        return text.strip()
    except Exception as e:
        return f"[OCR error: {e}]"


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts all text from a PDF file using a hybrid approach:
    - PyMuPDF text extraction for digital pages (fast, cross-platform)
    - Tesseract OCR for scanned/image-only pages (no embedded text)

    Returns plain text string.
    """
    import fitz

    text = ""
    filename = os.path.basename(file_path)

    try:
        doc = fitz.open(file_path)
        total_pages = len(doc)
        print(f"  [PDF] {filename}: {total_pages} pages")

        ocr_pages = 0
        for i in range(total_pages):
            page = doc.load_page(i)

            # Try PyMuPDF text extraction first
            page_text = page.get_text("text").strip()

            if page_text and len(page_text) > 30:
                # Digital page — use extracted text directly
                text += f"\n--- PAGE {i+1} ---\n{page_text}\n"
            else:
                # Scanned page — fall back to Tesseract OCR
                ocr_pages += 1
                print(f"    [OCR] Page {i+1}/{total_pages} — no text, running Tesseract...")
                ocr_text = _ocr_page(doc, i)
                if ocr_text:
                    text += f"\n--- PAGE {i+1} [OCR] ---\n{ocr_text}\n"

        doc.close()

        char_count = len(text.strip())
        print(f"  [PDF] {filename}: {char_count:,} chars "
              f"({ocr_pages} OCR pages, {total_pages - ocr_pages} digital pages)")

        if char_count == 0:
            text = (f"[NO TEXT in {filename}: All pages are scanned images with "
                    f"no extractable text. Ensure Tesseract is installed.]")

    except Exception as e:
        text = f"[PDF ERROR for {filename}]: {str(e)}"

    return text


def extract_text_from_multiple_pdfs(file_paths: list) -> dict:
    """Process multiple PDFs. Returns {filename: extracted_text}."""
    results = {}
    for path in file_paths:
        filename = os.path.basename(path)
        print(f"\nExtracting: {filename}")
        results[filename] = extract_text_from_pdf(path)
    return results


def combine_all_documents(extracted_docs: dict) -> str:
    """Combines all extracted documents into one string for the parser agent."""
    combined = ""
    for filename, text in extracted_docs.items():
        combined += f"\n\n{'='*60}\n"
        combined += f"DOCUMENT: {filename}\n"
        combined += f"{'='*60}\n"
        combined += text
    return combined