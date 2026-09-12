from pathlib import Path
import pdfplumber
from src.fetch_statutes import fetch_all_statutes, STATUTE_DATA

def test_fetch_and_verify_statutes():
    """Verify that all statute PDFs are generated and contain valid extractable text."""
    paths = fetch_all_statutes()
    assert len(paths) == len(STATUTE_DATA)

    for pdf_path in paths:
        assert pdf_path.exists(), f"PDF does not exist: {pdf_path}"
        with pdfplumber.open(pdf_path) as pdf:
            assert len(pdf.pages) >= 1
            extracted = "".join(page.extract_text() or "" for page in pdf.pages)
            assert len(extracted) > 150, f"Extracted text too short in {pdf_path.name}"
            # Verify key legal terms appear
            assert "Section" in extracted or "Act" in extracted
