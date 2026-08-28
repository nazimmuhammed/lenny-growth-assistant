from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from ..db.session import get_db
from ..db import models
import uuid

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/")
def create_session(user_meta: dict = {}, db: DBSession = Depends(get_db)):
    session = models.Session(user_meta=user_meta)
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": str(session.id), "created_at": session.created_at}

@router.get("/{session_id}/messages")
def get_messages(session_id: str, db: DBSession = Depends(get_db)):
    messages = db.query(models.Message).filter(
        models.Message.session_id == uuid.UUID(session_id)
    ).order_by(models.Message.created_at).all()
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "sources": m.sources,
            "model_used": m.model_used,
            "created_at": m.created_at,
        }
        for m in messages
    ]