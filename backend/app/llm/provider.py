from .anthropic_client import AnthropicClient
from .ollama_client import OllamaClient
from ..config import settings

def get_llm_client():
    if settings.LLM_PROVIDER == "anthropic":
        return AnthropicClient()
    return OllamaClient()