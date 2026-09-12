from pathlib import Path
import json
import numpy as np
from src.generate_embeddings import sanity_check_retrieval

def test_embeddings_file_integrity():
    """Verify that the generated embeddings matrix matches chunk metadata count and dimension."""
    emb_file = Path("data/embeddings/chunk_embeddings.npy")
    ids_file = Path("data/embeddings/chunk_ids.jsonl")

    assert emb_file.exists(), "Missing chunk_embeddings.npy"
    assert ids_file.exists(), "Missing chunk_ids.jsonl"

    embeddings = np.load(emb_file)
    with open(ids_file, "r", encoding="utf-8") as f:
        metadata = [json.loads(line) for line in f if line.strip()]

    # Verify shapes match
    assert embeddings.shape[0] == len(metadata), f"Rows {embeddings.shape[0]} != meta count {len(metadata)}"
    assert embeddings.shape[1] == 384, f"Expected 384 dimensions, got {embeddings.shape[1]}"
    assert embeddings.dtype == np.float32

    # Verify vector normalization (L2 norm approx 1.0 for each row)
    norms = np.linalg.norm(embeddings, axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-4)


def test_sanity_check_similarity():
    """Verify that sanity check retrieval returns ranked, scored chunks."""
    results = sanity_check_retrieval("security deposit refund deduction", top_k=5)
    assert len(results) == 5

    prev_score = 1.0
    for r in results:
        assert "score" in r
        assert "chunk_id" in r
        assert "text" in r
        assert -1.0 <= r["score"] <= 1.0
        # Check scores are monotonically descending
        assert r["score"] <= prev_score
        prev_score = r["score"]

    # Top results for security deposit query should contain relevant terms
    combined_text = " ".join(r["text"] for r in results).lower()
    assert "deposit" in combined_text or "rent" in combined_text or "refund" in combined_text
