"""
Speech-to-Text: Google Cloud Speech-to-Text (primary), Gemini as fallback.
Long audio (>60s): upload to GCS and use batch_recognize (no ffmpeg needed).
Supports video uploads: audio is extracted with ffmpeg then transcribed.
Set GOOGLE_CLOUD_STT_BUCKET in .env and create the bucket in Google Cloud Console.
"""
from typing import List, Optional, Tuple
from app.models import TranscriptChunk
from app.config import settings
from app.store import vector_store
import logging
import subprocess
import tempfile
import os
import uuid
from io import BytesIO

logger = logging.getLogger(__name__)

# Above this size (bytes) we use GCS + batch_recognize for long audio (no ffmpeg)
LONG_AUDIO_SIZE_THRESHOLD = 1 * 1024 * 1024  # 1 MB

DEFAULT_AUDIO_MIME = "audio/mpeg"

# Cloud Speech-to-Text: project ID from .env (via settings) or os.environ
def _get_cloud_project() -> str:
    return (settings.google_cloud_project or os.environ.get("GOOGLE_CLOUD_PROJECT") or "").strip()

# Resolve credentials path so it works when server is started from project root
def _resolve_credentials():
    creds = (settings.google_application_credentials or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    if not creds:
        return
    if os.path.isabs(creds) and os.path.isfile(creds):
        return
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(backend_dir)
    for base in [os.getcwd(), backend_dir, project_root]:
        p = os.path.join(base, creds.lstrip("./"))
        if os.path.isfile(p):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(p)
            break
_resolve_credentials()


def _seconds_to_hhmmss(seconds: float) -> str:
    """Convert seconds to HH:MM:SS string."""
    s = int(round(seconds))
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _transcribe_long_audio_via_gcs(
    audio_content: bytes,
    bucket_name: str,
    project: str,
) -> tuple[List[TranscriptChunk], Optional[str]]:
    """
    Upload audio to GCS and run batch_recognize (for long audio, no ffmpeg needed).
    Returns (chunks, error_message).
    """
    try:
        from google.cloud.storage import Client as GcsClient
        from google.cloud.speech_v2 import SpeechClient
        from google.cloud.speech_v2.types import cloud_speech

        blob_name = f"catchup-stt/{uuid.uuid4().hex}.mp3"
        gcs_client = GcsClient(project=project)
        bucket = gcs_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_string(audio_content, content_type="audio/mpeg")
        uri = f"gs://{bucket_name}/{blob_name}"
        logger.info(f"Uploaded long audio to {uri}, starting batch_recognize")

        speech_client = SpeechClient()
        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=["en-US"],
            model="long",
            features=cloud_speech.RecognitionFeatures(enable_word_time_offsets=True),
        )
        file_meta = cloud_speech.BatchRecognizeFileMetadata(uri=uri)
        request = cloud_speech.BatchRecognizeRequest(
            recognizer=f"projects/{project}/locations/global/recognizers/_",
            config=config,
            files=[file_meta],
            recognition_output_config=cloud_speech.RecognitionOutputConfig(
                inline_response_config=cloud_speech.InlineOutputConfig(),
            ),
        )
        operation = speech_client.batch_recognize(request=request)
        # Wait up to 30 min for long lectures
        result = operation.result(timeout=1800)
        try:
            blob.delete()
        except Exception:
            pass

        chunks = []
        if getattr(result, "results", None):
            for file_result in result.results.values():
                # BatchRecognizeFileResult may have .transcript (RecognizeResponse) or similar
                transcript = getattr(file_result, "transcript", None) or getattr(file_result, "transcription", None)
                if not transcript:
                    continue
                results_list = getattr(transcript, "results", None) or []
                for seg in results_list:
                    alts = getattr(seg, "alternatives", None) or []
                    if not alts:
                        continue
                    alt = alts[0]
                    text = (getattr(alt, "transcript", None) or "").strip()
                    if not text:
                        continue
                    ts = "00:00:00"
                    words = getattr(alt, "words", None) or []
                    if words:
                        w0 = words[0]
                        if hasattr(w0, "start_offset") and getattr(w0, "start_offset", None):
                            so = w0.start_offset
                            s = (getattr(so, "seconds", 0) or 0) + (getattr(so, "nanos", 0) or 0) / 1e9
                            ts = _seconds_to_hhmmss(s)
                        elif hasattr(w0, "start_time") and getattr(w0, "start_time", None):
                            ts = _seconds_to_hhmmss(w0.start_time.total_seconds())
                    chunks.append(TranscriptChunk(timestamp=ts, text=text, speaker=None))
        if chunks:
            logger.info(f"Batch recognize returned {len(chunks)} chunks")
        return chunks, None
    except Exception as e:
        err = str(e)
        logger.warning(f"GCS batch_recognize failed: {err}")
        return [], err


