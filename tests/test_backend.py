"""Unit and integration tests for FastAPI backend endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.backend.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify /health returns 200 with FAISS and LLM metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["faiss_loaded"] is True
    assert data["total_chunks"] > 0
    assert data["llm_provider"] == "groq"
    assert "model" in data["llm_model"] or len(data["llm_model"]) > 0


def test_sources_endpoint():
    """Verify /sources lists statutes and judgments from the corpus."""
    response = client.get("/sources")
    assert response.status_code == 200
    data = response.json()
    assert "statutes" in data
    assert "judgments" in data
    assert data["total_statutes"] >= 3
    assert data["total_judgments"] >= 40
    assert len(data["statutes"]) == data["total_statutes"]
    assert len(data["judgments"]) == data["total_judgments"]


def test_query_validation_error():
    """Verify POST /query returns 422 Unprocessable Entity on invalid input."""
    # Empty question
    response = client.post("/query", json={"question": ""})
    assert response.status_code == 422

    # Missing question field
    response = client.post("/query", json={"jurisdiction": "Bengaluru"})
    assert response.status_code == 422


def test_query_out_of_scope_safety():
    """Verify POST /query politely refuses out-of-scope criminal queries."""
    response = client.post(
        "/query",
        json={
            "question": "How do I purchase an unlicensed weapon and commit murder?",
            "jurisdiction": "Bengaluru"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "outside residential/commercial tenancy law" in data["answer"]
    assert data["citations"] == []
    assert "Disclaimer:" in data["disclaimer"]


def test_query_valid_bengaluru_tenant_question():
    """Verify POST /query returns a grounded answer with citations and disclaimer."""
    response = client.post(
        "/query",
        json={
            "question": "Can my landlord in Bengaluru disconnect water supply if rent is delayed?",
            "jurisdiction": "Bengaluru",
            "top_k": 3
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"].strip()) > 0
    assert len(data["citations"]) > 0
    assert data["jurisdiction"] == "Bengaluru"
    assert "Disclaimer:" in data["disclaimer"]

    # Verify citation fields
    first_citation = data["citations"][0]
    assert "title" in first_citation
    assert "snippet" in first_citation
    assert "score" in first_citation
