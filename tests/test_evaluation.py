"""Unit and integration tests for Phase 7 Evaluation modules."""

import pytest
from pathlib import Path
from src.eval.eval_retrieval import is_chunk_relevant, extract_keywords
from src.eval.eval_generation import (
    evaluate_faithfulness,
    extract_content_words,
    extract_citations,
    split_into_sentences
)
from src.eval.generate_report import generate_evaluation_report


def test_extract_keywords_and_content_words():
    topic = "utility charges and maintenance obligations"
    kw = extract_keywords(topic)
    assert "utility" in kw
    assert "charges" in kw
    assert "maintenance" in kw
    assert "obligations" in kw
    assert "and" not in kw


def test_is_chunk_relevant_section_and_topic_match():
    chunk_relevant = {
        "title": "The Karnataka Rent Act, 1999 - Section 44 Cutting off or withholding essential supply or service",
        "text": "No landlord shall without just or sufficient cause cut off or withhold any essential supply or service enjoyed by the tenant in respect of the premises let to him.",
        "jurisdiction": "Bengaluru"
    }
    chunk_irrelevant = {
        "title": "Delhi Rent Control Act, 1958 - Section 14",
        "text": "Eviction of tenant on grounds of non-payment of rent or subletting.",
        "jurisdiction": "Delhi"
    }

    # Test Section 44 essential supply match
    assert is_chunk_relevant(
        chunk=chunk_relevant,
        expected_topic="Karnataka Rent Act Section 44 essential services",
        category="utilities"
    ) is True

    # Test irrelevant chunk
    assert is_chunk_relevant(
        chunk=chunk_irrelevant,
        expected_topic="Karnataka Rent Act Section 44 essential services",
        category="utilities"
    ) is False


def test_is_chunk_relevant_category_synonym():
    chunk = {
        "title": "Karnataka High Court Judgment - Security Deposit",
        "text": "The landlord cannot make arbitrary deductions for ordinary wear and tear of the premises.",
        "jurisdiction": "Bengaluru"
    }
    assert is_chunk_relevant(
        chunk=chunk,
        expected_topic="security deposit refund and notice",
        category="security_deposit"
    ) is True


def test_split_into_sentences_and_citations():
    text = (
        "Under Section 44 of the Karnataka Rent Act 1999, the landlord cannot disconnect water.\n"
        "- The tenant should issue a written notice to the landlord.\n"
        "- You can approach the Rent Controller for restoration of amenities.\n"
        "Disclaimer: This is for educational guidance and does not constitute formal legal advice."
    )
    sentences = split_into_sentences(text)
    assert len(sentences) >= 2
    # Ensure disclaimer is excluded
    assert not any("educational guidance" in s.lower() for s in sentences)

    citations = extract_citations(text)
    assert "44" in citations["sections"]
    assert any("karnataka rent act" in act.lower() for act in citations["acts"])


def test_evaluate_faithfulness_grounded_vs_hallucinated():
    context_chunks = [
        {
            "title": "The Karnataka Rent Act, 1999 - Section 44",
            "text": "No landlord shall cut off or withhold water and electricity supplies. The Rent Controller may order restoration.",
            "jurisdiction": "Bengaluru"
        }
    ]

    # Grounded answer
    grounded_ans = (
        "Under Section 44 of the Karnataka Rent Act, the landlord cannot cut off water and electricity supplies. "
        "The tenant may approach the Rent Controller to order restoration."
    )
    res_grounded = evaluate_faithfulness(grounded_ans, context_chunks)
    assert res_grounded["groundedness_score"] >= 0.70
    assert res_grounded["is_flagged"] is False
    assert "44" in res_grounded["verified_sections"]

    # Hallucinated answer (cites non-existent Section 999 and unrelated claims)
    hallucinated_ans = (
        "According to Section 999 of the Martian Tenancy Code, space rent is strictly regulated by orbital authorities. "
        "Rocket fuel taxes cannot be deducted arbitrarily."
    )
    res_hallucinated = evaluate_faithfulness(hallucinated_ans, context_chunks)
    assert res_hallucinated["groundedness_score"] < 0.60
    assert res_hallucinated["is_flagged"] is True
    assert "999" in res_hallucinated["unverified_sections"]


def test_generate_report_execution(tmp_path):
    report_file = tmp_path / "test_eval_report.md"
    content = generate_evaluation_report(output_report_path=report_file)
    assert report_file.exists()
    assert "# Indian Metro Tenant Rights RAG — System Evaluation Report" in content
    assert "Mean Reciprocal Rank (MRR)" in content
