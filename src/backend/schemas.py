"""Pydantic data validation schemas for the Tenant Rights Legal RAG API."""

from typing import List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Source citation reference supporting the legal answer."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    doc_id: str = Field(..., description="Document identifier")
    title: str = Field(..., description="Statute or Court judgment title")
    source_type: str = Field(..., description="statute or judgment")
    jurisdiction: str = Field(..., description="Applicable jurisdiction (e.g., Bengaluru, Delhi, General)")
    score: float = Field(..., description="Semantic similarity relevance score")
    snippet: str = Field(..., description="Text excerpt from the legal source")
    url: Optional[str] = Field(None, description="Direct URL to legal document if available")


class QueryRequest(BaseModel):
    """User inquiry request payload."""
    question: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="Natural language question about tenant rights or rental disputes",
        examples=["My landlord in Bangalore cut off my water supply over rent dispute. What can I do?"]
    )
    jurisdiction: Optional[str] = Field(
        default="Bengaluru",
        description="Target city or state jurisdiction ('Bengaluru', 'Delhi', 'Other' or null for all-India)",
        examples=["Bengaluru"]
    )
    top_k: Optional[int] = Field(
        default=4,
        ge=1,
        le=10,
        description="Number of legal source chunks to retrieve"
    )


class QueryResponse(BaseModel):
    """Structured response payload returned by the legal assistant."""
    query: str
    jurisdiction: Optional[str]
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    disclaimer: str


class HealthResponse(BaseModel):
    """System and pipeline health status."""
    status: str
    faiss_loaded: bool
    total_chunks: int
    llm_provider: str
    llm_model: str


class SourceItem(BaseModel):
    """Metadata summary of an indexed statute or judgment."""
    doc_id: str
    title: str
    source_type: str
    jurisdiction: str
    chunks_count: int
    url: Optional[str] = None


class SourcesResponse(BaseModel):
    """Corpus transparency response listing available statutes and case judgments."""
    statutes: List[SourceItem] = Field(default_factory=list)
    judgments: List[SourceItem] = Field(default_factory=list)
    total_statutes: int
    total_judgments: int
