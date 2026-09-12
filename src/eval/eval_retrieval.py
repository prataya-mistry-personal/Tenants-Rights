"""Retrieval evaluation module for Indian Metro Tenant Rights RAG system.

Computes Precision@k, Recall/HitRate@k, MRR, and Mean Cosine Similarity
against benchmark evaluation dataset (`data/eval/eval_questions.jsonl`).
"""

import sys
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
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

STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all",
    "any", "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
    "can", "will", "just", "don", "should", "now", "vs", "versus",
    # Domain-generic background words
    "act", "section", "sec", "rent", "tenancy", "tenant", "landlord", "law", "code"
}


def extract_keywords(text: str) -> List[str]:
    """Tokenize and filter keywords from text."""
    tokens = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
    return [t for t in tokens if len(t) > 2 and t not in STOPWORDS]


def is_chunk_relevant(
    chunk: Dict[str, Any],
    expected_topic: str,
    category: str,
    expected_sources: Optional[List[str]] = None
) -> bool:
    """Determine if a retrieved chunk is legally relevant to the evaluation topic.

    Uses keyword/entity matching against statutory titles, sections, and chunk body.
    """
    chunk_title = chunk.get("title", "").lower()
    chunk_text = chunk.get("text", "").lower()
    combined_content = f"{chunk_title} {chunk_text}"

    # 1. Check explicit expected sources if provided
    if expected_sources:
        for src in expected_sources:
            if src.lower() in combined_content:
                return True

    topic_tokens = extract_keywords(expected_topic)
    if not topic_tokens:
        # Fallback to category
        return category.lower() in combined_content

    # 2. Check for statutory section matches (e.g., 'section 44', 'section 108', 'section 14')
    section_matches = re.findall(r"section\s+(\d+[a-zA-Z]*)", expected_topic.lower())
    for sec in section_matches:
        sec_pattern = rf"\bsection\s+{sec}\b"
        if re.search(sec_pattern, combined_content):
            return True

    # 3. Specific legal topic aliases & synonyms
    synonym_map = {
        "utilities": ["water", "electricity", "amenities", "essential services", "maintenance"],
        "security_deposit": ["security deposit", "advance", "refund", "wear and tear", "deduction", "painting"],
        "eviction": ["evict", "possession", "vacate", "grounds for eviction", "notice to quit"],
        "entry_notice": ["entry", "inspection", "notice", "privacy", "reasonable hours"],
        "rent_revision": ["rent increase", "revision", "unilateral", "escalation", "agreed rent"],
        "repairs": ["repair", "maintenance", "damage", "whitewash", "plumbing"],
        "subletting": ["sublet", "sub-tenant", "assign", "possession", "unauthorized"],
        "rent_default": ["default", "arrears", "non-payment", "withhold"],
        "harassment": ["harass", "pressure", "force", "threaten", "essential services"],
        "rent_receipts": ["receipt", "proof of payment", "acknowledgment", "counterfoil"]
    }

    # 4. Token overlap calculation
    matched_tokens = [t for t in topic_tokens if t in combined_content]
    overlap_ratio = len(matched_tokens) / len(topic_tokens) if topic_tokens else 0.0

    # If >50% of expected topic keywords match, it's relevant
    if overlap_ratio >= 0.50:
        return True

    # 5. Check category synonym overlap
    cat_terms = synonym_map.get(category.lower(), [])
    cat_match = any(term in combined_content for term in cat_terms)
    if cat_match and overlap_ratio >= 0.30:
        return True

    return False


