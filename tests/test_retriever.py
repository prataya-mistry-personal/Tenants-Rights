from pathlib import Path
import pytest
from src.build_index import build_faiss_index
from src.retriever import retrieve, LegalRetriever

def test_build_index():
    """Verify that FAISS IndexFlatIP index is built and total matches embedding count."""
    index, ntotal = build_faiss_index()
    index_file = Path("data/embeddings/faiss.index")

    assert index_file.exists()
    assert ntotal >= 30
    assert index.ntotal == ntotal
    assert index.d == 384


def test_retriever_query():
    """Verify retrieval returns ranked results for tenancy query."""
    results = retrieve("security deposit deduction without bill", k=3)
    assert len(results) == 3

    for r in results:
        assert "rank" in r
        assert "score" in r
        assert "chunk_id" in r
        assert "text" in r
        assert "source_type" in r
        assert "jurisdiction" in r


def test_retriever_jurisdiction_filtering():
    """Verify that jurisdiction filtering includes matching jurisdiction and central statutes."""
    results_blr = retrieve("water and electricity supply disconnected", k=5, jurisdiction="Bengaluru")
    assert len(results_blr) > 0

    valid_jurisdictions = {"bengaluru", "other", "general", "central"}
    for r in results_blr:
        assert r["jurisdiction"].lower() in valid_jurisdictions
