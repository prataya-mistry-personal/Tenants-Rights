from pathlib import Path
import json
from src.extract_pdf_text import extract_all_statutes
from src.clean_judgments import clean_all_judgments, clean_judgment_body

def test_extract_statutes():
    """Verify that statute text files are extracted and readable."""
    statute_files = extract_all_statutes()
    assert len(statute_files) >= 3

    for txt_file in statute_files:
        assert txt_file.exists()
        with open(txt_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert len(content) > 100
            assert "Section" in content or "Act" in content


def test_clean_judgments():
    """Verify that judgment files are stripped of boilerplate and saved with metadata."""
    cleaned_files = clean_all_judgments()
    assert len(cleaned_files) >= 10

    # Test boilerplate stripping
    sample_dirty = "Some text [Cites 5, Cited by 2]\n\n\n\nIndian Kanoon - http://indiankanoon.org/doc/123\n\nMore text."
    cleaned = clean_judgment_body(sample_dirty)
    assert "[Cites" not in cleaned
    assert "Indian Kanoon" not in cleaned
    assert "More text." in cleaned

    # Check metadata file
    meta_file = Path("data/processed/judgments/cleaned_metadata.jsonl")
    assert meta_file.exists()
    with open(meta_file, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    assert len(records) == len(cleaned_files)
