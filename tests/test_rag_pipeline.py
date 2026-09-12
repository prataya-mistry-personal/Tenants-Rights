from src.prompts import build_prompt, format_context
from src.rag_pipeline import answer

def test_prompt_builder():
    """Verify that prompt builder injects context, query, and structure correctly."""
    mock_chunks = [
        {
            "chunk_id": "c1",
            "title": "Model Tenancy Act 2021",
            "source_type": "statute",
            "jurisdiction": "Other",
            "text": "Section 11 states security deposit shall not exceed two months rent."
        }
    ]
    prompt = build_prompt("How much deposit can landlord charge?", mock_chunks, jurisdiction="Delhi")

    assert "Jurisdiction of Inquiry: Delhi" in prompt
    assert "Model Tenancy Act 2021" in prompt
    assert "Section 11" in prompt
    assert "How much deposit can landlord charge?" in prompt


def test_rag_pipeline_end_to_end():
    """Verify that the full RAG pipeline generates a coherent, cited answer with disclaimer."""
    query = "Can landlord in Bengaluru disconnect water supply?"
    result = answer(query, jurisdiction="Bengaluru", return_details=True)

    assert isinstance(result, dict)
    assert "answer" in result
    assert "retrieved_chunks" in result
    assert len(result["retrieved_chunks"]) > 0
    assert len(result["answer"].strip()) > 30

    # Verify disclaimer is included
    assert "Disclaimer:" in result["answer"]