def evaluate_retrieval(
    top_k_values: Optional[List[int]] = None,
    eval_file_path: Optional[Path] = None,
    output_metrics_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Run retrieval evaluation across all benchmark questions and compute metrics."""
    if top_k_values is None:
        top_k_values = [1, 3, 5]

    cfg = load_config()
    eval_path = eval_file_path or (PROJECT_ROOT / cfg.paths.eval_dir / "eval_questions.jsonl")
    out_path = output_metrics_path or (PROJECT_ROOT / cfg.paths.eval_dir / "retrieval_metrics.json")

    if not eval_path.exists():
        raise FileNotFoundError(f"Evaluation questions not found at {eval_path}")

    questions: List[Dict[str, Any]] = []
    with open(eval_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))

    max_k = max(top_k_values)
    total_q = len(questions)

    precisions = {k: [] for k in top_k_values}
    recalls = {k: [] for k in top_k_values}
    reciprocal_ranks = []
    top1_scores = []
    mean_scores = {k: [] for k in top_k_values}

    jurisdiction_stats = defaultdict(lambda: {"total": 0, "hit_at_3": 0, "mrr": 0.0, "p_at_3": 0.0})
    category_stats = defaultdict(lambda: {"total": 0, "hit_at_3": 0, "mrr": 0.0, "p_at_3": 0.0})
    per_query_results = []

    print("=" * 80)
    print(f"       RUNNING SYSTEM RETRIEVAL EVALUATION ({total_q} Benchmark Questions)")
    print("=" * 80)

    for idx, q_item in enumerate(questions, start=1):
        q_id = q_item.get("id", f"eval_{idx:02d}")
        question = q_item["question"]
        jurisdiction = q_item.get("jurisdiction")
        category = q_item.get("category", "general")
        expected_topic = q_item.get("expected_topic", "")
        expected_sources = q_item.get("expected_sources", [])

        # Retrieve top max_k results
        results = retrieve(question, k=max_k, jurisdiction=jurisdiction)

        # Evaluate relevance per retrieved rank
        relevance_flags = [
            is_chunk_relevant(chunk, expected_topic, category, expected_sources)
            for chunk in results
        ]

        # Cosine similarity scores
        scores = [chunk.get("score", 0.0) for chunk in results]
        if scores:
            top1_scores.append(scores[0])

        # Compute MRR for this query
        first_rel_rank = next((i + 1 for i, rel in enumerate(relevance_flags) if rel), 0)
        rr = (1.0 / first_rel_rank) if first_rel_rank > 0 else 0.0
        reciprocal_ranks.append(rr)

        # Compute metrics across top-k values
        query_metrics = {
            "id": q_id,
            "question": question,
            "jurisdiction": jurisdiction,
            "category": category,
            "expected_topic": expected_topic,
            "mrr": rr,
            "first_relevant_rank": first_rel_rank,
            "retrieved_ranks": []
        }

        for k in top_k_values:
            k_flags = relevance_flags[:k]
            k_scores = scores[:k]
            p_k = sum(k_flags) / k if k > 0 else 0.0
            r_k = 1.0 if any(k_flags) else 0.0
            mean_score_k = sum(k_scores) / len(k_scores) if k_scores else 0.0

            precisions[k].append(p_k)
            recalls[k].append(r_k)
            mean_scores[k].append(mean_score_k)
            query_metrics[f"precision@{k}"] = round(p_k, 4)
            query_metrics[f"recall@{k}"] = round(r_k, 4)

        for rank_idx, (chunk, rel) in enumerate(zip(results, relevance_flags), start=1):
            query_metrics["retrieved_ranks"].append({
                "rank": rank_idx,
                "title": chunk.get("title", ""),
                "score": round(chunk.get("score", 0.0), 4),
                "is_relevant": rel
            })

        per_query_results.append(query_metrics)

        # Accumulate category & jurisdiction breakdowns (at k=3)
        p3 = query_metrics["precision@3"] if 3 in top_k_values else query_metrics[f"precision@{top_k_values[0]}"]
        r3 = query_metrics["recall@3"] if 3 in top_k_values else query_metrics[f"recall@{top_k_values[0]}"]

        jurisdiction_stats[jurisdiction or "Unknown"]["total"] += 1
        jurisdiction_stats[jurisdiction or "Unknown"]["hit_at_3"] += int(r3 > 0)
        jurisdiction_stats[jurisdiction or "Unknown"]["mrr"] += rr
        jurisdiction_stats[jurisdiction or "Unknown"]["p_at_3"] += p3

        category_stats[category]["total"] += 1
        category_stats[category]["hit_at_3"] += int(r3 > 0)
        category_stats[category]["mrr"] += rr
        category_stats[category]["p_at_3"] += p3

    # Aggregate summaries
    overall_metrics = {
        "total_questions": total_q,
        "mrr": round(sum(reciprocal_ranks) / total_q, 4) if total_q else 0.0,
        "mean_top1_cosine": round(sum(top1_scores) / len(top1_scores), 4) if top1_scores else 0.0,
    }

    for k in top_k_values:
        overall_metrics[f"precision@{k}"] = round(sum(precisions[k]) / total_q, 4)
        overall_metrics[f"recall@{k}"] = round(sum(recalls[k]) / total_q, 4)
        overall_metrics[f"mean_cosine@{k}"] = round(sum(mean_scores[k]) / total_q, 4)

    # Format jurisdiction summary
    jurisdiction_summary = {}
    for jur, stats in jurisdiction_stats.items():
        cnt = stats["total"]
        jurisdiction_summary[jur] = {
            "total_questions": cnt,
            "recall@3_hit_rate": round(stats["hit_at_3"] / cnt, 4) if cnt else 0.0,
            "precision@3": round(stats["p_at_3"] / cnt, 4) if cnt else 0.0,
            "mrr": round(stats["mrr"] / cnt, 4) if cnt else 0.0
        }

    # Format category summary
    category_summary = {}
    for cat, stats in category_stats.items():
        cnt = stats["total"]
        category_summary[cat] = {
            "total_questions": cnt,
            "recall@3_hit_rate": round(stats["hit_at_3"] / cnt, 4) if cnt else 0.0,
            "precision@3": round(stats["p_at_3"] / cnt, 4) if cnt else 0.0,
            "mrr": round(stats["mrr"] / cnt, 4) if cnt else 0.0
        }

    output_data = {
        "overall_metrics": overall_metrics,
        "jurisdiction_breakdown": jurisdiction_summary,
        "category_breakdown": category_summary,
        "per_query_results": per_query_results
    }

    # Ensure destination directory exists and write metrics JSON
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    # Display report to console
    print("\n" + "=" * 80)
    print("                    RETRIEVAL EVALUATION RESULTS")
    print("=" * 80)
    print(f"Total Benchmark Questions : {total_q}")
    print(f"Mean Reciprocal Rank (MRR): {overall_metrics['mrr']:.4f}")
    for k in top_k_values:
        print(f"Precision@{k}               : {overall_metrics[f'precision@{k}']:.4f}")
        print(f"Recall@{k} (Hit Rate)      : {overall_metrics[f'recall@{k}']:.4f}")
        print(f"Mean Cosine Similarity@{k} : {overall_metrics[f'mean_cosine@{k}']:.4f}")
    print("-" * 80)
    print("Performance by Jurisdiction:")
    for jur, s in jurisdiction_summary.items():
        print(f"  * {jur:<12}: Recall@3={s['recall@3_hit_rate']:.4f}, P@3={s['precision@3']:.4f}, MRR={s['mrr']:.4f} (N={s['total_questions']})")
    print("=" * 80)
    print(f"Results saved to: {out_path.relative_to(PROJECT_ROOT) if out_path.is_relative_to(PROJECT_ROOT) else out_path}\n")

    return output_data


if __name__ == "__main__":
    evaluate_retrieval()