def _transcribe_with_cloud_speech(
    audio_content: bytes,
    file_path: Optional[str] = None,
    mime_type: Optional[str] = None,
) -> tuple[List[TranscriptChunk], Optional[str]]:
    """
    Transcribe using Google Cloud Speech-to-Text (v2).
    Long audio (>~1 min / >1MB): upload to GCS and use batch_recognize (set GOOGLE_CLOUD_STT_BUCKET).
    Short audio: sync recognize (60s limit).
    Returns (chunks, error_message).
    """
    project = _get_cloud_project()
    if not project:
        return [], "GOOGLE_CLOUD_PROJECT not set (check .env)"

    # Long audio: use GCS + batch (no ffmpeg needed)
    bucket = (getattr(settings, "google_cloud_stt_bucket", None) or os.environ.get("GOOGLE_CLOUD_STT_BUCKET") or "").strip()
    if len(audio_content) > LONG_AUDIO_SIZE_THRESHOLD and bucket:
        return _transcribe_long_audio_via_gcs(audio_content, bucket, project)

    if len(audio_content) > LONG_AUDIO_SIZE_THRESHOLD and not bucket:
        return [], "Audio is too long for sync recognition (60s limit). Set GOOGLE_CLOUD_STT_BUCKET in .env and create a GCS bucket for long lectures (no ffmpeg needed). See backend/GOOGLE_VERIFY.md."

    try:
        from google.cloud.speech_v2 import SpeechClient
        from google.cloud.speech_v2.types import cloud_speech

        client = SpeechClient()
        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=["en-US"],
            model="long",
            features=cloud_speech.RecognitionFeatures(enable_word_time_offsets=True),
        )
        request = cloud_speech.RecognizeRequest(
            recognizer=f"projects/{project}/locations/global/recognizers/_",
            config=config,
            content=audio_content,
        )
        response = client.recognize(request=request)
        chunks = []
        for result in response.results:
            if not result.alternatives:
                continue
            alt = result.alternatives[0]
            transcript = (alt.transcript or "").strip()
            if not transcript:
                continue
            total_sec = 0.0
            if alt.words:
                first = alt.words[0]
                if hasattr(first, "start_offset") and first.start_offset:
                    total_sec = first.start_offset.seconds + (first.start_offset.nanos or 0) / 1e9
                elif hasattr(first, "start_time") and first.start_time:
                    total_sec = first.start_time.total_seconds()
            chunks.append(
                TranscriptChunk(timestamp=_seconds_to_hhmmss(total_sec), text=transcript, speaker=None)
            )
        if chunks:
            logger.info(f"Cloud Speech-to-Text returned {len(chunks)} chunks")
        return chunks, None
    except Exception as e:
        err = str(e)
        logger.warning(f"Cloud Speech-to-Text failed: {err}")
        return [], err


def _transcribe_with_gemini(audio_path: str, mime_type: str) -> tuple[List[TranscriptChunk], Optional[str]]:
    """Fallback: transcribe using Gemini API. Returns (chunks, error_message)."""
    import google.generativeai as genai
    from app.config import settings

    prompt = (
        "Transcribe this audio precisely. Reply with only the transcript, one segment per line: "
        "[HH:MM:SS] Speaker: text. If timestamps unknown use 00:00:00, 00:00:05, ..."
    )
    model = genai.GenerativeModel(settings.gemini_model)
    content_parts = [prompt]
    if hasattr(genai, "upload_file"):
        try:
            uploaded = genai.upload_file(audio_path, mime_type=mime_type)
            if uploaded:
                content_parts.append(uploaded)
        except Exception as e:
            logger.warning(f"genai.upload_file failed: {e}")
    if len(content_parts) == 1:
        content_parts.append(audio_path)
    try:
        response = model.generate_content(content_parts)
        text = response.text if hasattr(response, "text") else str(response)
        return _parse_gemini_transcript(text), None
    except Exception as e:
        err = str(e)
        logger.error(f"Gemini transcription error: {err}")
        return [], err


