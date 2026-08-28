import os, glob, re
from sqlalchemy import text as sql_text
from ..db.session import SessionLocal
from ..config import settings
from .embed import get_embedding

def strip_frontmatter(content: str) -> str:
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content

def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += max(chunk_size - overlap, 1)
    return chunks

def ingest_transcripts(transcript_dir: str = "data/transcripts/selected"):
    db = SessionLocal()
    db.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector"))
    db.execute(sql_text("""
        CREATE TABLE IF NOT EXISTS chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            episode_title TEXT,
            source_url TEXT,
            chunk_text TEXT,
            embedding vector(768)
        )
    """))
    db.commit()

    files = glob.glob(os.path.join(transcript_dir, "*.md"))
    print(f"Found {len(files)} transcript files")

    for filepath in files:
        episode_title = os.path.basename(filepath).replace(".md", "")
        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read()

        content = strip_frontmatter(raw)
        chunks = chunk_text(content, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        print(f"  {episode_title}: {len(chunks)} chunks")

        for chunk in chunks:
            if not chunk.strip():
                continue
            embedding = get_embedding(chunk)
            db.execute(
                sql_text("""
                    INSERT INTO chunks (episode_title, source_url, chunk_text, embedding)
                    VALUES (:title, :url, :chunk, :embedding)
                """),
                {
                    "title": episode_title,
                    "url": f"https://github.com/ChatPRD/lennys-podcast-transcripts/tree/main/episodes/{episode_title}",
                    "chunk": chunk,
                    "embedding": str(embedding),
                },
            )
        db.commit()

    db.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest_transcripts()