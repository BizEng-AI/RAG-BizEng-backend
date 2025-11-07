# ocr_pdf.py
from __future__ import annotations
import os, re, sys, io
from pathlib import Path
from typing import List
from pdf2image import convert_from_path, pdfinfo_from_path
from PIL import Image
import pytesseract
import unicodedata
from unidecode import unidecode

# --- Configure for Windows (if needed)
# If Tesseract isn't in PATH, set it explicitly:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# Poppler path (bin folder) for pdf2image on Windows:
POPLER_PATH = r"C:\poppler\Library\bin"  # adjust to where you unzipped poppler

def normalize_text(s: str) -> str:
    # Normalize Unicode, fix spacing, kill control chars, turn fancy bullets into plain ones, etc.
    s = unicodedata.normalize("NFKC", s)
    # Replace common mojibake bullets/dashes with ASCII
    s = s.replace("•", "- ").replace("▪", "- ").replace("–", "-").replace("—", "-")
    # Remove zero-width stuff
    s = re.sub(r"[\u200B-\u200D\uFEFF]", "", s)
    # Fix stray combining accents
    s = unicodedata.normalize("NFKC", s)
    # Optional: transliterate odd diacritics that often show up broken
    s = unidecode(s)
    # Collapse excessive whitespace
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def dehyphenate_lines(text: str) -> str:
    # Join words broken at line end with hyphen: “informa-\ntion” -> “information”
    return re.sub(r"(\w+)-\n(\w+)", r"\1\2\n", text)

def strip_line_numbers_headers(text: str) -> str:
    # Textbooks often have running headers/footers; remove super-short “page artifacts”.
    cleaned = []
    for line in text.splitlines():
        # Skip pure page numbers or header-like lines
        if re.fullmatch(r"\s*\d+\s*", line):
            continue
        if len(line.strip()) <= 2:
            # over-aggressive? keep if you want
            continue
        cleaned.append(line)
    return "\n".join(cleaned)

def ocr_pdf(pdf_path: str, dpi: int = 300, lang: str = "eng", batch_size: int = 10) -> str:
    pdf = Path(pdf_path)
    assert pdf.exists(), f"PDF not found: {pdf.resolve()}"
    print(f"[ocr] PDF: {pdf.resolve()}  dpi={dpi}", flush=True)

    # Get total page count without loading all pages
    info = pdfinfo_from_path(pdf_path, poppler_path=POPLER_PATH)
    total_pages = info["Pages"]
    print(f"[ocr] pages: {total_pages}", flush=True)

    parts: List[str] = []
    config = r"--oem 3 --psm 6"

    # Process in batches to avoid memory issues
    for start_page in range(1, total_pages + 1, batch_size):
        end_page = min(start_page + batch_size - 1, total_pages)

        # Only load batch_size pages at a time
        try:
            images: List[Image.Image] = convert_from_path(
                pdf_path, dpi=dpi, poppler_path=POPLER_PATH,
                first_page=start_page, last_page=end_page
            )

            for i, img in enumerate(images, start=start_page):
                gray = img.convert("L")
                txt = pytesseract.image_to_string(gray, lang=lang, config=config)
                txt = dehyphenate_lines(txt)
                txt = normalize_text(txt)
                parts.append(txt)

                if i % 5 == 0 or i == total_pages:
                    print(f"[ocr] page {i}/{total_pages}", flush=True)

                # Free memory
                img.close()
                del gray

            # Clear batch from memory
            del images

        except Exception as e:
            print(f"[ocr] ERROR on pages {start_page}-{end_page}: {e}", flush=True)
            print(f"[ocr] Continuing with next batch...", flush=True)
            continue

    out = "\n\n".join(parts)
    out = strip_line_numbers_headers(out)
    return out

def main():
    if len(sys.argv) < 3:
        print("Usage: python ocr_pdf.py <input.pdf> <output.txt>", file=sys.stderr)
        sys.exit(2)
    pdf_in = sys.argv[1]
    txt_out = sys.argv[2]
    text = ocr_pdf(pdf_in, dpi=300, lang="eng")
    Path(txt_out).write_text(text, encoding="utf-8")
    print(f"[ocr] wrote: {Path(txt_out).resolve()}  chars={len(text):,}", flush=True)

if __name__ == "__main__":
    main()
