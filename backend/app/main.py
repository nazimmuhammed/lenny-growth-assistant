from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.session import engine
from .db import models
from .api import sessions, chat, artifacts
from .config import settings

app = FastAPI(title="Lenny Growth Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(artifacts.router)


@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/config")
def config():
    return {"llm_provider": settings.LLM_PROVIDER, "model": settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama" else "claude-sonnet-4-6"}