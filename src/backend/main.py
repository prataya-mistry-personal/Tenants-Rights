"""FastAPI application for Indian Tenant Rights Legal Assistant."""

import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.retriever import LegalRetriever
from src.rag_pipeline import answer
from src.backend.schemas import (
    QueryRequest,
    QueryResponse,
    Citation,
    HealthResponse,
    SourceItem,
    SourcesResponse,
)

# Initialize FastAPI application
app = FastAPI(
    title="Indian Tenant Rights AI Legal Assistant API",
    description="Backend API for semantic legal search and grounded guidance on Indian metro tenancy laws.",
    version="0.1.0",
)

# CORS middleware for local web development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cached sources cache
_SOURCES_CACHE: Optional[SourcesResponse] = None


def _load_sources_summary() -> SourcesResponse:
    """Read and aggregate corpus sources from chunk metadata."""
    global _SOURCES_CACHE
    if _SOURCES_CACHE is not None:
        return _SOURCES_CACHE

    cfg = load_config()
    ids_path = PROJECT_ROOT / cfg.embeddings.chunk_ids_path

    statute_map: Dict[str, Dict[str, Any]] = {}
    judgment_map: Dict[str, Dict[str, Any]] = {}

    if ids_path.exists():
        with open(ids_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                meta = json.loads(line)
                doc_id = meta.get("doc_id", "unknown")
                source_type = meta.get("source_type", "statute").lower()
                target_map = statute_map if source_type == "statute" else judgment_map

                if doc_id not in target_map:
                    target_map[doc_id] = {
                        "doc_id": doc_id,
                        "title": meta.get("title", doc_id),
                        "source_type": source_type,
                        "jurisdiction": meta.get("jurisdiction", "General"),
                        "chunks_count": 0,
                        "url": meta.get("url"),
                    }
                target_map[doc_id]["chunks_count"] += 1

    statutes = [SourceItem(**item) for item in statute_map.values()]
    judgments = [SourceItem(**item) for item in judgment_map.values()]

    _SOURCES_CACHE = SourcesResponse(
        statutes=statutes,
        judgments=judgments,
        total_statutes=len(statutes),
        total_judgments=len(judgments),
    )
    return _SOURCES_CACHE


# Basic out-of-scope keywords for safety check
OUT_OF_SCOPE_TOPICS = [
    "murder", "homicide", "narcotics", "drug trafficking",
    "weapon", "bomb", "kidnapping", "cybercrime", "rape"
]

DEFAULT_DISCLAIMER = (
    "Disclaimer: This response provides general legal information based on Indian statutes "
    "and case law and does not constitute formal legal advice. For binding legal representation, "
    "please consult a qualified advocate."
)


@app.get("/health", response_model=HealthResponse, tags=["System"])
def get_health():
    """Check health of the FAISS retriever and configured LLM provider."""
    cfg = load_config()
    index_path = PROJECT_ROOT / cfg.embeddings.faiss_index_path
    
    total_chunks = 0
    faiss_loaded = False
    if index_path.exists():
        try:
            retriever = LegalRetriever()
            retriever._load_resources()
            assert retriever._index is not None
            total_chunks = retriever._index.ntotal
            faiss_loaded = True
        except Exception:
            faiss_loaded = False

    return HealthResponse(
        status="ok" if faiss_loaded else "degraded",
        faiss_loaded=faiss_loaded,
        total_chunks=total_chunks,
        llm_provider=cfg.llm.provider,
        llm_model=cfg.llm.model_name,
    )


@app.get("/sources", response_model=SourcesResponse, tags=["Corpus"])
def get_sources():
    """List all indexed statutes and court judgments available in the legal database."""
    return _load_sources_summary()


@app.post("/query", response_model=QueryResponse, tags=["Legal Assistant"])
def query_tenant_rights(request: QueryRequest):
    """Answer tenant questions using semantic retrieval and Groq LLM generation."""
    question = request.question.strip()

    # Safety check: Detect clearly out-of-scope non-tenancy criminal topics
    lower_q = question.lower()
    if any(topic in lower_q for topic in OUT_OF_SCOPE_TOPICS):
        return QueryResponse(
            query=question,
            jurisdiction=request.jurisdiction,
            answer=(
                "I specialize specifically in Indian Tenant & Rental Law (such as security deposits, "
                "unlawful eviction, essential service cutoffs, lease agreements, and Rent Authority procedures). "
                "Your inquiry appears to fall outside residential/commercial tenancy law. "
                "Please consult a qualified criminal law advocate or local authorities."
            ),
            citations=[],
            disclaimer=DEFAULT_DISCLAIMER,
        )

    try:
        result = answer(
            query=question,
            jurisdiction=request.jurisdiction,
            k=request.top_k,
            return_details=True,
        )
        assert isinstance(result, dict)

        # Convert retrieved chunks into structured Citation objects
        citations: List[Citation] = []
        for c in result.get("retrieved_chunks", []):
            citations.append(
                Citation(
                    chunk_id=c.get("chunk_id", ""),
                    doc_id=c.get("doc_id", ""),
                    title=c.get("title", c.get("doc_id", "Unknown")),
                    source_type=c.get("source_type", "statute"),
                    jurisdiction=c.get("jurisdiction", "General"),
                    score=round(float(c.get("score", 0.0)), 4),
                    snippet=c.get("text", "")[:350],
                    url=c.get("url") or None,
                )
            )

        raw_answer: str = result.get("answer", "")
        
        # Ensure clean separation of answer and disclaimer
        clean_answer = raw_answer
        disclaimer = DEFAULT_DISCLAIMER
        if "Disclaimer:" in raw_answer:
            parts = raw_answer.split("Disclaimer:", 1)
            clean_answer = parts[0].strip()
            disclaimer = f"Disclaimer:{parts[1].strip()}"

        return QueryResponse(
            query=question,
            jurisdiction=request.jurisdiction,
            answer=clean_answer,
            citations=citations,
            disclaimer=disclaimer,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate legal guidance: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.backend.main:app", host="127.0.0.1", port=8000, reload=True)
