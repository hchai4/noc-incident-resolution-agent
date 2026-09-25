import os
import re
import glob
import shutil
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

RUNBOOKS_DIR = os.getenv("RUNBOOKS_DIR", "data/noc_runbooks")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "data/chroma_db")
COLLECTION_NAME = "noc_runbooks_index"


def load_runbook_documents(directory_path: str):
    """
    Loads all markdown SOP files from the target directory
    and tags each document with explicit source metadata.
    """
    md_files = glob.glob(os.path.join(directory_path, "*.md"))
    if not md_files:
        raise FileNotFoundError(f"No .md runbook files found in {directory_path}")

    documents = []
    for file_path in sorted(md_files):
        loader = TextLoader(file_path, encoding="utf-8")
        docs = loader.load()
        for doc in docs:
            doc.metadata["source_file"] = Path(file_path).name
        documents.extend(docs)

    return documents


def build_alarm_aliases(sop_text: str) -> list[str]:
    """
    Build short, alarm-shaped retrieval keys from SOP title, symptoms, and
    first technical action. Operator tickets are much closer to these strings
    than to a full policy document, which raises cosine similarity.
    """
    title = sop_text.splitlines()[0].strip() if sop_text.strip() else ""
    topic = title.split(":", 1)[-1]
    topic = re.sub(
        r"\b(Incident Protocol|Mitigation Protocol|& Facility Transfer|Protocol)\b",
        "",
        topic,
    ).strip(" :") or title

    symptoms = ""
    actions = ""
    if "1. Scope & Symptoms" in sop_text:
        symptoms = sop_text.split("1. Scope & Symptoms", 1)[-1].split("2. ", 1)[0]
    if "3. Immediate Technical Actions" in sop_text:
        actions = sop_text.split("3. Immediate Technical Actions", 1)[-1].split("4. ", 1)[0]

    symptoms = re.sub(
        r"This standard operating procedure applies to\s*",
        "",
        symptoms,
        flags=re.I,
    )
    symptoms = re.sub(r"^Applies to\s*", "", symptoms.strip(), flags=re.I)
    symptoms = " ".join(symptoms.split())
    clauses = [c.strip() for c in re.split(r",| or ", symptoms) if c.strip()]
    first = clauses[0] if clauses else topic
    second = " ".join(clauses[1].split()[:6]) if len(clauses) > 1 else ""

    first_act = re.split(r"\n\n", actions.strip())[0].strip() if actions.strip() else ""
    loc_match = re.search(
        r"\bon\s+([A-Za-z0-9][A-Za-z0-9\- ]{2,40}?)(?:\s*\(|\.|$)",
        first_act,
        flags=re.I,
    )
    loc = f"on {loc_match.group(1).strip()}" if loc_match else ""

    aliases = [
        f"CRITICAL: {first} on {topic}",
        f"ALARM: {first} on {topic}",
        f"CRITICAL: {topic}",
        f"ALARM: {topic}",
    ]
    if loc:
        aliases.append(f"CRITICAL: {first} {loc}")
        if second:
            aliases.append(f"ALARM: {first}, {second} {loc}")

    unique = []
    seen = set()
    for alias in aliases:
        alias = " ".join(alias.split())
        if alias and alias not in seen:
            seen.add(alias)
            unique.append(alias)
    return unique


def build_vector_index(force_rebuild: bool = True):
    """
    Parses, embeds, and saves SOP runbooks into ChromaDB.

    Each SOP is stored as full document text, but additional vectors are
    computed from alarm-style aliases so live NOC tickets match at high cosine.
    """
    print(f"Loading SOP documents from: {RUNBOOKS_DIR}")
    raw_docs = load_runbook_documents(RUNBOOKS_DIR)
    print(f"Loaded {len(raw_docs)} SOP documents.")

    if force_rebuild and os.path.exists(CHROMA_PERSIST_DIR):
        shutil.rmtree(CHROMA_PERSIST_DIR)

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
        collection_metadata={"hnsw:space": "cosine"}
    )

    embed_inputs = []
    stored_docs = []
    metadatas = []
    ids = []
    idx = 0

    for doc in raw_docs:
        source_file = doc.metadata["source_file"]
        full_text = doc.page_content.strip()
        variants = build_alarm_aliases(full_text) + [full_text]
        for variant in variants:
            embed_inputs.append(variant)
            stored_docs.append(full_text)
            metadatas.append({
                "source_file": source_file,
                "chunk_id": f"{source_file}#chunk-{idx}",
            })
            ids.append(f"{source_file}-{idx}")
            idx += 1

    vectors = embeddings.embed_documents(embed_inputs)
    vector_store._collection.add(
        ids=ids,
        embeddings=vectors,
        documents=stored_docs,
        metadatas=metadatas,
    )

    print(f"Successfully indexed {len(stored_docs)} vectors into Chroma collection '{COLLECTION_NAME}'.")
    print(f"Index persisted at: {CHROMA_PERSIST_DIR}")
    return vector_store


if __name__ == "__main__":
    build_vector_index()
