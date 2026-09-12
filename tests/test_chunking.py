import json
from pathlib import Path
from src.chunk_documents import build_all_chunks, split_into_sentences, chunk_text

def test_split_into_sentences():
    """Test that legal abbreviations and section numbers do not cause premature splitting."""
    sample = "Section 27 of the Karnataka Rent Act, 1999 applies. In Dr. B.R. Ambedkar v. State of Karnataka, the Hon'ble Court held Sec. 44 protects utilities."
    sents = split_into_sentences(sample)
    assert len(sents) == 2
    assert "Karnataka Rent Act, 1999 applies." in sents[0]
    assert "Sec. 44 protects utilities." in sents[1]


def test_chunking_execution():
    """Verify that all source documents produce valid, non-empty, sentence-bounded chunks."""
    chunks = build_all_chunks()
    assert len(chunks) >= 30, f"Expected at least 30 chunks, got {len(chunks)}"

    chunk_file = Path("data/chunks/chunks.jsonl")
    assert chunk_file.exists()

    with open(chunk_file, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    assert len(records) == len(chunks)

    for c in records:
        assert "chunk_id" in c
        assert "doc_id" in c
        assert "text" in c
        assert "source_type" in c
        # Verify chunk text is non-empty string with valid length
        assert isinstance(c["text"], str)
        assert len(c["text"].strip()) > 50, "Chunk text too short"
        assert c["word_count"] > 0
