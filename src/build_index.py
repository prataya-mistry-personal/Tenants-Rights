"""FAISS Index Builder for Tenant-Landlord Legal Chunks.

Builds an exact Inner Product (cosine similarity) FAISS index (IndexFlatIP)
from data/embeddings/chunk_embeddings.npy and saves to data/embeddings/faiss.index.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import faiss

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config


def build_faiss_index(
    embeddings_file: Optional[Path] = None,
    output_index_file: Optional[Path] = None
) -> Tuple[faiss.IndexFlatIP, int]:
    """Build and save an IndexFlatIP FAISS vector index."""
    cfg = load_config()
    emb_path = embeddings_file or Path(cfg.paths.embeddings_dir) / "chunk_embeddings.npy"
    index_path = output_index_file or Path(cfg.embeddings.faiss_index_path)
    index_path.parent.mkdir(parents=True, exist_ok=True)

    if not emb_path.exists():
        raise FileNotFoundError(f"Embeddings matrix not found at {emb_path}. Run src/generate_embeddings.py first.")

    print(f"Loading embeddings from: {emb_path}")
    embeddings = np.load(emb_path).astype(np.float32)
    n_vectors, dimension = embeddings.shape

    print(f"Vectors: {n_vectors}, Dimension: {dimension}")
    print("Building faiss.IndexFlatIP (Exact Inner Product / Cosine Similarity)...")

    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    print(f"Saving FAISS index to: {index_path}")
    faiss.write_index(index, str(index_path))

    # Step 5.1 Verification: index.ntotal == embedding count
    print("\n" + "=" * 60)
    print("           FAISS INDEX BUILD SUMMARY (Step 5.1)")
    print("=" * 60)
    print(f"Index Type            : faiss.IndexFlatIP")
    print(f"Total Vectors Indexed : {index.ntotal}")
    print(f"Vector Dimensions     : {index.d}")
    print(f"Saved Index Location  : {index_path}")
    print(f"Verification Check    : index.ntotal ({index.ntotal}) == n_vectors ({n_vectors}) -> {index.ntotal == n_vectors}")
    print("=" * 60)

    assert index.ntotal == n_vectors, f"Mismatch: index.ntotal ({index.ntotal}) != n_vectors ({n_vectors})"
    return index, index.ntotal


if __name__ == "__main__":
    build_faiss_index()
