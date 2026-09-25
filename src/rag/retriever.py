import os
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "data/chroma_db")
COLLECTION_NAME = "noc_runbooks_index"


def get_vector_store() -> Chroma:
    """
    Initializes a read handle to the persisted ChromaDB collection.
    """
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
        collection_metadata={"hnsw:space": "cosine"},
    )


def retrieve_sop_context(alarm_query: str, k: int = 2) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Queries ChromaDB with similarity relevance scoring.
    Returns:
      - formatted_context: Clean string formatted for LLM system prompts with citations.
      - raw_evidence: List of dictionaries with metadata, score, and chunk content.
    """
    vector_store = get_vector_store()

    # Retrieve docs with similarity relevance score (0.0 to 1.0, where 1.0 is exact match)
    results = vector_store.similarity_search_with_relevance_scores(alarm_query, k=k)

    formatted_context_blocks = []
    raw_evidence = []

    for doc, score in results:
        source_file = doc.metadata.get("source_file", "unknown_sop.md")
        chunk_id = doc.metadata.get("chunk_id", "chunk-0")
        clean_content = doc.page_content.strip()

        evidence_entry = {
            "source_file": source_file,
            "chunk_id": chunk_id,
            "relevance_score": round(float(score), 4),
            "content": clean_content
        }
        raw_evidence.append(evidence_entry)

        # Markdown block for LLM prompt context injection
        formatted_context_blocks.append(
            f"--- CITATION: [{source_file}] (Confidence: {score:.2f}) ---\n"
            f"{clean_content}\n"
        )

    formatted_context = "\n".join(formatted_context_blocks)
    return formatted_context, raw_evidence


if __name__ == "__main__":
    test_alarm = "CRITICAL: Loss of Signal (LOS) on Metro Fiber Link LAX-ONT-01"
    context, evidence = retrieve_sop_context(test_alarm, k=2)

    print("=== RETRIEVED CONTEXT FOR AGENT PROMPT ===")
    print(context)
    print("=== EVIDENCE AUDIT TRAIL ===")
    for item in evidence:
        print(f"File: {item['source_file']} | Score: {item['relevance_score']}")