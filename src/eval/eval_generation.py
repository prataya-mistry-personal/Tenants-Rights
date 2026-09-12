"""Generation groundedness and faithfulness evaluation module.

Evaluates generated answers against retrieved legal chunks using sentence-level
context overlap heuristics, statutory citation verification, and automated flagging
of potential hallucination / unsupported claims.
"""

import sys
import os
import json
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
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
from src.rag_pipeline import answer as generate_rag_answer

STOPWORDS: Set[str] = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "is", "are", "was", "were", "be", "been", "being", "have", "has",
    "had", "do", "does", "did", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all",
    "any", "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
    "can", "will", "just", "don", "should", "now", "vs", "versus", "this", "that",
    "these", "those", "you", "your", "they", "their", "it", "its", "may", "must",
    "also", "based", "according", "following", "provided", "step", "actions"
}

STANDARD_DISCLAIMER_PATTERNS = [
    r"disclaimer:?.*$",
    r"this information is for educational guidance.*$",
    r"does not constitute formal legal advice.*$"
]


def extract_content_words(text: str) -> List[str]:
    """Extract filtered content words from text."""
    tokens = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
    return [t for t in tokens if len(t) > 2 and t not in STOPWORDS]


def clean_answer_for_eval(answer_text: str) -> str:
    """Remove boilerplate disclaimers and introductory intros before sentence analysis."""
    lines = []
    for line in answer_text.split("\n"):
        cleaned_line = line.strip()
        # Strip disclaimers
        if re.search(r"disclaimer:", cleaned_line, re.IGNORECASE):
            continue
        if cleaned_line:
            lines.append(cleaned_line)
    return "\n".join(lines)


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences and bullet points for granular evaluation."""
    cleaned = clean_answer_for_eval(text)
    # Split by standard sentence delimiters and numbered/bullet items
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n\s*[-*•\d+.]\s*", cleaned)
    sentences = []
    for s in raw_sentences:
        s_clean = s.strip()
        # Filter out trivial fragments or markdown headers
        if len(s_clean) > 15 and not s_clean.startswith("#") and not s_clean.endswith(":"):
            sentences.append(s_clean)
    return sentences


def extract_citations(text: str) -> Dict[str, List[str]]:
    """Extract statutory sections and legal acts cited in the text."""
    sections = re.findall(r"\b(?:section|sec\.?)\s+(\d+[a-zA-Z]*)", text, re.IGNORECASE)
    acts = []
    act_patterns = [
        r"karnataka rent act(?:,?\s*1999)?",
        r"model tenancy act(?:,?\s*2021)?",
        r"delhi rent control act(?:,?\s*1958)?",
        r"transfer of property act(?:,?\s*1882)?",
        r"consumer protection act(?:,?\s*2019)?",
        r"indian contract act(?:,?\s*1872)?"
    ]
    for pattern in act_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                acts.append(match.group(0).strip())

    return {
        "sections": list(set(sections)),
        "acts": list(set(acts))
    }


def evaluate_faithfulness(
    answer_text: str,
    retrieved_chunks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Compute sentence-level groundedness and statutory citation accuracy.

    Returns:
        Dict containing groundedness_score, citation_accuracy, supported_sentences,
        unsupported_sentences, citations_verified, citations_unverified, and flag status.
    """
    context_corpus = " ".join([
        f"{chunk.get('title', '')} {chunk.get('text', '')}"
        for chunk in retrieved_chunks
    ]).lower()

    sentences = split_into_sentences(answer_text)
    supported_sentences = []
    unsupported_sentences = []

    for sentence in sentences:
        sent_words = extract_content_words(sentence)
        if not sent_words:
            continue

        # Check keyword overlap ratio
        matched = [w for w in sent_words if w in context_corpus]
        overlap_ratio = len(matched) / len(sent_words)

        # Check bigram / phrase overlap
        bigrams = [f"{sent_words[i]} {sent_words[i+1]}" for i in range(len(sent_words) - 1)]
        matched_bigrams = [bg for bg in bigrams if bg in context_corpus]
        bigram_ratio = len(matched_bigrams) / len(bigrams) if bigrams else 0.0

        # Heuristic support condition:
        # A sentence is supported if either:
        # 1. Overlap ratio >= 0.40 OR
        # 2. Bigram ratio >= 0.25 and overlap >= 0.30
        is_supported = (overlap_ratio >= 0.40) or (bigram_ratio >= 0.25 and overlap_ratio >= 0.30)

        sent_detail = {
            "sentence": sentence,
            "overlap_ratio": round(overlap_ratio, 3),
            "bigram_ratio": round(bigram_ratio, 3),
            "supported": is_supported
        }

        if is_supported:
            supported_sentences.append(sent_detail)
        else:
            unsupported_sentences.append(sent_detail)

    total_sentences = len(sentences)
    sent_groundedness = (
        len(supported_sentences) / total_sentences if total_sentences > 0 else 1.0
    )

    # Citation Verification
    answer_citations = extract_citations(answer_text)
    verified_sections = []
    unverified_sections = []

    for sec in answer_citations["sections"]:
        sec_pattern = rf"\bsection\s+{sec}\b"
        if re.search(sec_pattern, context_corpus, re.IGNORECASE):
            verified_sections.append(sec)
        else:
            unverified_sections.append(sec)

    verified_acts = []
    unverified_acts = []
    for act in answer_citations["acts"]:
        if act.lower() in context_corpus:
            verified_acts.append(act)
        else:
            unverified_acts.append(act)

    total_citations = len(answer_citations["sections"]) + len(answer_citations["acts"])
    verified_citations = len(verified_sections) + len(verified_acts)
    citation_accuracy = (
        (verified_citations / total_citations) if total_citations > 0 else 1.0
    )

    # Composite Groundedness Score
    if total_citations > 0:
        composite_score = (0.75 * sent_groundedness) + (0.25 * citation_accuracy)
    else:
        composite_score = sent_groundedness

    # Determine whether to flag for manual review
    # Flag if groundedness < 0.60 OR unverified statutory sections were cited
    is_flagged = (composite_score < 0.60) or (len(unverified_sections) > 0)
    flag_reasons = []
    if composite_score < 0.60:
        flag_reasons.append(f"Low sentence overlap ({sent_groundedness:.2f})")
    if unverified_sections:
        flag_reasons.append(f"Unverified section citations in context: {unverified_sections}")

    return {
        "groundedness_score": round(composite_score, 4),
        "sentence_groundedness": round(sent_groundedness, 4),
        "citation_accuracy": round(citation_accuracy, 4),
        "total_sentences": total_sentences,
        "supported_sentences_count": len(supported_sentences),
        "unsupported_sentences_count": len(unsupported_sentences),
        "verified_sections": verified_sections,
        "unverified_sections": unverified_sections,
        "verified_acts": verified_acts,
        "unverified_acts": unverified_acts,
        "is_flagged": is_flagged,
        "flag_reasons": flag_reasons,
        "unsupported_sentences": unsupported_sentences[:3]  # top 3 sample unsupported
    }


