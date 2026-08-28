from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    LLM_PROVIDER: str = "ollama"
    ANTHROPIC_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100

    class Config:
        env_file = ".env"

settings = Settings()