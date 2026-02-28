"""
Google Meet transcript ingestion (live captions / recording).
In production: Meet live captions API, Meet recording → Drive/YouTube transcript, or Pub/Sub.
"""
from typing import List, Optional
import hmac
import hashlib
import logging
from app.models import TranscriptChunk, GoogleMeetWebhookPayload
from app.store import vector_store
from app.config import settings

logger = logging.getLogger(__name__)


def verify_meet_webhook_signature(payload_body: bytes, signature_header: Optional[str]) -> bool:
    """
    Verify webhook signature when google_meet_webhook_secret is set.
    Uses HMAC-SHA256; in production align with Google Pub/Sub or Meet webhook signing.
    """
    if not settings.google_meet_webhook_secret or not signature_header:
        return True
    expected = hmac.new(
        settings.google_meet_webhook_secret.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)


def process_meet_webhook(payload: GoogleMeetWebhookPayload) -> bool:
    """
    Process incoming Google Meet transcript/captions webhook.
    Caller (main) should verify signature via verify_meet_webhook_signature when secret is set.
    """
    logger.info(f"[STUB] Processing Google Meet webhook for meeting {payload.meeting_id}")

    try:
        session_id = get_meet_session_id(payload.meeting_id)
        vector_store.add_chunks(session_id=session_id, chunks=[payload.transcript_chunk])
        logger.info(f"[STUB] Added Meet transcript chunk at {payload.transcript_chunk.timestamp}")
        return True
    except Exception as e:
        logger.error(f"Error processing Meet webhook: {e}")
        return False


def simulate_meet_transcript(meeting_id: str, chunks: List[TranscriptChunk]) -> bool:
    """
    Simulate Google Meet transcript ingestion for testing.
    Mirrors what would happen with live captions or recording transcript.
    """
    logger.info(f"[STUB] Simulating Google Meet transcript for meeting {meeting_id}")

    try:
        session_id = get_meet_session_id(meeting_id)
        vector_store.add_chunks(session_id=session_id, chunks=chunks)
        logger.info(f"[STUB] Simulated {len(chunks)} Meet transcript chunks")
        return True
    except Exception as e:
        logger.error(f"Error simulating Meet transcript: {e}")
        return False


def get_meet_session_id(meeting_id: str) -> str:
    """Convert Google Meet meeting ID/link to internal session ID."""
    return f"meet_{meeting_id}"
