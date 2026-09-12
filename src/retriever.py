"""Retriever module for semantic legal search over FAISS index with optional jurisdiction filtering."""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config


class LegalRetriever:
    """Singleton/Cached retriever for FAISS legal chunk search."""

    def __init__(self):
        self.cfg = load_config()
        raw_index_path = Path(self.cfg.embeddings.faiss_index_path)
        self.index_path = raw_index_path if raw_index_path.is_absolute() else PROJECT_ROOT / raw_index_path
        raw_ids_path = Path(self.cfg.embeddings.chunk_ids_path)
        self.ids_path = raw_ids_path if raw_ids_path.is_absolute() else PROJECT_ROOT / raw_ids_path
        self.model_name = self.cfg.embeddings.model_name

        self._index: Optional[faiss.Index] = None
        self._model: Optional[SentenceTransformer] = None
        self._metadata: Optional[List[Dict[str, Any]]] = None

    def _load_resources(self):
        if self._index is None:
            if not self.index_path.exists():
                raise FileNotFoundError(
                    f"FAISS index not found at {self.index_path}. Run src/build_index.py first."
                )
            self._index = faiss.read_index(str(self.index_path))

        if self._metadata is None:
            if not self.ids_path.exists():
                raise FileNotFoundError(
                    f"Metadata IDs not found at {self.ids_path}. Run src/generate_embeddings.py first."
                )
            self._metadata = []
            with open(self.ids_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        self._metadata.append(json.loads(line))

        if self._model is None:
            self._model = SentenceTransformer(self.model_name)

    def retrieve(
        self,
        query: str,
        k: int = 5,
        jurisdiction: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve top-k relevant chunks for a user query with optional jurisdiction filtering.

        Args:
            query: Natural language legal question or statement.
            k: Number of chunks to return.
            jurisdiction: Optional jurisdiction filter ('Bengaluru', 'Delhi', 'Other', 'General').
                          When specified, prioritizes local laws/judgments while allowing central/general acts.

        Returns:
            List of ranked chunk dictionaries with similarity scores and metadata.
        """
        self._load_resources()
        assert self._model is not None and self._index is not None and self._metadata is not None

        # Encode query
        query_vec = self._model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True
        ).astype(np.float32)

        # Retrieve extra candidates if filtering
        fetch_k = min(k * 8 if jurisdiction else k, self._index.ntotal)
        scores, indices = self._index.search(query_vec, fetch_k)

        flat_scores = scores[0]
        flat_indices = indices[0]

        results: List[Dict[str, Any]] = []

        for score, idx in zip(flat_scores, flat_indices):
            if idx < 0 or idx >= len(self._metadata):
                continue

            meta = self._metadata[idx]
            chunk_jurisdiction = meta.get("jurisdiction", "Other")

            # Jurisdiction filter
            if jurisdiction:
                target = jurisdiction.strip().lower()
                chunk_j = chunk_jurisdiction.strip().lower()
                # Accept if exact match OR if chunk is from central/general statutes/judgments
                is_match = (
                    chunk_j == target or
                    chunk_j in ["other", "general", "central"] or
                    target in ["other", "general"]
                )
                if not is_match:
                    continue

            results.append({
                "rank": len(results) + 1,
                "score": float(score),
                "chunk_id": meta["chunk_id"],
                "doc_id": meta["doc_id"],
                "title": meta.get("title", meta["doc_id"]),
                "source_type": meta.get("source_type", "unknown"),
                "jurisdiction": chunk_jurisdiction,
                "category": meta.get("category", "general"),
                "url": meta.get("url", ""),
                "text": meta["text"]
            })

            if len(results) >= k:
                break

        return results


# Global singleton instance for easy module-level import
_RETRIEVER_INSTANCE: Optional[LegalRetriever] = None


def retrieve(
    query: str,
    k: int = 5,
    jurisdiction: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Module-level retrieve wrapper."""
    global _RETRIEVER_INSTANCE
    if _RETRIEVER_INSTANCE is None:
        _RETRIEVER_INSTANCE = LegalRetriever()
    return _RETRIEVER_INSTANCE.retrieve(query, k=k, jurisdiction=jurisdiction)


if __name__ == "__main__":
    # Quick CLI test
    sample_query = "Can landlord cut off water electricity supply in Bengaluru?"
    print(f"\nSearching: '{sample_query}' (jurisdiction='Bengaluru', k=3)\n")
    chunks = retrieve(sample_query, k=3, jurisdiction="Bengaluru")
    for c in chunks:
        print(f"[{c['rank']}] Score: {c['score']:.4f} | {c['source_type'].upper()} ({c['jurisdiction']}): {c['title'][:55]}")
        print(f"    Snippet: {c['text'][:140].replace(chr(10), ' ')}...\n")
