"""Prompt templates and context formatting for Tenant Rights RAG system."""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


LEGAL_SYSTEM_PROMPT = (
    "You are an expert AI legal information assistant specializing in Indian Tenant and Rental Law.\n"
    "Your objective is to provide accurate, concise, and structured legal guidance to tenants.\n\n"
    "STRICT GUIDELINES:\n"
    "1. Answer ONLY using the facts, statutes, and legal rulings present in the provided Legal Context.\n"
    "2. If the context does not contain enough information to answer, clearly state what is known from the context and advise consulting a legal professional.\n"
    "3. Mention which section, act, or court judgment you are drawing from INLINE in the text (e.g., 'According to Section 44 of the Karnataka Rent Act 1999...' or 'In Ramji Prasad vs DM Allahabad...').\n"
    "4. Highlight practical next steps for the tenant (such as preserving evidence, issuing written notice, or filing a petition before the Rent Authority/Court).\n"
    "5. ALWAYS conclude your answer with this exact disclaimer:\n"
    "   'Disclaimer: This response provides general legal information based on Indian statutes and case law and does not constitute formal legal advice.'"
)


def format_context(chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved chunk dictionaries into a clean, numbered context block for the LLM."""
    if not chunks:
        return "No relevant legal context found."

    context_blocks = []
    for idx, c in enumerate(chunks, start=1):
        title = c.get("title", c.get("doc_id", f"Source {idx}"))
        source_type = c.get("source_type", "reference").upper()
        jurisdiction = c.get("jurisdiction", "General")
        category = c.get("category", "")
        text = c.get("text", "").strip()

        header = f"[Source {idx}: {title} | Type: {source_type} | Jurisdiction: {jurisdiction}]"
        context_blocks.append(f"{header}\n{text}")

    return "\n\n" + ("=" * 50) + "\n\n".join([""] + context_blocks) + "\n" + ("=" * 50)


def build_prompt(
    query: str,
    chunks: List[Dict[str, Any]],
    jurisdiction: Optional[str] = None
) -> str:
    """Build the final user prompt incorporating jurisdiction, retrieved context, and the user's question."""
    context_str = format_context(chunks)
    jurisdiction_str = f"Jurisdiction of Inquiry: {jurisdiction.strip()}\n" if jurisdiction else "Jurisdiction: General / Indian Law\n"

    prompt = (
        f"{jurisdiction_str}\n"
        f"LEGAL CONTEXT EXCERPTS:\n"
        f"{context_str}\n\n"
        f"TENANT'S INQUIRY:\n"
        f"{query.strip()}\n\n"
        f"INSTRUCTIONS:\n"
        f"Synthesize a clear, structured response answering the tenant's inquiry based strictly on the excerpts above.\n"
        f"Cite relevant acts, sections, and case precedents inline, provide actionable next steps, and include the mandatory disclaimer."
    )

    return prompt


if __name__ == "__main__":
    # Test demonstration of build_prompt
    mock_chunks = [
        {
            "chunk_id": "statute_karnataka_rent_act_1999_002",
            "doc_id": "karnataka_rent_act_1999",
            "title": "THE KARNATAKA RENT ACT, 1999",
            "source_type": "statute",
            "jurisdiction": "Bengaluru",
            "category": "statutory",
            "text": "Section 44 - Cutting Off or Withholding Essential Supply or Service: (1) No landlord shall, without just and sufficient cause, cut off or withhold any essential supply or service enjoyed by the tenant in respect of the premises let to him."
        },
        {
            "chunk_id": "judgment_ik_1183921_001",
            "doc_id": "ik_1183921",
            "title": "B.V. Manjunatha vs Smt. Gangamma (Karnataka High Court)",
            "source_type": "judgment",
            "jurisdiction": "Bengaluru",
            "category": "utility_disconnection",
            "text": "The High Court directed immediate reconnection of water pipeline to the tenant's apartment in Bengaluru and confirmed that tenant disputes cannot be resolved by depriving tenants of potable water."
        }
    ]

    sample_q = "My landlord in Bengaluru has turned off the water valve to force me to leave. What are my rights?"
    sample_prompt = build_prompt(sample_q, mock_chunks, jurisdiction="Bengaluru")

    print("\n--- SAMPLE BUILT PROMPT ---")
    print(sample_prompt)
    print("---------------------------")
