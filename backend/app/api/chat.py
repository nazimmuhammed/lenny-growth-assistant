import logging
import uuid as uuid_lib
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.db.session import SessionLocal
from app.db.models import Session as ChatSession, Message
from app.rag.retriever import retrieve
from app.llm.provider import get_llm_client
from app.config import settings
from app.agent.skills.ship30 import run_ship30_skill

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    response: str
    sources: list[dict]
    model_used: str
    sufficient_context: bool


SYSTEM_PROMPT_TEMPLATE = """You are the Lenny Growth Assistant, an expert on product management and growth, grounded ONLY in the provided transcript excerpts from Lenny's Podcast.

Rules:
- Answer using ONLY the context below. Do not use outside knowledge.
- When you reference a claim, cite the episode title in parentheses, e.g. (Episode: "How to build a growth team").
- If the context is insufficient to answer well, say so explicitly and explain what's missing — do not fabricate.

CONTEXT:
{context}
"""

SHIP30_TRIGGERS = ["ship30", "ship 30", "turn this into an essay", "write an essay", "atomic essay"]


def should_route_to_ship30(message: str) -> bool:
    lowered = message.lower()
    return any(trigger in lowered for trigger in SHIP30_TRIGGERS)


def build_context(chunks: list[dict]) -> str:
    if not chunks:
        return "(no relevant transcript excerpts found)"
    parts = []
    for c in chunks:
        parts.append(f"[Episode: {c['episode_title']}]\n{c['chunk_text']}\n(source: {c['source_url']})")
    return "\n\n---\n\n".join(parts)


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        session_uuid = uuid_lib.UUID(req.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail={"error": "invalid_session_id"})

    db = SessionLocal()
    try:
        session = db.get(ChatSession, session_uuid)
        if not session:
            raise HTTPException(status_code=404, detail={"error": "session_not_found"})

        history = (
            db.execute(
                select(Message)
                .where(Message.session_id == session_uuid)
                .order_by(Message.created_at)
            )
            .scalars()
            .all()
        )

        try:
            chunks, sufficient = retrieve(req.message, top_k=5, similarity_threshold=0.3)
        except Exception as e:
            logger.exception("retrieval failed")
            raise HTTPException(status_code=502, detail={"error": "retrieval_failed", "message": str(e)})

        if should_route_to_ship30(req.message):
            try:
                result = run_ship30_skill(req.message)
            except Exception as e:
                logger.exception("ship30 skill failed")
                raise HTTPException(status_code=502, detail={"error": "ship30_failed", "message": str(e)})

            db.add(Message(session_id=session_uuid, role="user", content=req.message))
            db.add(
                Message(
                    session_id=session_uuid,
                    role="assistant",
                    content=result["essay"],
                    sources=result["sources"],
                    model_used=result["model_used"],
                )
            )
            db.commit()

            return ChatResponse(
                response=result["essay"],
                sources=result["sources"],
                model_used=result["model_used"],
                sufficient_context=result["sufficient_context"],
            )

        context = build_context(chunks)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

        messages = [{"role": m.role, "content": m.content} for m in history]
        messages.append({"role": "user", "content": req.message})

        try:
            client = get_llm_client()
            answer = client.generate(messages=messages, system=system_prompt, max_tokens=1024)
        except Exception as e:
            logger.exception("llm generation failed")
            raise HTTPException(
                status_code=502,
                detail={"error": "llm_generation_failed", "provider": settings.LLM_PROVIDER, "message": str(e)},
            )

        sources = [{"episode_title": c["episode_title"], "source_url": c["source_url"]} for c in chunks]

        db.add(Message(session_id=session_uuid, role="user", content=req.message))
        db.add(
            Message(
                session_id=session_uuid,
                role="assistant",
                content=answer,
                sources=sources,
                model_used=settings.LLM_PROVIDER,
            )
        )
        db.commit()

        return ChatResponse(
            response=answer,
            sources=sources,
            model_used=settings.LLM_PROVIDER,
            sufficient_context=sufficient,
        )
    finally:
        db.close()