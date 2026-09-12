import json
from pathlib import Path
from src.fetch_judgments import scrape_indian_kanoon, sanitize_filename

def test_fetch_judgments(tmp_path):
    """Verify that judgment scraping saves raw files and metadata correctly."""
    # Test with a small target count into temporary directory
    saved_files = scrape_indian_kanoon(target_count=10, output_dir=tmp_path, delay_range=(0.1, 0.2))
    assert len(saved_files) >= 10

    # Verify metadata.jsonl exists and has matching records
    metadata_file = tmp_path / "judgments_metadata.jsonl"
    assert metadata_file.exists()

    with open(metadata_file, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    assert len(records) == len(saved_files)
    for rec in records:
        assert "doc_id" in rec
        assert "title" in rec
        assert "category" in rec
        assert "char_count" in rec
        assert rec["char_count"] > 100

    # Spot check one file content
    first_file = saved_files[0]
    with open(first_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Title:" in content
        assert "Category:" in content
        assert "===" in content
