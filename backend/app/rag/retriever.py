from sqlalchemy import text as sql_text
from ..db.session import SessionLocal
from .embed import get_embedding

def retrieve(query: str, top_k: int = 5, similarity_threshold: float = 0.3):
    embedding = get_embedding(query)
    db = SessionLocal()
    try:
        results = db.execute(
            sql_text("""
                SELECT episode_title, source_url, chunk_text,
                       1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM chunks
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
            """),
            {"embedding": str(embedding), "top_k": top_k},
        ).fetchall()
    finally:
        db.close()

    chunks = [
        {"episode_title": r.episode_title, "source_url": r.source_url,
         "chunk_text": r.chunk_text, "similarity": r.similarity}
        for r in results
    ]
    sufficient = any(c["similarity"] >= similarity_threshold for c in chunks)
    return chunks, sufficient