def _parse_gemini_transcript(text: str) -> List[TranscriptChunk]:
    """Parse Gemini transcript output into TranscriptChunk list."""
    chunks = []
    for line in (text or "").strip().splitlines():
        line = line.strip()
        if not line:
            continue
        ts, rest = "00:00:00", line
        if line.startswith("["):
            end = line.find("]")
            if end != -1:
                ts = line[1:end].strip()
                rest = line[end + 1 :].strip()
        if ":" in rest:
            idx = rest.index(":")
            speaker = rest[:idx].strip()
            content = rest[idx + 1 :].strip()
        else:
            speaker = "Speaker 1"
            content = rest
        if content:
            chunks.append(TranscriptChunk(timestamp=ts, text=content, speaker=speaker or None))
    if not chunks and (text or "").strip():
        chunks.append(
            TranscriptChunk(timestamp="00:00:00", text=text.strip(), speaker="Speaker 1")
        )
    return chunks


# MIME / file extension hint for Gemini fallback
AUDIO_MIME_TYPES = {
    ".mp3": "audio/mpeg", ".mpeg": "audio/mpeg", ".mpga": "audio/mpeg",
    ".wav": "audio/wav", ".webm": "audio/webm", ".m4a": "audio/mp4",
    ".mp4": "audio/mp4", ".ogg": "audio/ogg", ".flac": "audio/flac",
}

# Video extensions: we extract audio with ffmpeg then transcribe
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".m4v", ".wmv", ".flv"}
VIDEO_CONTENT_TYPES = {"video/mp4", "video/webm", "video/quicktime", "video/x-msvideo", "video/x-matroska", "video/x-m4v", "video/x-ms-wmv", "video/x-flv"}


def transcribe_audio(session_id: str, audio_file_path: str) -> List[TranscriptChunk]:
    """Transcribe audio file: Cloud STT (primary), Gemini fallback."""
    logger.info(f"Transcribing audio for session {session_id}: {audio_file_path}")
    ext = os.path.splitext(audio_file_path)[1].lower()
    mime = AUDIO_MIME_TYPES.get(ext, DEFAULT_AUDIO_MIME)
    with open(audio_file_path, "rb") as f:
        audio_content = f.read()
    chunks, _ = _transcribe_with_cloud_speech(audio_content)
    if not chunks:
        chunks, _ = _transcribe_with_gemini(audio_file_path, mime)
    return chunks


def transcribe_audio_bytes(
    audio_data: bytes,
    mime_type: str = DEFAULT_AUDIO_MIME,
) -> tuple[List[TranscriptChunk], str]:
    """
    Transcribe raw audio bytes: Cloud STT (primary), Gemini fallback.
    Long audio (>60s) is chunked automatically (needs pydub + ffmpeg).
    Returns (chunks, error_detail). error_detail is non-empty when both fail.
    """
    suffix = ".mp3"
    for ext, m in AUDIO_MIME_TYPES.items():
        if m == mime_type:
            suffix = ext
            break
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_data)
        path = f.name
    try:
        chunks, err1 = _transcribe_with_cloud_speech(audio_data, file_path=path, mime_type=mime_type)
        if chunks:
            return chunks, ""
        chunks, err2 = _transcribe_with_gemini(path, mime_type)
        if chunks:
            return chunks, ""
        detail = "Cloud STT: " + (err1 or "no text") + ". Gemini: " + (err2 or "no text")
        return [], detail
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def _extract_audio_from_video(video_data: bytes, video_suffix: str) -> Tuple[Optional[bytes], str, str]:
    """
    Extract audio from video using ffmpeg. Returns (audio_bytes, error_message, mime_type).
    On success: error_message is "", mime_type is "audio/mpeg" or "audio/wav".
    On failure: audio_bytes is None, error_message describes the failure, mime_type is "".
    """
    ext = video_suffix.lower() if video_suffix.startswith(".") else "." + video_suffix.lower()
    if ext not in VIDEO_EXTENSIONS:
        ext = ".mp4"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as vf:
        vf.write(video_data)
        video_path = vf.name
    out_mp3 = video_path + ".mp3"
    out_wav = video_path + ".wav"
    err_msg = ""

    def _run_ffmpeg(args: list, out_file: str) -> Tuple[Optional[bytes], str]:
        try:
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", video_path] + args + [out_file],
                capture_output=True,
                timeout=600,
                text=True,
            )
            if result.returncode != 0:
                stderr = (result.stderr or "")[-1500:]
                return None, stderr.strip() or f"ffmpeg exited with code {result.returncode}"
            if os.path.isfile(out_file):
                with open(out_file, "rb") as f:
                    return f.read(), ""
            return None, "ffmpeg produced no output file"
        except FileNotFoundError:
            return None, "ffmpeg not found in PATH. Install ffmpeg (e.g. brew install ffmpeg) and restart the backend."
        except subprocess.TimeoutExpired:
            return None, "ffmpeg timed out. Try a shorter video."
        except Exception as e:
            return None, str(e)

    try:
        # Try MP3 first (libmp3lame)
        audio_bytes, err_msg = _run_ffmpeg(["-vn", "-acodec", "libmp3lame", "-q:a", "2"], out_mp3)
        if audio_bytes:
            return (audio_bytes, "", "audio/mpeg")
        # Fallback: WAV (pcm_s16le is built-in; works when libmp3lame is missing)
        audio_bytes, wav_err = _run_ffmpeg(["-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1"], out_wav)
        if audio_bytes:
            return (audio_bytes, "", "audio/wav")
        return (None, wav_err or err_msg or "Could not extract audio from video.", "")
    finally:
        for p in (video_path, out_mp3, out_wav):
            try:
                if os.path.isfile(p):
                    os.unlink(p)
            except OSError:
                pass


