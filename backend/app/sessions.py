"""
Session registration and listing, for the session history view.
"""
from typing import List
from sqlalchemy import select
from app.db import SessionLocal, SessionRecord
from app.models import Session
import logging

logger = logging.getLogger(__name__)


def _to_model(row: SessionRecord) -> Session:
    return Session(
        id=row.id,
        display_name=row.display_name,
        mode=row.mode,
        created_at=row.created_at,
    )


def register_session(id: str, display_name: str, mode: str) -> Session:
    """Register a new session, or no-op if it already exists (e.g. a tab reload mid-capture)."""
    with SessionLocal() as db:
        existing = db.get(SessionRecord, id)
        if existing:
            logger.info(f"Session {id} already registered, skipping")
            return _to_model(existing)

        row = SessionRecord(id=id, display_name=display_name, mode=mode)
        db.add(row)
        db.commit()
        db.refresh(row)
        logger.info(f"Registered session {id}: {display_name} ({mode})")
        return _to_model(row)


def list_sessions() -> List[Session]:
    """List all sessions, newest first."""
    with SessionLocal() as db:
        rows = db.execute(
            select(SessionRecord).order_by(SessionRecord.created_at.desc())
        ).scalars().all()
        return [_to_model(r) for r in rows]