def evaluate_generation(
    sample_size: Optional[int] = None,
    eval_file_path: Optional[Path] = None,
    output_metrics_path: Optional[Path] = None,
    top_k: int = 4
) -> Dict[str, Any]:
    """Execute RAG generation across benchmark questions and evaluate groundedness."""
    cfg = load_config()
    eval_path = eval_file_path or (PROJECT_ROOT / cfg.paths.eval_dir / "eval_questions.jsonl")
    out_path = output_metrics_path or (PROJECT_ROOT / cfg.paths.eval_dir / "generation_metrics.json")

    if not eval_path.exists():
        raise FileNotFoundError(f"Evaluation questions not found at {eval_path}")

    questions: List[Dict[str, Any]] = []
    with open(eval_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))

    if sample_size and sample_size < len(questions):
        # Evenly stratified sample across categories
        step = len(questions) / sample_size
        questions = [questions[int(i * step)] for i in range(sample_size)]

    total_q = len(questions)
    print("=" * 80)
    print(f"       RUNNING RAG GENERATION & GROUNDEDNESS EVALUATION ({total_q} Questions)")
    print("=" * 80)

    results = []
    groundedness_scores = []
    citation_accuracies = []
    flagged_cases = []

    jurisdiction_stats = defaultdict(lambda: {"total": 0, "groundedness_sum": 0.0, "citation_acc_sum": 0.0, "flagged": 0})
    category_stats = defaultdict(lambda: {"total": 0, "groundedness_sum": 0.0, "citation_acc_sum": 0.0, "flagged": 0})

    for idx, q_item in enumerate(questions, start=1):
        q_id = q_item.get("id", f"eval_{idx:02d}")
        question = q_item["question"]
        jurisdiction = q_item.get("jurisdiction")
        category = q_item.get("category", "general")

        print(f"\n[{idx:02d}/{total_q}] Evaluating {q_id} ({jurisdiction} - {category})...")
        safe_q = question.encode('ascii', errors='replace').decode('ascii')
        print(f"  Q: \"{safe_q[:90]}...\"")

        try:
            # Generate RAG answer with details
            rag_output = generate_rag_answer(
                query=question,
                jurisdiction=jurisdiction,
                k=top_k,
                return_details=True
            )
            assert isinstance(rag_output, dict)
            answer_text = rag_output.get("answer", "")
            retrieved_chunks = rag_output.get("retrieved_chunks", [])

            # Evaluate faithfulness / groundedness
            faith_eval = evaluate_faithfulness(answer_text, retrieved_chunks)

            score = faith_eval["groundedness_score"]
            cit_acc = faith_eval["citation_accuracy"]
            groundedness_scores.append(score)
            citation_accuracies.append(cit_acc)

            eval_entry = {
                "id": q_id,
                "question": question,
                "jurisdiction": jurisdiction,
                "category": category,
                "answer": answer_text,
                "retrieved_chunk_titles": [c.get("title") for c in retrieved_chunks],
                "groundedness": faith_eval
            }
            results.append(eval_entry)

            if faith_eval["is_flagged"]:
                flagged_cases.append({
                    "id": q_id,
                    "question": question,
                    "jurisdiction": jurisdiction,
                    "category": category,
                    "groundedness_score": score,
                    "flag_reasons": faith_eval["flag_reasons"],
                    "unsupported_sentences": [s["sentence"] for s in faith_eval["unsupported_sentences"]],
                    "unverified_sections": faith_eval["unverified_sections"]
                })
                print(f"  -> [FLAGGED] Score: {score:.3f} | Reasons: {faith_eval['flag_reasons']}")
            else:
                print(f"  -> [OK] Groundedness: {score:.3f} | Citations: {cit_acc:.3f}")

            # Accumulate breakdown stats
            jur_key = jurisdiction or "Unknown"
            jurisdiction_stats[jur_key]["total"] += 1
            jurisdiction_stats[jur_key]["groundedness_sum"] += score
            jurisdiction_stats[jur_key]["citation_acc_sum"] += cit_acc
            jurisdiction_stats[jur_key]["flagged"] += int(faith_eval["is_flagged"])

            category_stats[category]["total"] += 1
            category_stats[category]["groundedness_sum"] += score
            category_stats[category]["citation_acc_sum"] += cit_acc
            category_stats[category]["flagged"] += int(faith_eval["is_flagged"])

            # Polite rate-limit delay
            time.sleep(0.4)

        except Exception as err:
            print(f"  -> [ERROR] Failed to evaluate {q_id}: {err}")

    # Compute overall metrics
    mean_groundedness = (
        sum(groundedness_scores) / len(groundedness_scores) if groundedness_scores else 0.0
    )
    mean_citation_acc = (
        sum(citation_accuracies) / len(citation_accuracies) if citation_accuracies else 0.0
    )

    jurisdiction_summary = {}
    for jur, s in jurisdiction_stats.items():
        cnt = s["total"]
        jurisdiction_summary[jur] = {
            "total_questions": cnt,
            "mean_groundedness": round(s["groundedness_sum"] / cnt, 4) if cnt else 0.0,
            "citation_accuracy": round(s["citation_acc_sum"] / cnt, 4) if cnt else 0.0,
            "flagged_cases_count": s["flagged"],
            "flagged_rate": round(s["flagged"] / cnt, 4) if cnt else 0.0
        }

    category_summary = {}
    for cat, s in category_stats.items():
        cnt = s["total"]
        category_summary[cat] = {
            "total_questions": cnt,
            "mean_groundedness": round(s["groundedness_sum"] / cnt, 4) if cnt else 0.0,
            "citation_accuracy": round(s["citation_acc_sum"] / cnt, 4) if cnt else 0.0,
            "flagged_cases_count": s["flagged"],
            "flagged_rate": round(s["flagged"] / cnt, 4) if cnt else 0.0
        }

    output_data = {
        "overall_metrics": {
            "total_questions_evaluated": len(results),
            "mean_groundedness_score": round(mean_groundedness, 4),
            "mean_citation_accuracy": round(mean_citation_acc, 4),
            "total_flagged_cases": len(flagged_cases),
            "flagged_rate": round(len(flagged_cases) / len(results), 4) if results else 0.0
        },
        "jurisdiction_breakdown": jurisdiction_summary,
        "category_breakdown": category_summary,
        "flagged_cases": flagged_cases,
        "results": results
    }

    # Save to JSON
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print("\n" + "=" * 80)
    print("                    GENERATION EVALUATION RESULTS")
    print("=" * 80)
    print(f"Total Evaluated Questions : {len(results)}")
    print(f"Mean Groundedness Score   : {mean_groundedness:.4f}")
    print(f"Mean Citation Accuracy    : {mean_citation_acc:.4f}")
    print(f"Total Flagged Cases       : {len(flagged_cases)} ({len(flagged_cases)/len(results)*100:.1f}%)" if results else "")
    print("-" * 80)
    print("Performance by Jurisdiction:")
    for jur, s in jurisdiction_summary.items():
        print(f"  * {jur:<12}: Groundedness={s['mean_groundedness']:.4f}, Citations={s['citation_accuracy']:.4f}, Flagged={s['flagged_cases_count']}/{s['total_questions']}")
    print("=" * 80)
    print(f"Results saved to: {out_path.relative_to(PROJECT_ROOT) if out_path.is_relative_to(PROJECT_ROOT) else out_path}\n")

    return output_data


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate RAG Generation Faithfulness")
    parser.add_argument("--sample", type=int, default=None, help="Optional sample size for quick evaluation")
    args = parser.parse_args()

    evaluate_generation(sample_size=args.sample)
