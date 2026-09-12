import json
from pathlib import Path
from src.config import load_config

def test_eval_questions_structure():
    """Verify that eval_questions.jsonl is well-formed with required fields and valid jurisdictions."""
    cfg = load_config()
    eval_file = Path(cfg.paths.eval_dir) / "eval_questions.jsonl"
    assert eval_file.exists(), f"Missing eval file: {eval_file}"

    with open(eval_file, "r", encoding="utf-8") as f:
        rows = [json.loads(line.strip()) for line in f if line.strip()]

    assert len(rows) >= 10, f"Expected at least 10 eval questions, found {len(rows)}"

    valid_jurisdictions = set(cfg.jurisdictions)

    for row in rows:
        assert "id" in row, "Each eval row must have an 'id'"
        assert "question" in row, "Each eval row must have a 'question'"
        assert "jurisdiction" in row, "Each eval row must have a 'jurisdiction'"
        assert row["jurisdiction"] in valid_jurisdictions, (
            f"Invalid jurisdiction '{row['jurisdiction']}', expected one of {valid_jurisdictions}"
        )
        assert len(row["question"].strip()) > 10, "Question text is too short"
