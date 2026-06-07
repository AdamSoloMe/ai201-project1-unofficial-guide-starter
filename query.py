"""
Retrieval + grounded generation.

ask(question) returns {"answer": str, "sources": list[str], "chunks": list[dict]}
"""

import os
import chromadb
from groq import Groq
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

CHROMA_DIR = "chroma_db"
COLLECTION_NAME = "qc_professors"
TOP_K = 5
MODEL_NAME = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """\
You are a helpful assistant for students at CUNY Queens College looking for honest,
student-sourced information about Computer Science professors. Answer the user's
question using ONLY the information provided in the retrieved Rate My Professors
reviews below. Do not use any outside knowledge.

If the excerpts do not contain enough information to answer the question,
respond with: "I don't have enough information in my documents to answer that."

Always cite which professor's page(s) your answer draws from at the end of your
response, like this: [Source: ProfessorName]
"""

_model: SentenceTransformer | None = None
_collection: chromadb.Collection | None = None
_groq_client: Groq | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_collection() -> chromadb.Collection:
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


def _get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key or api_key == "your_key_here":
            raise ValueError(
                "GROQ_API_KEY is not set. Add your key to .env and restart."
            )
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    model = _get_model()
    collection = _get_collection()

    embedding = model.encode([question])[0].tolist()
    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "source": meta["source"],
            "url": meta.get("url", ""),
            "distance": round(dist, 4),
        })
    return chunks


def ask(question: str) -> dict:
    chunks = retrieve(question)

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Excerpt {i} — Source: {chunk['source']}]\n{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    user_message = f"Retrieved excerpts:\n\n{context}\n\nQuestion: {question}"

    groq = _get_groq()
    response = groq.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content.strip()
    sources = list(dict.fromkeys(c["source"] for c in chunks))  # deduplicated, ordered

    return {"answer": answer, "sources": sources, "chunks": chunks}


if __name__ == "__main__":
    # Quick retrieval test — run before wiring up the UI
    test_questions = [
        "Which CS professor at Queens College is the most highly rated?",
        "What do students say about Alex Ryba?",
        "Is Jerry Waxman a good professor?",
    ]
    for q in test_questions:
        print(f"\nQ: {q}")
        chunks = retrieve(q)
        print(f"Top result [{chunks[0]['distance']}]: {chunks[0]['text'][:200]}…")
        print(f"Source: {chunks[0]['source']}")
