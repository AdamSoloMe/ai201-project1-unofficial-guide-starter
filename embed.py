"""
Reads all .txt files from documents/, chunks them, embeds with
all-MiniLM-L6-v2, and stores in a local ChromaDB collection.

Run after ingest.py:
    python embed.py
"""

import os
import re
import chromadb
from sentence_transformers import SentenceTransformer

DOCUMENTS_DIR = "documents"
CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "berserk"
CHUNK_SIZE = 400      # characters — sized for 1–3 short reviews per chunk
CHUNK_OVERLAP = 50    # characters


def load_documents() -> list[dict]:
    docs = []
    for fname in sorted(os.listdir(DOCUMENTS_DIR)):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(DOCUMENTS_DIR, fname)
        with open(path, encoding="utf-8") as f:
            raw = f.read()

        # Parse the header written by ingest.py
        source = fname.replace(".txt", "")
        url = ""
        lines = raw.splitlines()
        body_start = 0
        for i, line in enumerate(lines):
            if line.startswith("Source:"):
                source = line.removeprefix("Source:").strip()
            elif line.startswith("URL:"):
                url = line.removeprefix("URL:").strip()
            elif line.strip() == "" and i >= 2:
                body_start = i + 1
                break

        body = "\n\n".join(lines[body_start:])
        docs.append({"source": source, "url": url, "text": body})
        print(f"  loaded {source} ({len(body):,} chars)")

    return docs


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Splits text into overlapping chunks that respect paragraph boundaries
    where possible, falling back to character-level splitting.
    """
    paragraphs = re.split(r"\n\n+", text)
    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If this paragraph alone exceeds chunk_size, hard-split it
        if len(para) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = current[-overlap:] if overlap else ""
            for i in range(0, len(para), chunk_size - overlap):
                piece = para[i : i + chunk_size]
                if piece.strip():
                    chunks.append(piece.strip())
            current = para[-(overlap):] if overlap else ""
            continue

        # Would adding this paragraph overflow the current chunk?
        candidate = (current + "\n\n" + para).strip()
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current.strip():
                chunks.append(current.strip())
            # Carry the overlap from the end of the previous chunk
            current = (current[-overlap:] + "\n\n" + para).strip() if overlap else para

    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if len(c) > 30]


def main():
    docs = load_documents()
    if not docs:
        print("No documents found. Run ingest.py first.")
        return

    model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"\nLoaded embedding model: all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Drop and recreate so re-running embed.py is idempotent
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    all_chunks = []
    all_ids = []
    all_metadatas = []

    for doc in docs:
        chunks = chunk_text(doc["text"], CHUNK_SIZE, CHUNK_OVERLAP)
        print(f"  {doc['source']}: {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{doc['source']}_{i}")
            all_metadatas.append({
                "source": doc["source"],
                "url": doc["url"],
                "chunk_index": i,
            })

    print(f"\nTotal chunks: {len(all_chunks)}")
    print("Embedding…")

    embeddings = model.encode(all_chunks, show_progress_bar=True).tolist()

    # Upsert in batches of 500 (ChromaDB limit)
    batch = 500
    for start in range(0, len(all_chunks), batch):
        end = start + batch
        collection.add(
            ids=all_ids[start:end],
            documents=all_chunks[start:end],
            embeddings=embeddings[start:end],
            metadatas=all_metadatas[start:end],
        )

    print(f"Stored {len(all_chunks)} chunks in ChromaDB at ./{CHROMA_DIR}/")
    print("\nSample chunks:")
    for chunk in all_chunks[:3]:
        print(f"  [{len(chunk)} chars] {chunk[:120]}…")


if __name__ == "__main__":
    main()
