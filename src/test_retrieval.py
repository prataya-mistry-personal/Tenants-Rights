"""Evaluation test runner for FAISS retrieval across all benchmark questions."""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config
from src.retriever import retrieve


def run_retrieval_eval(top_k: int = 3) -> Dict[str, Any]:
    """Run all evaluation questions through the retriever and print top results."""
    cfg = load_config()
    eval_file = Path(cfg.paths.eval_dir) / "eval_questions.jsonl"

    if not eval_file.exists():
        raise FileNotFoundError(f"Evaluation questions not found at {eval_file}")

    questions: List[Dict[str, Any]] = []
    with open(eval_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))

    print("=" * 80)
    print(f"       RUNNING RETRIEVAL EVALUATION ({len(questions)} Questions, Top-{top_k})")
    print("=" * 80)

    top1_scores = []
    all_scores = []
    retrieved_sources_counter = Counter()

    for idx, q_item in enumerate(questions, start=1):
        q_id = q_item.get("id", f"eval_{idx:02d}")
        question = q_item["question"]
        jurisdiction = q_item.get("jurisdiction")
        category = q_item.get("category", "general")

        results = retrieve(question, k=top_k, jurisdiction=jurisdiction)

        print(f"\n[{idx:02d}/{len(questions)}] ID: {q_id} | Jurisdiction: {jurisdiction} | Category: {category}")
        safe_q = question.encode('ascii', errors='replace').decode('ascii')
        print(f"Query: \"{safe_q}\"")

        if results:
            top1_scores.append(results[0]["score"])
            for r in results:
                all_scores.append(r["score"])
                retrieved_sources_counter[r["source_type"]] += 1
                safe_title = r["title"][:50].encode('ascii', errors='replace').decode('ascii')
                snippet = r["text"][:130].replace("\n", " ").encode('ascii', errors='replace').decode('ascii')
                print(f"  -> Rank {r['rank']} (Score: {r['score']:.4f}) [{r['source_type'].upper()}] [{r['jurisdiction']}] {safe_title}")
                print(f"     \"{snippet}...\"")
        else:
            print("  -> [NO CHUNKS RETRIEVED]")

    avg_top1 = sum(top1_scores) / len(top1_scores) if top1_scores else 0.0
    avg_all = sum(all_scores) / len(all_scores) if all_scores else 0.0

    print("\n" + "=" * 80)
    print("                      RETRIEVAL EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Total Questions Evaluated : {len(questions)}")
    print(f"Mean Top-1 Cosine Score   : {avg_top1:.4f}")
    print(f"Mean Top-{top_k} Cosine Score  : {avg_all:.4f}")
    print(f"Retrieved Source Types    : {dict(retrieved_sources_counter)}")
    print("=" * 80)

    return {
        "total_questions": len(questions),
        "mean_top1_score": avg_top1,
        "mean_all_score": avg_all,
        "sources_distribution": dict(retrieved_sources_counter)
    }


if __name__ == "__main__":
    run_retrieval_eval(top_k=3)
