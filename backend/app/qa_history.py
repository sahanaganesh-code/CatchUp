"""
Persistence for Q&A conversations, so revisiting a past session shows what
was already asked instead of starting fresh every time.
"""
from typing import List
from sqlalchemy import select
from app.db import SessionLocal, QAHistoryRow
from app.models import QAHistoryItem, Evidence, QuestionResponse
import uuid
import logging

logger = logging.getLogger(__name__)


def _to_model(row: QAHistoryRow) -> QAHistoryItem:
    return QAHistoryItem(
        question=row.question,
        answer=row.answer,
        evidence=[Evidence(**e) for e in row.evidence],
        has_sufficient_evidence=row.has_sufficient_evidence,
        created_at=row.created_at,
    )


def save_qa(session_id: str, question: str, response: QuestionResponse) -> None:
    """Persist one question/answer exchange for a session."""
    with SessionLocal() as db:
        row = QAHistoryRow(
            id=str(uuid.uuid4()),
            session_id=session_id,
            question=question,
            answer=response.answer,
            evidence=[e.model_dump() for e in response.evidence],
            has_sufficient_evidence=response.has_sufficient_evidence,
        )
        db.add(row)
        db.commit()
    logger.info(f"Saved Q&A for session {session_id}")


def list_qa_history(session_id: str) -> List[QAHistoryItem]:
    """List all past Q&A for a session, oldest first (chat order)."""
    with SessionLocal() as db:
        rows = db.execute(
            select(QAHistoryRow)
            .where(QAHistoryRow.session_id == session_id)
            .order_by(QAHistoryRow.created_at)
        ).scalars().all()
        return [_to_model(r) for r in rows]
