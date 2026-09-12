"""Extract and clean plain text from raw statute PDFs using pdfplumber."""

import sys
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
import pdfplumber

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config


def clean_extracted_statute_text(raw_text: str) -> str:
    """Normalize whitespace and strip running headers/footers from extracted PDF text."""
    lines = raw_text.splitlines()
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        # Remove repetitive header / footer lines
        if stripped.startswith("Tenant Rights Legal Reference Repository"):
            continue
        if re.match(r"^Page \d+$", stripped, re.IGNORECASE):
            continue
        cleaned_lines.append(stripped)

    # Rejoin lines
    text = "\n".join(cleaned_lines)
    # Collapse 3+ newlines into 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_pdf(pdf_path: Path, output_dir: Path) -> Path:
    """Extract and write text from a single PDF file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    txt_filename = pdf_path.stem + ".txt"
    out_path = output_dir / txt_filename

    extracted_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            extracted_pages.append(page_text)

    full_raw_text = "\n\n".join(extracted_pages)
    cleaned_text = clean_extracted_statute_text(full_raw_text)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(cleaned_text)

    return out_path


def extract_all_statutes(
    raw_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None
) -> List[Path]:
    """Extract plain text from all statute PDFs in raw_dir into processed_dir."""
    cfg = load_config()
    input_dir = raw_dir or Path(cfg.paths.raw_data_dir) / "statutes"
    output_dir = processed_dir or Path(cfg.paths.processed_data_dir) / "statutes"
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {input_dir}. Run src/fetch_statutes.py first.")

    processed_files = []
    print(f"Extracting text from {len(pdf_files)} statute PDFs...")
    for pdf_path in pdf_files:
        out_file = extract_pdf(pdf_path, output_dir)
        char_count = out_file.stat().st_size
        print(f"  [OK] {pdf_path.name} -> {out_file.name} ({char_count} bytes)")
        processed_files.append(out_file)

    return processed_files


if __name__ == "__main__":
    extracted = extract_all_statutes()
    print(f"\nExtraction complete. {len(extracted)} text files saved to data/processed/statutes/.")
