"""
Speech-to-Text (STT) for live audio capture (screen-share/tab-audio mode and
in-person audio uploads). Uses Gemini's native audio input support - see
gemini_client.generate_from_audio().
"""
from typing import List
from app.models import TranscriptChunk
from app.store import vector_store
from app.gemini_client import generate_from_audio
import logging

logger = logging.getLogger(__name__)

NO_SPEECH_SENTINEL = "[NO_SPEECH]"

TRANSCRIPTION_PROMPT = (
    "Transcribe the speech in this audio clip verbatim. "
    f"If there is no discernible speech (silence, music only, background noise), "
    f"respond with exactly: {NO_SPEECH_SENTINEL}. "
    "Do not add commentary, timestamps, or speaker labels - return only the spoken words."
)


def _format_timestamp(total_seconds: float) -> str:
    """Convert elapsed seconds to HH:MM:SS, matching TranscriptChunk.timestamp convention."""
    total_seconds = max(0, int(total_seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# WebM/Matroska files must start with this exact 4-byte EBML magic number.
EBML_MAGIC = b"\x1a\x45\xdf\xa3"


def _diagnose_audio_bytes(audio_bytes: bytes) -> str:
    """Cheap structural diagnostics for debugging chunk upload issues - not
    a full parse, just enough to tell malformed/empty audio apart from a
    genuinely valid file Gemini just couldn't find speech in."""
    size = len(audio_bytes)
    starts_with_ebml = audio_bytes[:4] == EBML_MAGIC
    head_hex = audio_bytes[:16].hex()
    tail_hex = audio_bytes[-16:].hex() if size >= 16 else audio_bytes.hex()
    return f"size={size}B starts_with_ebml_magic={starts_with_ebml} head={head_hex} tail={tail_hex}"


def transcribe_audio(
    session_id: str,
    audio_bytes: bytes,
    mime_type: str,
    start_offset_seconds: float
) -> List[TranscriptChunk]:
    """
    Transcribe a single audio chunk and return it as one TranscriptChunk
    timestamped at start_offset_seconds. Returns [] if no speech is detected.
    """
    try:
        logger.info(
            f"Transcribing chunk for session {session_id} @ {start_offset_seconds}s: "
            f"{_diagnose_audio_bytes(audio_bytes)}"
        )
        text = generate_from_audio(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            prompt=TRANSCRIPTION_PROMPT,
            temperature=0.0,
        ).strip()

        if not text or text == NO_SPEECH_SENTINEL:
            logger.info(f"No speech detected in chunk for session {session_id} @ {start_offset_seconds}s")
            return []

        if "provide the audio" in text.lower() or "provide an audio" in text.lower():
            logger.warning(
                f"Gemini reported no usable audio attached for session {session_id} "
                f"@ {start_offset_seconds}s despite a non-empty request. "
                f"{_diagnose_audio_bytes(audio_bytes)}"
            )

        chunk = TranscriptChunk(
            timestamp=_format_timestamp(start_offset_seconds),
            text=text,
            speaker=None,
        )
        return [chunk]

    except Exception as e:
        logger.error(f"Error transcribing audio chunk for session {session_id}: {e}")
        return []


def process_audio_upload(
    session_id: str,
    audio_data: bytes,
    mime_type: str,
    start_offset_seconds: float
) -> bool:
    """
    Transcribe an uploaded audio chunk and add it to the vector store.
    Returns False on error OR if no speech was detected (not necessarily an error).
    """
    try:
        chunks = transcribe_audio(session_id, audio_data, mime_type, start_offset_seconds)
        if chunks:
            vector_store.add_chunks(session_id=session_id, chunks=chunks)
            logger.info(f"Added {len(chunks)} transcribed chunk(s) for session {session_id}")
            return True
        return False

    except Exception as e:
        logger.error(f"Error processing audio upload: {e}")
        return False


def get_screen_share_session_id(share_id: str) -> str:
    """Convert a screen-share client id to internal session ID."""
    return f"screenshare_{share_id}"


def get_inperson_session_id(lecture_id: str) -> str:
    """Convert lecture ID to internal session ID."""
    return f"inperson_{lecture_id}"
