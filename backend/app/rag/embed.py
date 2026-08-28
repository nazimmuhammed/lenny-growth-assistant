import httpx
from ..config import settings

def get_embedding(text: str) -> list[float]:
    try:
        resp = httpx.post(
            f"{settings.OLLAMA_BASE_URL}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text},
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()["embedding"]
    except httpx.ConnectError:
        raise RuntimeError("Cannot reach Ollama for embeddings. Is the ollama container running?")