import os

from sentence_transformers import CrossEncoder

MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
# Default -9 keeps rerank-only eval. Set RETRIEVAL_ABSTAIN_THRESHOLD=0.5 to refuse weak hits.
ABSTAIN_THRESHOLD = float(os.getenv("RETRIEVAL_ABSTAIN_THRESHOLD", "-9.0"))

_MODEL = None


def get_cross_encoder() -> CrossEncoder:
    global _MODEL
    if _MODEL is None:
        _MODEL = CrossEncoder(MODEL_NAME)
    return _MODEL


def rerank_files(
    query: str,
    files: list[str],
    parent_by_file: dict[str, str],
) -> list[tuple[str, float]]:
    """Score (query, parent SOP) pairs. Higher is more relevant (MS MARCO logit)."""
    pairs: list[tuple[str, str]] = []
    kept = []
    for name in files:
        parent = parent_by_file.get(name, "").strip()
        if not parent:
            continue
        kept.append(name)
        pairs.append((query, parent[:2000]))
    if not pairs:
        return []
    scores = get_cross_encoder().predict(pairs)
    ranked = sorted(zip(kept, scores, strict=False), key=lambda row: float(row[1]), reverse=True)
    return [(name, float(score)) for name, score in ranked]
