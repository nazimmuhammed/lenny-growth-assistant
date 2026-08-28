import httpx
from ..config import settings

class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    def generate(self, messages: list, system: str = "", max_tokens: int = 1000) -> str:
        prompt_messages = []
        if system:
            prompt_messages.append({"role": "system", "content": system})
        prompt_messages.extend(messages)

        try:
            resp = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": prompt_messages,
                    "stream": False,
                },
                timeout=300.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot reach Ollama at {self.base_url}. Is the ollama container running?"
            )
        except httpx.TimeoutException:
            raise RuntimeError("Ollama request timed out. The model may be too slow or not pulled yet.")