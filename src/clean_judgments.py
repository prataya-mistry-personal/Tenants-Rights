"""Clean and normalize raw judgment text files from Indian Kanoon."""

import sys
import re
import json
import html
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config


BOILERPLATE_PATTERNS = [
    r'\[Cites\s*\d+\s*,\s*Cited by\s*\d+\s*\]',
    r'\[Cites\s*\d+\s*\]',
    r'\[Cited by\s*\d+\s*\]',
    r'Indian Kanoon\s*-\s*http[s]?://[^\s]+',
    r'Try out our Premium Member services[^\n]+',
    r'Get this document in PDF[^\n]+',
    r'User Queries\s*\n[^\n]+',
    r'Take notes as you read[^\n]+',
]


def clean_judgment_body(raw_body: str) -> str:
    """Normalize whitespace, remove Indian Kanoon boilerplate and clean legal text."""
    text = raw_body

    # Unescape HTML entities
    text = html.unescape(text)

    # Remove Indian Kanoon boilerplate tags and artifacts
    for pattern in BOILERPLATE_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Remove excessive repeated symbols (lines of dashes, underscores, dots)
    text = re.sub(r'[-_=*~]{4,}', '---', text)

    # Normalize unicode quotes and dashes
    text = text.replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('\u201c', '"').replace('\u201d', '"')
    text = text.replace('\u2013', '-').replace('\u2014', '--')
    text = text.replace('\xa0', ' ')

    # Normalize line breaks and spaces
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.splitlines()]
    
    # Remove empty lines at start/end and collapse consecutive empty lines
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        if not line:
            if not prev_empty:
                cleaned_lines.append('')
                prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False

    cleaned_text = "\n".join(cleaned_lines).strip()
    return cleaned_text


def parse_raw_judgment_file(file_path: Path) -> Tuple[Dict[str, str], str]:
    """Parse header metadata and raw body text from a saved raw judgment file."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    metadata: Dict[str, str] = {}
    body = content

    if "============================================================" in content:
        parts = content.split("============================================================", 1)
        header_part = parts[0]
        body = parts[1] if len(parts) > 1 else ""

        for line in header_part.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                metadata[key.strip().lower()] = val.strip()

    return metadata, body


def clean_all_judgments(
    raw_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None
) -> List[Path]:
    """Clean all judgment files in raw_dir and save to processed_dir."""
    cfg = load_config()
    input_dir = raw_dir or Path(cfg.paths.raw_data_dir) / "judgments"
    output_dir = processed_dir or Path(cfg.paths.processed_data_dir) / "judgments"
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_files = [f for f in input_dir.glob("*.txt") if f.name != "judgments_metadata.jsonl"]
    if not raw_files:
        raise FileNotFoundError(f"No judgment text files found in {input_dir}. Run src/fetch_judgments.py first.")

    print(f"Cleaning {len(raw_files)} judgment files...")
    cleaned_files: List[Path] = []
    metadata_records: List[Dict[str, Any]] = []

    for file_path in raw_files:
        metadata, raw_body = parse_raw_judgment_file(file_path)
        cleaned_body = clean_judgment_body(raw_body)

        # Fallback if body was empty
        if not cleaned_body and raw_body:
            cleaned_body = raw_body.strip()

        out_path = output_dir / file_path.name

        # Re-attach standardized metadata header
        header = (
            f"Title: {metadata.get('title', file_path.stem)}\n"
            f"Court: {metadata.get('court', 'Unknown Court')}\n"
            f"Date: {metadata.get('date', 'Unknown Date')}\n"
            f"Jurisdiction: {metadata.get('jurisdiction', 'Other')}\n"
            f"Category: {metadata.get('category', 'general')}\n"
            f"URL: {metadata.get('url', '')}\n"
            f"{'='*60}\n\n"
        )

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(header + cleaned_body)

        cleaned_files.append(out_path)
        metadata_records.append({
            "doc_id": file_path.stem,
            "filename": file_path.name,
            "title": metadata.get("title", file_path.stem),
            "court": metadata.get("court", "Unknown Court"),
            "date": metadata.get("date", "Unknown Date"),
            "jurisdiction": metadata.get("jurisdiction", "Other"),
            "category": metadata.get("category", "general"),
            "url": metadata.get("url", ""),
            "raw_chars": len(raw_body),
            "cleaned_chars": len(cleaned_body),
            "word_count": len(cleaned_body.split())
        })

    # Save cleaned master metadata index
    meta_path = output_dir / "cleaned_metadata.jsonl"
    with open(meta_path, "w", encoding="utf-8") as f:
        for rec in metadata_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[OK] Cleaned {len(cleaned_files)} judgments saved to {output_dir}")
    print(f"[OK] Saved metadata index to {meta_path}")
    return cleaned_files


if __name__ == "__main__":
    files = clean_all_judgments()
    print(f"\nProcessing complete. {len(files)} cleaned judgment files ready.")
