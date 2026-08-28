import logging
import uuid as uuid_lib
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.db.session import SessionLocal
from app.db.models import Session as ChatSession, Message, Artifact
from app.llm.provider import get_llm_client
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class ArtifactRequest(BaseModel):
    session_id: str
    artifact_type: str  # "markdown" | "html"
    instructions: str


class ArtifactResponse(BaseModel):
    artifact_id: str
    type: str
    content: str


ARTIFACT_SYSTEM_PROMPT = """You generate a standalone {artifact_type} artifact based on the conversation so far and the user's instructions.

Rules:
- Output ONLY the {artifact_type} content itself. No commentary, no explanation, no markdown code fences around it.
- Ground any factual claims in the conversation context provided. Do not fabricate.
- If artifact_type is "html": produce a single self-contained HTML snippet (inline CSS only, no external scripts, no <script> tags unless explicitly requested — this content will be sandboxed and treated as untrusted).
- If artifact_type is "markdown": produce clean, well-structured Markdown.

CONVERSATION CONTEXT:
{conversation}
"""


@router.post("/artifacts", response_model=ArtifactResponse)
def create_artifact(req: ArtifactRequest):
    if req.artifact_type not in ("markdown", "html"):
        raise HTTPException(status_code=400, detail={"error": "invalid_artifact_type"})

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
        conversation = "\n\n".join(f"{m.role.upper()}: {m.content}" for m in history)

        system_prompt = ARTIFACT_SYSTEM_PROMPT.format(
            artifact_type=req.artifact_type, conversation=conversation or "(no prior conversation)"
        )

        try:
            client = get_llm_client()
            content = client.generate(
                messages=[{"role": "user", "content": req.instructions}],
                system=system_prompt,
                max_tokens=3000,
            )
        except Exception as e:
            logger.exception("artifact generation failed")
            raise HTTPException(
                status_code=502,
                detail={"error": "artifact_generation_failed", "provider": settings.LLM_PROVIDER, "message": str(e)},
            )

        artifact = Artifact(session_id=session_uuid, type=req.artifact_type, content=content)
        db.add(artifact)
        db.commit()
        db.refresh(artifact)

        return ArtifactResponse(artifact_id=str(artifact.id), type=artifact.type, content=artifact.content)
    finally:
        db.close()