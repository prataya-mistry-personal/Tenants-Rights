"""Document chunking module for statutes and judgments.

Splits processed legal texts into semantically coherent, sentence-bounded chunks
(~300-400 tokens / ~350 words, with ~15% overlap) and persists to data/chunks/chunks.jsonl.
"""

import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import load_config


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences while respecting abbreviations, section numbers, initials, and citations."""
    # Normalize internal whitespace
    clean_text = re.sub(r'[ \t]+', ' ', text).strip()
    if not clean_text:
        return []

    protected = clean_text

    # Protect capital initials like A.P., B.R., P.J., V.R., etc.
    protected = re.sub(r'\b([A-Z]\.)+', lambda m: m.group(0).replace('.', '_DOT_'), protected)

    # Protect common legal abbreviations from premature splitting
    abbreviations = [
        ("Sec.", "Sec_DOT_"),
        ("sec.", "sec_DOT_"),
        ("v.", "v_DOT_"),
        ("vs.", "vs_DOT_"),
        ("Ors.", "Ors_DOT_"),
        ("Anr.", "Anr_DOT_"),
        ("Ltd.", "Ltd_DOT_"),
        ("Pvt.", "Pvt_DOT_"),
        ("Co.", "Co_DOT_"),
        ("No.", "No_DOT_"),
        ("Nos.", "Nos_DOT_"),
        ("Hon'ble", "Honble_DOT_"),
        ("Dr.", "Dr_DOT_"),
        ("Mr.", "Mr_DOT_"),
        ("Mrs.", "Mrs_DOT_"),
        ("Smt.", "Smt_DOT_"),
        ("Sri.", "Sri_DOT_"),
        ("Shri.", "Shri_DOT_"),
        ("i.e.", "ie_DOT_"),
        ("e.g.", "eg_DOT_"),
        ("viz.", "viz_DOT_"),
        ("Art.", "Art_DOT_"),
        ("cl.", "cl_DOT_"),
        ("sub-sec.", "subsec_DOT_"),
    ]
    for abbr, token in abbreviations:
        protected = protected.replace(abbr, token)

    # Split on sentence terminals: period, exclamation, or question mark followed by whitespace
    raw_sentences = re.split(r'(?<=[.!?])\s+', protected)

    # Restore abbreviations and dots
    sentences = []
    for s in raw_sentences:
        s_restored = s.strip()
        for abbr, token in abbreviations:
            s_restored = s_restored.replace(token, abbr)
        s_restored = s_restored.replace('_DOT_', '.')
        if s_restored:
            sentences.append(s_restored)

    return sentences


def chunk_text(
    text: str,
    target_words: int = 320,
    overlap_words: int = 48
) -> List[str]:
    """Chunk text into sentence-bounded blocks of approx target_words with overlap."""
    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]
    if not paragraphs:
        return []

    all_sentences: List[str] = []
    for para in paragraphs:
        para_sents = split_into_sentences(para)
        if para_sents:
            all_sentences.extend(para_sents)
        else:
            all_sentences.append(para)

    chunks: List[str] = []
    current_sentences: List[str] = []
    current_word_count = 0

    for sent in all_sentences:
        sent_words = len(sent.split())
        if current_word_count + sent_words > target_words and current_sentences:
            # Yield current chunk
            chunk_str = " ".join(current_sentences).strip()
            if chunk_str:
                chunks.append(chunk_str)

            # Build overlap from trailing sentences
            overlap_sentences: List[str] = []
            overlap_count = 0
            for prev_sent in reversed(current_sentences):
                p_words = len(prev_sent.split())
                if overlap_count + p_words <= overlap_words:
                    overlap_sentences.insert(0, prev_sent)
                    overlap_count += p_words
                else:
                    break

            current_sentences = overlap_sentences.copy()
            current_word_count = sum(len(s.split()) for s in current_sentences)

        current_sentences.append(sent)
        current_word_count += sent_words

    # Append any remaining sentences as the final chunk
    if current_sentences:
        chunk_str = " ".join(current_sentences).strip()
        if chunk_str:
            chunks.append(chunk_str)

    return chunks


def load_statute_documents(statutes_dir: Path) -> List[Dict[str, Any]]:
    """Load processed statute plain text files with jurisdiction mapping."""
    statute_docs = []
    jurisdiction_map = {
        "karnataka_rent_act_1999": "Bengaluru",
        "model_tenancy_act_2021": "Other",
        "transfer_of_property_act_1882_leases": "Other",
    }

    for txt_file in statutes_dir.glob("*.txt"):
        with open(txt_file, "r", encoding="utf-8") as f:
            content = f.read().strip()

        doc_id = txt_file.stem
        # Extract title from first line if available
        first_line = content.splitlines()[0] if content else doc_id
        jurisdiction = jurisdiction_map.get(doc_id, "Other")

        statute_docs.append({
            "doc_id": doc_id,
            "filename": txt_file.name,
            "title": first_line,
            "source_type": "statute",
            "jurisdiction": jurisdiction,
            "text": content
        })

    return statute_docs


def load_judgment_documents(judgments_dir: Path) -> List[Dict[str, Any]]:
    """Load processed judgment files and extract metadata."""
    meta_file = judgments_dir / "cleaned_metadata.jsonl"
    meta_lookup: Dict[str, Dict[str, Any]] = {}
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    meta_lookup[item.get("filename", "")] = item
                    meta_lookup[item.get("doc_id", "")] = item

    judgment_docs = []
    for txt_file in judgments_dir.glob("*.txt"):
        if txt_file.name == "cleaned_metadata.jsonl":
            continue

        with open(txt_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()

        doc_id = txt_file.stem
        meta = meta_lookup.get(txt_file.name) or meta_lookup.get(doc_id) or {}

        title = meta.get("title", doc_id)
        jurisdiction = meta.get("jurisdiction", "Other")
        category = meta.get("category", "general")
        url = meta.get("url", "")

        # Separate header if present in body
        body = content
        if "============================================================" in content:
            parts = content.split("============================================================", 1)
            body = parts[1].strip() if len(parts) > 1 else content

        judgment_docs.append({
            "doc_id": doc_id,
            "filename": txt_file.name,
            "title": title,
            "source_type": "judgment",
            "jurisdiction": jurisdiction,
            "category": category,
            "url": url,
            "text": body
        })

    return judgment_docs


def build_all_chunks(
    processed_dir: Optional[Path] = None,
    output_file: Optional[Path] = None,
    target_words: int = 320,
    overlap_words: int = 48
) -> List[Dict[str, Any]]:
    """Process all statutes and judgments into sentence-bounded chunks."""
    cfg = load_config()
    proc_dir = processed_dir or Path(cfg.paths.processed_data_dir)
    out_path = output_file or Path(cfg.paths.chunks_dir) / "chunks.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    statutes_dir = proc_dir / "statutes"
    judgments_dir = proc_dir / "judgments"

    all_docs: List[Dict[str, Any]] = []
    if statutes_dir.exists():
        all_docs.extend(load_statute_documents(statutes_dir))
    if judgments_dir.exists():
        all_docs.extend(load_judgment_documents(judgments_dir))

    if not all_docs:
        raise FileNotFoundError(f"No processed documents found in {proc_dir}")

    all_chunks: List[Dict[str, Any]] = []
    doc_chunk_counts: Dict[str, int] = {}

    for doc in all_docs:
        doc_id = doc["doc_id"]
        text_content = doc["text"]
        raw_chunks = chunk_text(text_content, target_words=target_words, overlap_words=overlap_words)

        doc_chunk_counts[doc_id] = len(raw_chunks)

        for idx, chunk_str in enumerate(raw_chunks, start=1):
            chunk_id = f"{doc['source_type']}_{doc_id}_{idx:03d}"
            record = {
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "title": doc.get("title", doc_id),
                "source_type": doc["source_type"],
                "jurisdiction": doc.get("jurisdiction", "Other"),
                "category": doc.get("category", "statutory" if doc["source_type"] == "statute" else "general"),
                "url": doc.get("url", ""),
                "chunk_index": idx,
                "total_chunks_in_doc": len(raw_chunks),
                "word_count": len(chunk_str.split()),
                "char_count": len(chunk_str),
                "text": chunk_str
            }
            all_chunks.append(record)

    # Persist chunks to chunks.jsonl
    with open(out_path, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    # Step 3.2: Validation and Summary Statistics
    total_chunks = len(all_chunks)
    avg_words = sum(c["word_count"] for c in all_chunks) / total_chunks if total_chunks else 0
    avg_chars = sum(c["char_count"] for c in all_chunks) / total_chunks if total_chunks else 0
    empty_chunks = [c for c in all_chunks if not c["text"].strip()]
    zero_chunk_docs = [doc_id for doc_id, count in doc_chunk_counts.items() if count == 0]

    print("\n" + "=" * 60)
    print("           CHUNK VALIDATION SUMMARY (Phase 3)")
    print("=" * 60)
    print(f"Total Source Documents : {len(all_docs)} (Statutes + Judgments)")
    print(f"Total Chunks Generated : {total_chunks}")
    print(f"Average Words / Chunk  : {avg_words:.1f} words (~{avg_words*1.33:.0f} tokens)")
    print(f"Average Chars / Chunk  : {avg_chars:.1f} characters")
    print(f"Empty Chunks           : {len(empty_chunks)}")
    print(f"Docs with 0 Chunks     : {len(zero_chunk_docs)}")
    print(f"Persisted to File      : {out_path}")
    print("=" * 60)

    if empty_chunks:
        raise ValueError(f"Found {len(empty_chunks)} empty chunks!")
    if zero_chunk_docs:
        raise ValueError(f"Found documents with 0 chunks: {zero_chunk_docs}")

    return all_chunks


if __name__ == "__main__":
    chunks = build_all_chunks()
    print(f"\nChunking complete: {len(chunks)} chunks verified and ready.")
