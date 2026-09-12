"""Embedding generation and vector sanity check module for legal text chunks.

Uses sentence-transformers (all-MiniLM-L6-v2) to generate normalized dense embeddings
for all chunks in data/chunks/chunks.jsonl, saving to data/embeddings/chunk_embeddings.npy
and data/embeddings/chunk_ids.jsonl.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config


def load_chunks(chunks_file: Path) -> List[Dict[str, Any]]:
    """Load all chunk dictionaries from JSONL file."""
    if not chunks_file.exists():
        raise FileNotFoundError(f"Chunks file not found at {chunks_file}. Run src/chunk_documents.py first.")

    chunks = []
    with open(chunks_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def generate_embeddings(
    chunks_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    batch_size: int = 64
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """Generate dense normalized embeddings for all chunks and save to disk."""
    cfg = load_config()
    in_file = chunks_path or Path(cfg.paths.chunks_dir) / "chunks.jsonl"
    out_dir = output_dir or Path(cfg.paths.embeddings_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading chunks from: {in_file}")
    chunks = load_chunks(in_file)
    if not chunks:
        raise ValueError(f"No chunks found in {in_file}")

    print(f"Total chunks to embed: {len(chunks)}")
    texts = [c["text"] for c in chunks]

    model_name = cfg.embeddings.model_name
    print(f"Loading embedding model: '{model_name}' on CPU...")
    model = SentenceTransformer(model_name)

    print(f"Encoding {len(texts)} chunks (batch_size={batch_size})...")
    # normalize_embeddings=True makes inner product identical to cosine similarity
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    # Convert to float32
    embeddings = embeddings.astype(np.float32)

    # Prepare metadata records
    chunk_metadata = []
    for idx, c in enumerate(chunks):
        chunk_metadata.append({
            "index": idx,
            "chunk_id": c["chunk_id"],
            "doc_id": c["doc_id"],
            "title": c.get("title", c["doc_id"]),
            "source_type": c.get("source_type", "unknown"),
            "jurisdiction": c.get("jurisdiction", "Other"),
            "category": c.get("category", "general"),
            "word_count": c.get("word_count", len(c["text"].split())),
            "char_count": c.get("char_count", len(c["text"])),
            "text": c["text"]
        })

    # Save files
    emb_file = out_dir / "chunk_embeddings.npy"
    ids_file = out_dir / "chunk_ids.jsonl"

    np.save(emb_file, embeddings)
    with open(ids_file, "w", encoding="utf-8") as f:
        for item in chunk_metadata:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # Step 4.1 verification: embeddings.shape[0] == len(chunk_ids)
    print("\n" + "=" * 60)
    print("           EMBEDDING GENERATION SUMMARY (Phase 4.1)")
    print("=" * 60)
    print(f"Embedding Matrix Shape : {embeddings.shape} (rows x dimensions)")
    print(f"Chunk Metadata Count   : {len(chunk_metadata)}")
    print(f"Model Name             : {model_name}")
    print(f"Saved Embeddings File  : {emb_file}")
    print(f"Saved Metadata File    : {ids_file}")
    print("=" * 60)

    assert embeddings.shape[0] == len(chunk_metadata), (
        f"Mismatch: embeddings rows ({embeddings.shape[0]}) != metadata count ({len(chunk_metadata)})"
    )

    return embeddings, chunk_metadata


def sanity_check_retrieval(
    query: str,
    top_k: int = 5,
    embeddings_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """Sanity check: Embed a query and retrieve top-k nearest chunks by cosine similarity."""
    cfg = load_config()
    emb_dir = embeddings_dir or Path(cfg.paths.embeddings_dir)

    emb_file = emb_dir / "chunk_embeddings.npy"
    ids_file = emb_dir / "chunk_ids.jsonl"

    if not emb_file.exists() or not ids_file.exists():
        raise FileNotFoundError("Embedding artifacts missing. Run generate_embeddings() first.")

    embeddings = np.load(emb_file)
    with open(ids_file, "r", encoding="utf-8") as f:
        chunk_metadata = [json.loads(line) for line in f if line.strip()]

    model = SentenceTransformer(cfg.embeddings.model_name)
    query_vec = model.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)[0]

    # Cosine similarity is dot product because vectors are L2 normalized
    scores = np.dot(embeddings, query_vec)
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    print("\n" + "-" * 70)
    print(f"SANITY CHECK QUERY: \"{query}\" (Top {top_k} Nearest Chunks)")
    print("-" * 70)

    for rank, idx in enumerate(top_indices, start=1):
        score = float(scores[idx])
        meta = chunk_metadata[idx]
        raw_snip = meta["text"][:180].replace("\n", " ") + "..."
        safe_snip = raw_snip.encode('ascii', errors='replace').decode('ascii')
        safe_title = meta['title'][:55].encode('ascii', errors='replace').decode('ascii')
        print(f"\n[{rank}] Score: {score:.4f} | ID: {meta['chunk_id']} | Jurisdiction: {meta['jurisdiction']}")
        print(f"    Source: {meta['source_type'].upper()} - {safe_title}")
        print(f"    Snippet: {safe_snip}")

        results.append({
            "rank": rank,
            "score": score,
            "chunk_id": meta["chunk_id"],
            "title": meta["title"],
            "jurisdiction": meta["jurisdiction"],
            "source_type": meta["source_type"],
            "text": meta["text"]
        })

    print("-" * 70)
    return results


if __name__ == "__main__":
    embeddings, chunk_metadata = generate_embeddings()

    # Step 4.2 Sanity check queries
    test_queries = [
        "security deposit not returned by landlord after moving out",
        "landlord disconnected water and electricity supply to force eviction",
        "notice period required before landlord enters tenant apartment",
    ]

    print("\n=== RUNNING STEP 4.2 SANITY CHECKS ===")
    for q in test_queries:
        sanity_check_retrieval(q, top_k=5)
