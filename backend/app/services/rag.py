"""Lightweight RAG retrieval using TF-IDF cosine similarity — no external
embedding API needed, works fully offline once dependencies are installed.
Swap for a real vector DB (pgvector, Pinecone, Chroma) if you need semantic
retrieval at scale."""
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def retrieve_relevant_chunks(query: str, chunks: List[Dict], top_k: int = 5) -> List[Dict]:
    """chunks: list of {id, text, page}. Returns top_k most relevant chunks."""
    if not chunks:
        return []
    texts = [c["text"] for c in chunks]
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        matrix = vectorizer.fit_transform(texts + [query])
    except ValueError:
        # e.g. empty vocabulary
        return chunks[:top_k]

    query_vec = matrix[-1]
    doc_vecs = matrix[:-1]
    sims = cosine_similarity(query_vec, doc_vecs).flatten()

    ranked = sorted(zip(chunks, sims), key=lambda x: x[1], reverse=True)
    return [c for c, score in ranked[:top_k] if score > 0] or chunks[:top_k]


def build_context(chunks: List[Dict], max_chars: int = 6000) -> str:
    """Concatenates retrieved chunks into a single context block for the LLM prompt."""
    out = []
    total = 0
    for c in chunks:
        piece = f"[Page {c.get('page', '?')}] {c['text']}"
        if total + len(piece) > max_chars:
            break
        out.append(piece)
        total += len(piece)
    return "\n\n".join(out)