def _is_video(filename: str, content_type: Optional[str]) -> bool:
    if content_type and content_type.split(";")[0].strip().lower() in VIDEO_CONTENT_TYPES:
        return True
    ext = os.path.splitext(filename or "")[1].lower()
    return ext in VIDEO_EXTENSIONS


def process_audio_upload(
    session_id: str, audio_data: bytes, mime_type: Optional[str] = None
) -> tuple[bool, str]:
    """
    Process uploaded audio: transcribe with Cloud Speech-to-Text (primary) or Gemini,
    then add chunks to the vector store.
    Returns (success, message).
    """
    logger.info(f"Processing audio upload for session {session_id} (Google Cloud STT primary)")
    try:
        chunks, detail = transcribe_audio_bytes(audio_data, mime_type=mime_type or DEFAULT_AUDIO_MIME)
        if not chunks:
            return False, detail or "Transcription returned no text."
        vector_store.add_chunks(session_id=session_id, chunks=chunks)
        logger.info(f"Added {len(chunks)} transcript chunks to vector store")
        return True, ""
    except Exception as e:
        logger.error(f"Error processing audio upload: {e}")
        return False, str(e)


def process_media_upload(
    session_id: str,
    file_data: bytes,
    filename: str = "",
    content_type: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Process uploaded audio or video. For video: extracts audio (transcription) and
    visual text from slides/on-screen (OCR), then adds both to the session so
    recap and Q&A use transcript + visual content.
    Returns (success, message).
    """
    if _is_video(filename, content_type):
        logger.info(f"Video upload detected ({filename}), extracting audio and visual content")
        ext = os.path.splitext(filename or "video")[1]
        ext = ext.lower() if ext.startswith(".") else "." + (ext or "mp4")
        if ext not in VIDEO_EXTENSIONS:
            ext = ".mp4"
        video_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as vf:
                vf.write(file_data)
                video_path = vf.name
            audio_data, extract_err, audio_mime = _extract_audio_from_video(file_data, ext)
            if audio_data is None:
                return False, extract_err or "Could not extract audio from video. Is ffmpeg installed?"
            from app.video_vision import extract_visual_chunks
            visual_chunks = extract_visual_chunks(video_path) if video_path and os.path.isfile(video_path) else []
            success, msg = process_audio_upload(session_id, audio_data, mime_type=audio_mime or "audio/mpeg")
            if not success:
                return False, msg
            if visual_chunks:
                vector_store.add_chunks(session_id=session_id, chunks=visual_chunks)
                logger.info(f"Added {len(visual_chunks)} visual (slide/on-screen) chunks for recap and Q&A")
            return True, ""
        finally:
            if video_path and os.path.isfile(video_path):
                try:
                    os.unlink(video_path)
                except OSError:
                    pass
    return process_audio_upload(session_id, file_data)


def stream_audio_transcription(session_id: str, audio_stream) -> None:
    """
    Real-time streaming transcription (stub).
    Could use Cloud Speech-to-Text streaming_recognize in future.
    """
    logger.info(f"Streaming transcription for session {session_id} (stub)")


def get_inperson_session_id(lecture_id: str) -> str:
    """Convert lecture ID to internal session ID."""
    return f"inperson_{lecture_id}"
