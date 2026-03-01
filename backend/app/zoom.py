"""
Meeting transcript webhook ingestion (Google Meet primary).
We use Google Meet for the hackathon; this module keeps the same API surface
so main.py and frontend can keep using /api/zoom/webhook without merge conflicts.
All logic delegates to app.meet (Google Meet).
"""
from typing import List
from app.models import TranscriptChunk, ZoomWebhookPayload
from app import meet
import logging

logger = logging.getLogger(__name__)


def process_zoom_webhook(payload: ZoomWebhookPayload) -> bool:
    """
    Process incoming meeting transcript webhook (Google Meet).
    Keeps ZoomWebhookPayload for API compatibility; delegates to Meet.
    """
    logger.info(f"Processing meeting webhook for meeting {payload.meeting_id} (Google Meet)")
    return meet.process_meet_webhook(payload.meeting_id, payload.transcript_chunk)


def simulate_zoom_transcript(meeting_id: str, chunks: List[TranscriptChunk]) -> bool:
    """Simulate meeting transcript ingestion (Google Meet)."""
    return meet.simulate_meet_transcript(meeting_id, chunks)


def get_zoom_session_id(meeting_id: str) -> str:
    """Convert meeting ID to internal session ID (Meet prefix)."""
    return meet.get_meet_session_id(meeting_id)
