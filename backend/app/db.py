"""
SQLAlchemy schema and engine for persistent storage (Postgres + pgvector).
Kept separate from app/models.py, which holds pure Pydantic API request/
response shapes.
"""
from sqlalchemy import (
    create_engine, text, Column, String, Text, Boolean, Integer, DateTime, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector
from datetime import datetime
import uuid
from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=5)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class SessionRecord(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TranscriptChunkRow(Base):
    __tablename__ = "transcript_chunks"
    # No vector index (HNSW/IVFFlat both cap at 2000 dims in pgvector; Gemini's
    # embeddings are 3072-dim). Not needed at this app's scale anyway - every
    # query already filters to one session's chunks first (via the session_id
    # index below), and a single meeting's chunk count is always small enough
    # for a plain sequential cosine-distance scan over that filtered subset.
    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(String, nullable=False)
    speaker = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(settings.gemini_embed_dim), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class NoteRow(Base):
    __tablename__ = "notes"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    date = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TodoRow(Base):
    __tablename__ = "todos"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, nullable=False, default="medium")
    due_date = Column(String, nullable=True)
    evidence = Column(JSONB, nullable=False, default=list)
    completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CalendarEventRow(Base):
    __tablename__ = "calendar_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    date = Column(String, nullable=True)
    time = Column(String, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    evidence = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ActionRow(Base):
    __tablename__ = "actions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(JSONB, nullable=False, default=list)
    action_metadata = Column("metadata", JSONB, nullable=False, default=dict)
    approved = Column(Boolean, nullable=False, default=False)
    executed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def init_db():
    """Enable pgvector and create all tables. Idempotent - safe to call on every startup."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(engine)
