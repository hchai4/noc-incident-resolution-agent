import os
from typing import Any

from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from src.rag.hybrid import bm25_ranked_files, get_bm25, rrf_fuse
from src.rag.rerank import ABSTAIN_THRESHOLD, rerank_files

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "data/chroma_db")
COLLECTION_NAME = "noc_runbooks_index"


def get_vector_store() -> Chroma:
    """
    Initializes a read handle to the persisted ChromaDB collection.
    """
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY"),  # type: ignore[call-arg]
    )
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
        collection_metadata={"hnsw:space": "cosine"},
    )


def retrieve_sop_context(alarm_query: str, k: int = 2) -> tuple[str, list[dict[str, Any]]]:
    vector_store = get_vector_store()
    results = vector_store.similarity_search_with_relevance_scores(alarm_query, k=max(k * 4, 8))

    dense_files: list[str] = []
    parent_by_file: dict[str, str] = {}
    dense_score: dict[str, float] = {}
    chunk_by_file: dict[str, str] = {}

    for doc, score in results:
        source_file = doc.metadata.get("source_file", "unknown_sop.md")
        parent = (doc.metadata.get("parent_text") or doc.page_content).strip()
        if source_file not in parent_by_file:
            parent_by_file[source_file] = parent
            dense_score[source_file] = float(score)
            chunk_by_file[source_file] = doc.metadata.get("chunk_id", "chunk-0")
            dense_files.append(source_file)

    lexical_files = bm25_ranked_files(alarm_query, n=8)
    fused = rrf_fuse(dense_files, lexical_files)

    _, records = get_bm25()
    for row in records:
        parent_by_file.setdefault(row["source_file"], row["parent_text"])

    ranked = rerank_files(alarm_query, fused[:8], parent_by_file)
    if not ranked or ranked[0][1] < ABSTAIN_THRESHOLD:
        return "", []

    formatted_context_blocks = []
    raw_evidence = []
    for source_file, ce_score in ranked[:k]:
        parent = parent_by_file.get(source_file, "")
        raw_evidence.append(
            {
                "source_file": source_file,
                "chunk_id": chunk_by_file.get(source_file, "rerank"),
                "relevance_score": round(ce_score, 4),
                "content": parent,
            }
        )
        formatted_context_blocks.append(f"--- CITATION: [{source_file}] (CE: {ce_score:.2f}) ---\n{parent}\n")
    return "\n".join(formatted_context_blocks), raw_evidence


if __name__ == "__main__":
    test_alarm = "CRITICAL: Loss of Signal (LOS) on Metro Fiber Link LAX-ONT-01"
    context, evidence = retrieve_sop_context(test_alarm, k=2)

    print("=== RETRIEVED CONTEXT FOR AGENT PROMPT ===")
    print(context)
    print("=== EVIDENCE AUDIT TRAIL ===")
    for item in evidence:
        print(f"File: {item['source_file']} | Score: {item['relevance_score']}")
