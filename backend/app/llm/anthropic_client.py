import anthropic
from ..config import settings

class AnthropicClient:
    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate(self, messages: list, system: str = "", max_tokens: int = 1000) -> str:
        try:
            resp = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            return resp.content[0].text
        except anthropic.APIError as e:
            raise RuntimeError(f"Anthropic API error: {e}")