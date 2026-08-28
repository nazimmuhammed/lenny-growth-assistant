from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid, datetime
from .session import Base

class Session(Base):
    __tablename__ = "sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_meta = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    messages = relationship("Message", back_populates="session")

class Message(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    role = Column(String)          # user | assistant
    content = Column(Text)
    sources = Column(JSON, default=[])
    model_used = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    session = relationship("Session", back_populates="messages")

class Artifact(Base):
    __tablename__ = "artifacts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"))
    type = Column(String)          # markdown | html
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)