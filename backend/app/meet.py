"""
Google Meet transcript integration.
Uses Google Meet REST API (conferenceRecords.transcripts) for post-meeting transcripts,
and supports webhook-style payloads for compatibility with frontend/ingest flow.

For a Google-sponsored hackathon we use Google Meet instead of Zoom.
- Post-meeting: Meet API conferenceRecords.transcripts + transcript entries
- Real-time style: Accept same chunk payloads (e.g. from Meet add-on or manual ingest)
"""
from typing import List, Optional
from app.models import TranscriptChunk
from app.store import vector_store
import logging
import os

logger = logging.getLogger(__name__)

# Optional: Google Meet API (Workspace) - requires OAuth / service account
MEET_API_ENABLED = os.environ.get("GOOGLE_MEET_API_ENABLED", "false").lower() == "true"


def _session_id(conference_record_or_meeting_id: str) -> str:
    """Unified session id for Meet-backed sessions."""
    return f"meet_{conference_record_or_meeting_id}"


def process_meet_webhook(meeting_id: str, transcript_chunk: TranscriptChunk) -> bool:
    """
    Process an incoming Google Meet transcript chunk (webhook or push style).
    Same contract as Zoom webhook for easy swap: meeting_id + one chunk.
    """
    logger.info(f"Processing Meet webhook for meeting {meeting_id}")
    try:
        session_id = _session_id(meeting_id)
        vector_store.add_chunks(session_id=session_id, chunks=[transcript_chunk])
        logger.info(f"Added Meet transcript chunk at {transcript_chunk.timestamp}")
        return True
    except Exception as e:
        logger.error(f"Error processing Meet webhook: {e}")
        return False


def simulate_meet_transcript(meeting_id: str, chunks: List[TranscriptChunk]) -> bool:
    """Simulate Meet transcript ingestion for testing."""
    logger.info(f"Simulating Meet transcript for meeting {meeting_id}")
    try:
        session_id = _session_id(meeting_id)
        vector_store.add_chunks(session_id=session_id, chunks=chunks)
        logger.info(f"Simulated {len(chunks)} Meet transcript chunks")
        return True
    except Exception as e:
        logger.error(f"Error simulating Meet transcript: {e}")
        return False


def get_meet_session_id(meeting_id: str) -> str:
    """Convert Meet meeting/conference ID to internal session ID."""
    return _session_id(meeting_id)


# ---------------------------------------------------------------------------
# Google Meet REST API: fetch transcript entries from a conference record
# Requires Google Workspace (Meet) API and credentials.
# ---------------------------------------------------------------------------

def fetch_meet_transcript_entries(
    conference_record_id: str,
    transcript_id: str,
    credentials_path: Optional[str] = None,
) -> List[TranscriptChunk]:
    """
    Fetch transcript entries from Google Meet API and convert to TranscriptChunk list.
    Uses conferenceRecords.transcripts.entries.list.
    Returns [] if API is disabled or on error.
    """
    if not MEET_API_ENABLED:
        logger.info("Google Meet API not enabled (GOOGLE_MEET_API_ENABLED=false). Skipping fetch.")
        return []

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_path = credentials_path or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        if not creds_path or not os.path.isfile(creds_path):
            logger.warning("Google credentials file not set or missing; skipping Meet API fetch")
            return []
        scopes = ["https://www.googleapis.com/auth/meetings.space.readonly"]
        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=scopes)
        # Meet REST API: meet v2
        service = build("meet", "v2", credentials=creds)
        parent = f"conferenceRecords/{conference_record_id}/transcripts/{transcript_id}"
        response = service.conferenceRecords().transcripts().entries().list(parent=parent).execute()
        entries = response.get("transcriptEntries") or []

        chunks: List[TranscriptChunk] = []
        for entry in entries:
            # Meet API: startTime/endTime are RFC3339; we use HH:MM:SS for our model
            start = entry.get("startTime") or ""
            # Simple conversion: if it's already duration-like use it; else derive
            ts = _rfc3339_to_hhmmss(start) if start else "00:00:00"
            chunks.append(
                TranscriptChunk(
                    timestamp=ts,
                    text=entry.get("text") or "",
                    speaker=entry.get("participant"),
                )
            )
        logger.info(f"Fetched {len(chunks)} Meet transcript entries for {parent}")
        return chunks
    except FileNotFoundError:
        logger.warning("Google credentials file not found; skipping Meet API fetch")
        return []
    except Exception as e:
        logger.error(f"Error fetching Meet transcript entries: {e}")
        return []


def _rfc3339_to_hhmmss(rfc3339: str) -> str:
    """Convert RFC3339 timestamp to HH:MM:SS (duration-style) for our model."""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(rfc3339.replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except Exception:
        return "00:00:00"


def ingest_meet_transcript_from_api(
    conference_record_id: str,
    transcript_id: str,
    credentials_path: Optional[str] = None,
) -> bool:
    """
    Fetch transcript from Meet API and ingest into vector store.
    Returns True if at least one chunk was ingested.
    """
    chunks = fetch_meet_transcript_entries(
        conference_record_id, transcript_id, credentials_path
    )
    if not chunks:
        return False
    session_id = _session_id(conference_record_id)
    vector_store.add_chunks(session_id=session_id, chunks=chunks)
    return True
