from collections import defaultdict

from rank_bm25 import BM25Okapi

from src.rag.indexer import (
    RUNBOOKS_DIR,
    build_alarm_aliases,
    load_runbook_documents,
    split_sop_into_sections,
)

RRF_K = 60


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def load_bm25_corpus() -> tuple[BM25Okapi, list[dict]]:
    """One BM25 document per section (and per alias), same grain as Chroma."""
    records = []
    for doc in load_runbook_documents(RUNBOOKS_DIR):
        source_file = doc.metadata["source_file"]
        full_text = doc.page_content.strip()
        for chunk in split_sop_into_sections(source_file, full_text):
            records.append(
                {
                    "source_file": source_file,
                    "text": chunk["text"],
                    "parent_text": full_text,
                }
            )
        for alias in build_alarm_aliases(full_text):
            records.append(
                {
                    "source_file": source_file,
                    "text": alias,
                    "parent_text": full_text,
                }
            )
    bm25 = BM25Okapi([_tokenize(row["text"]) for row in records])
    return bm25, records


_BM25 = None
_RECORDS = None


def get_bm25() -> tuple[BM25Okapi, list[dict]]:
    global _BM25, _RECORDS
    if _BM25 is None:
        _BM25, _RECORDS = load_bm25_corpus()
    return _BM25, _RECORDS


def bm25_ranked_files(query: str, n: int = 8) -> list[str]:
    bm25, records = get_bm25()
    scores = bm25.get_scores(_tokenize(query))
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    files = []
    for i in order:
        name = records[i]["source_file"]
        if name not in files:
            files.append(name)
        if len(files) >= n:
            break
    return files


def rrf_fuse(dense_files: list[str], lexical_files: list[str]) -> list[str]:
    """RRF: score += 1 / (60 + rank). Higher is better."""
    scores: dict[str, float] = defaultdict(float)
    for rank, name in enumerate(dense_files, start=1):
        scores[name] += 1.0 / (RRF_K + rank)
    for rank, name in enumerate(lexical_files, start=1):
        scores[name] += 1.0 / (RRF_K + rank)
    return sorted(scores, key=lambda name: scores[name], reverse=True)
