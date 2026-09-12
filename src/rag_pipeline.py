"""End-to-end RAG pipeline chaining FAISS retriever, legal prompt builder, and LLM generator."""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import io

# Ensure UTF-8 output on Windows consoles
for _stream in (sys.stdout, sys.stderr):
    if isinstance(_stream, io.TextIOWrapper):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

from src.config import load_config
from src.retriever import retrieve
from src.prompts import build_prompt, LEGAL_SYSTEM_PROMPT
from src.llm_client import generate


def answer(
    query: str,
    jurisdiction: Optional[str] = None,
    k: Optional[int] = None,
    max_new_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    return_details: bool = False
) -> Union[str, Dict[str, Any]]:
    """Generate a legally grounded, cited answer for a tenant dispute inquiry.

    Args:
        query: Tenant's natural language question.
        jurisdiction: City or state jurisdiction ('Bengaluru', 'Delhi', 'Other').
        k: Number of legal chunks to retrieve (defaults to config retrieval.top_k).
        max_new_tokens: Maximum token length for response.
        temperature: Generation temperature (greedy / low temp default).
        return_details: If True, returns full dict with answer, retrieved chunks, and prompt.

    Returns:
        String answer or detailed dictionary.
    """
    cfg = load_config()
    top_k = k or cfg.retrieval.top_k

    # Step 1: Semantic Retrieval over FAISS
    chunks = retrieve(query=query, k=top_k, jurisdiction=jurisdiction)

    # Step 2: Build Structured Grounding Prompt
    prompt = build_prompt(query=query, chunks=chunks, jurisdiction=jurisdiction)

    # Step 3: LLM Generation
    response_text = generate(
        prompt=prompt,
        system_prompt=LEGAL_SYSTEM_PROMPT,
        max_new_tokens=max_new_tokens,
        temperature=temperature
    )

    # Ensure legal disclaimer is always present
    disclaimer_text = "Disclaimer: This response provides general legal information based on Indian statutes and case law and does not constitute formal legal advice."
    if "Disclaimer:" not in response_text:
        response_text = response_text.rstrip() + f"\n\n{disclaimer_text}"

    if return_details:
        return {
            "query": query,
            "jurisdiction": jurisdiction,
            "answer": response_text,
            "retrieved_chunks": chunks,
            "prompt_used": prompt
        }

    return response_text


if __name__ == "__main__":
    sample_queries = [
        {
            "q": "My landlord in Bengaluru has cut off my water and electricity supply because I refused an arbitrary rent hike. Is this legal and what can I do?",
            "jurisdiction": "Bengaluru"
        },
        {
            "q": "My landlord is refusing to refund my security deposit after I vacated the apartment, claiming arbitrary painting charges without any bills.",
            "jurisdiction": "Bengaluru"
        },
        {
            "q": "Can my landlord enter my rented apartment without any prior notice while I am away?",
            "jurisdiction": "Delhi"
        }
    ]

    print("\n" + "=" * 80)
    print("           END-TO-END RAG PIPELINE DEMONSTRATION")
    print("=" * 80)

    for idx, item in enumerate(sample_queries, start=1):
        q = item["q"]
        j = item["jurisdiction"]
        print(f"\n[{idx}/3] Query: {q}")
        print(f"Jurisdiction: {j}")
        print("-" * 80)

        result = answer(query=q, jurisdiction=j, return_details=True)
        assert isinstance(result, dict)

        print("\n--- RETRIEVED SOURCES ---")
        for chunk in result["retrieved_chunks"]:
            print(f"  * [{chunk['source_type'].upper()}] {chunk['title'][:60]} (Score: {chunk['score']:.4f})")

        print("\n--- GENERATED LEGAL GUIDANCE ---")
        print(result["answer"])
        print("=" * 80)
