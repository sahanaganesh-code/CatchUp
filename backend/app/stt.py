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

# Sync recognize limit: 60 seconds. Use 40 sec per chunk so recordings >40s (e.g. 45s) are chunked and work.
# For 16kHz mono LINEAR16: 40 * 16000 * 2 = 1_280_000 bytes per segment. Supports hour-long lectures.
SYNC_MAX_BYTES_16K_MONO = 40 * 16000 * 2

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


def _hhmmss_to_seconds(timestamp: str) -> float:
    """Parse HH:MM:SS (or H:MM:SS, MM:SS) to float seconds."""
    if not timestamp or not timestamp.strip():
        return 0.0
    parts = timestamp.strip().split(":")
    if len(parts) == 3:
        h, m, s = int(parts[0] or 0), int(parts[1] or 0), float(parts[2] or 0)
    elif len(parts) == 2:
        h, m, s = 0, int(parts[0] or 0), float(parts[1] or 0)
    else:
        return 0.0
    return h * 3600 + m * 60 + s


def _duration_to_seconds(obj) -> float:
    """Convert protobuf Duration (seconds+nanos) or datetime.timedelta to float seconds."""
    if obj is None:
        return 0.0
    if hasattr(obj, "total_seconds"):
        return float(obj.total_seconds())
    sec = getattr(obj, "seconds", 0) or 0
    if hasattr(obj, "nanos"):
        return sec + (getattr(obj, "nanos", 0) or 0) / 1e9
    if hasattr(obj, "microseconds"):
        return sec + (getattr(obj, "microseconds", 0) or 0) / 1e6
    return float(sec)


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
                            ts = _seconds_to_hhmmss(_duration_to_seconds(w0.start_offset))
                        elif hasattr(w0, "start_time") and getattr(w0, "start_time", None):
                            ts = _seconds_to_hhmmss(_duration_to_seconds(w0.start_time))
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
    *,
    explicit_linear16: bool = False,
) -> tuple[List[TranscriptChunk], Optional[str]]:
    """
    Transcribe using Google Cloud Speech-to-Text (v2). No Gemini.
    Long audio (>~1 min / >1MB): upload to GCS and use batch_recognize (set GOOGLE_CLOUD_STT_BUCKET).
    Short audio: sync recognize (60s limit).
    When explicit_linear16=True, audio_content is raw PCM s16le 16kHz mono; use ExplicitDecodingConfig.
    Returns (chunks, error_message).
    """
    project = _get_cloud_project()
    if not project:
        return [], "GOOGLE_CLOUD_PROJECT not set (check .env)"

    # Long audio: GCS path only for non-PCM (e.g. MP3). Raw PCM (explicit_linear16) must use chunked sync below.
    bucket = (getattr(settings, "google_cloud_stt_bucket", None) or os.environ.get("GOOGLE_CLOUD_STT_BUCKET") or "").strip()
    if not explicit_linear16 and len(audio_content) > LONG_AUDIO_SIZE_THRESHOLD and bucket:
        return _transcribe_long_audio_via_gcs(audio_content, bucket, project)

    if not explicit_linear16 and len(audio_content) > LONG_AUDIO_SIZE_THRESHOLD and not bucket:
        return [], "Audio is too long for sync recognition (60s limit). Set GOOGLE_CLOUD_STT_BUCKET in .env and create a GCS bucket for long lectures (no ffmpeg needed). See backend/GOOGLE_VERIFY.md."

    try:
        from google.cloud.speech_v2 import SpeechClient
        from google.cloud.speech_v2.types import cloud_speech

        client = SpeechClient()
        recognizer = f"projects/{project}/locations/global/recognizers/_"

        def run_sync(content: bytes, time_offset_sec: float = 0.0) -> List[TranscriptChunk]:
            if explicit_linear16:
                decoding = cloud_speech.ExplicitDecodingConfig(
                    encoding=cloud_speech.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    audio_channel_count=1,
                )
                config = cloud_speech.RecognitionConfig(
                    explicit_decoding_config=decoding,
                    language_codes=["en-US"],
                    model="long",
                    features=cloud_speech.RecognitionFeatures(enable_word_time_offsets=True),
                )
            else:
                config = cloud_speech.RecognitionConfig(
                    auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
                    language_codes=["en-US"],
                    model="long",
                    features=cloud_speech.RecognitionFeatures(enable_word_time_offsets=True),
                )
            request = cloud_speech.RecognizeRequest(
                recognizer=recognizer,
                config=config,
                content=content,
            )
            response = client.recognize(request=request)
            out = []
            for result in getattr(response, "results", None) or []:
                alts = getattr(result, "alternatives", None) or []
                if not alts:
                    continue
                alt = alts[0]
                transcript = (getattr(alt, "transcript", None) or "").strip()
                if not transcript:
                    continue
                total_sec = time_offset_sec
                words = getattr(alt, "words", None) or []
                if words:
                    first = words[0]
                    if hasattr(first, "start_offset") and first.start_offset:
                        total_sec = time_offset_sec + _duration_to_seconds(first.start_offset)
                    elif hasattr(first, "start_time") and first.start_time:
                        total_sec = time_offset_sec + _duration_to_seconds(first.start_time)
                out.append(
                    TranscriptChunk(timestamp=_seconds_to_hhmmss(total_sec), text=transcript, speaker=None)
                )
            return out

        chunks = []
        segment_duration_sec = SYNC_MAX_BYTES_16K_MONO / (16000 * 2)
        if explicit_linear16 and len(audio_content) > SYNC_MAX_BYTES_16K_MONO:
            num_segments = (len(audio_content) + SYNC_MAX_BYTES_16K_MONO - 1) // SYNC_MAX_BYTES_16K_MONO
            logger.info("Chunking %d bytes (~%d min) into %d segments of max %.0f sec each",
                       len(audio_content), len(audio_content) // (16000 * 2 * 60), num_segments, segment_duration_sec)
            offset = 0
            segment_index = 0
            while offset < len(audio_content):
                end = min(offset + SYNC_MAX_BYTES_16K_MONO, len(audio_content))
                segment = audio_content[offset:end]
                time_offset_sec = segment_index * segment_duration_sec
                try:
                    seg_chunks = run_sync(segment, time_offset_sec)
                    chunks.extend(seg_chunks)
                    logger.info("Segment %d/%d (%d–%d bytes): %d chunks",
                                segment_index + 1, num_segments, offset, end, len(seg_chunks))
                except Exception as seg_err:
                    logger.warning("Segment %d failed: %s (continuing with other segments)", segment_index + 1, seg_err)
                offset = end
                segment_index += 1
        else:
            chunks = run_sync(audio_content, 0.0)

        if chunks:
            logger.info(f"Cloud Speech-to-Text returned {len(chunks)} chunks total")
        elif not (explicit_linear16 and len(audio_content) > SYNC_MAX_BYTES_16K_MONO):
            logger.warning(
                "Cloud Speech-to-Text returned no results for %d bytes of audio",
                len(audio_content),
            )
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
    """Transcribe audio file using Cloud Speech-to-Text only (no Gemini)."""
    logger.info(f"Transcribing audio for session {session_id}: {audio_file_path}")
    with open(audio_file_path, "rb") as f:
        audio_content = f.read()
    chunks, _ = _transcribe_with_cloud_speech(audio_content)
    return chunks or []


def transcribe_audio_bytes(
    audio_data: bytes,
    mime_type: str = DEFAULT_AUDIO_MIME,
    filename: str = "",
) -> tuple[List[TranscriptChunk], str]:
    """
    Transcribe raw audio bytes using Cloud Speech-to-Text only (no Gemini).
    Browser audio/webm is converted to raw LINEAR16 (16kHz mono) via ffmpeg for Cloud STT.
    Treat as webm if mime is audio/webm OR filename ends with .webm (browser may omit content-type).
    Returns (chunks, error_detail).
    """
    data_to_use = audio_data
    mime_to_use = mime_type
    use_explicit_linear16 = False
    path_to_use: Optional[str] = None

    ct = (mime_type or "").strip().lower()
    fn = (filename or "").lower()
    is_wav = ct.startswith("audio/wav") or fn.endswith(".wav")
    is_webm = ct.startswith("audio/webm") or fn.endswith(".webm")

    if is_wav:
        logger.info("WAV audio detected (browser recording), converting to LINEAR16 for Cloud STT")
        pcm_bytes, conv_err = _convert_wav_to_linear16(audio_data)
        if pcm_bytes:
            if len(pcm_bytes) < 16000:
                return [], "Recording too short. Record at least 1 second of speech."
            data_to_use = pcm_bytes
            use_explicit_linear16 = True
        else:
            return [], f"Convert WAV to audio failed: {conv_err}"
    elif is_webm:
        logger.info("Webm audio detected (mime=%s, filename=%s), converting to LINEAR16/MP3 for Cloud STT", mime_type, filename)
        bucket = (getattr(settings, "google_cloud_stt_bucket", None) or os.environ.get("GOOGLE_CLOUD_STT_BUCKET") or "").strip()
        if len(audio_data) > LONG_AUDIO_SIZE_THRESHOLD and bucket:
            mp3_bytes, conv_err = _convert_webm_to_mp3(audio_data)
            if mp3_bytes:
                data_to_use = mp3_bytes
                mime_to_use = "audio/mpeg"
            else:
                return [], f"Convert webm to mp3 failed: {conv_err}"
        elif len(audio_data) > LONG_AUDIO_SIZE_THRESHOLD:
            return [], "Long webm not supported for sync. Set GOOGLE_CLOUD_STT_BUCKET in .env for long recordings."
        else:
            pcm_bytes, conv_err = _convert_webm_to_linear16(audio_data)
            if pcm_bytes:
                # Cloud STT needs at least ~0.5s of 16kHz mono s16le (16000 bytes)
                if len(pcm_bytes) < 16000:
                    return [], "Recording too short. Record at least 1 second of speech."
                data_to_use = pcm_bytes
                use_explicit_linear16 = True
            else:
                return [], f"Convert webm to audio failed: {conv_err}"

    if path_to_use is None and not use_explicit_linear16:
        suffix = ".mp3"
        for ext, m in AUDIO_MIME_TYPES.items():
            if m == mime_type:
                suffix = ext
                break
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(audio_data)
            path_to_use = f.name

    try:
        chunks, err = _transcribe_with_cloud_speech(
            data_to_use,
            file_path=path_to_use,
            mime_type=mime_to_use,
            explicit_linear16=use_explicit_linear16,
        )
        if chunks:
            return chunks, ""
        return [], err or "No speech detected in the recording. Try again with clear speech and minimal background noise."
    finally:
        try:
            if path_to_use and os.path.isfile(path_to_use):
                os.unlink(path_to_use)
        except OSError:
            pass


def _convert_webm_to_mp3(audio_data: bytes) -> Tuple[Optional[bytes], str]:
    """Convert audio/webm to MP3 for GCS long-audio path. Returns (mp3_bytes, error_message)."""
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(audio_data)
        in_path = f.name
    out_path = in_path + ".mp3"
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", in_path, "-vn", "-acodec", "libmp3lame", "-q:a", "2", out_path],
            capture_output=True,
            timeout=300,
            text=True,
        )
        if result.returncode != 0:
            return None, (result.stderr or "")[-500:].strip() or "ffmpeg failed"
        if os.path.isfile(out_path):
            with open(out_path, "rb") as f:
                return f.read(), ""
        return None, "ffmpeg produced no output"
    except FileNotFoundError:
        return None, "ffmpeg not found."
    except subprocess.TimeoutExpired:
        return None, "ffmpeg timed out"
    except Exception as e:
        return None, str(e)
    finally:
        for p in (in_path, out_path):
            try:
                if os.path.isfile(p):
                    os.unlink(p)
            except OSError:
                pass


def _convert_wav_to_linear16(audio_data: bytes) -> Tuple[Optional[bytes], str]:
    """
    Convert WAV (any sample rate/channels) to raw LINEAR16 16kHz mono for Cloud STT.
    Returns (pcm_bytes, error_message). Used for browser WAV recordings.
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_data)
        in_path = f.name
    out_path = in_path + ".raw"
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", in_path,
                "-vn", "-f", "s16le", "-ar", "16000", "-ac", "1",
                out_path,
            ],
            capture_output=True,
            timeout=600,
            text=True,
        )
        if result.returncode != 0:
            stderr = (result.stderr or "")[-500:]
            return None, stderr.strip() or "ffmpeg conversion failed"
        if os.path.isfile(out_path):
            with open(out_path, "rb") as f:
                return f.read(), ""
        return None, "ffmpeg produced no output"
    except FileNotFoundError:
        return None, "ffmpeg not found. Install ffmpeg (e.g. brew install ffmpeg)."
    except subprocess.TimeoutExpired:
        return None, "ffmpeg conversion timed out (10 min limit for long lectures)"
    except Exception as e:
        return None, str(e)
    finally:
        for p in (in_path, out_path):
            try:
                if os.path.isfile(p):
                    os.unlink(p)
            except OSError:
                pass


def _convert_webm_to_linear16(audio_data: bytes) -> Tuple[Optional[bytes], str]:
    """
    Convert browser-recorded audio/webm to raw LINEAR16 (16kHz mono, no header) for Cloud STT.
    Returns (pcm_bytes, error_message). Cloud STT requires explicit decoding for reliable results.
    """
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        f.write(audio_data)
        in_path = f.name
    out_path = in_path + ".raw"
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", in_path,
                "-vn", "-f", "s16le", "-ar", "16000", "-ac", "1",
                out_path,
            ],
            capture_output=True,
            timeout=120,
            text=True,
        )
        if result.returncode != 0:
            stderr = (result.stderr or "")[-500:]
            return None, stderr.strip() or "ffmpeg conversion failed"
        if os.path.isfile(out_path):
            with open(out_path, "rb") as f:
                return f.read(), ""
        return None, "ffmpeg produced no output"
    except FileNotFoundError:
        return None, "ffmpeg not found. Install ffmpeg (e.g. brew install ffmpeg)."
    except subprocess.TimeoutExpired:
        return None, "ffmpeg conversion timed out"
    except Exception as e:
        return None, str(e)
    finally:
        for p in (in_path, out_path):
            try:
                if os.path.isfile(p):
                    os.unlink(p)
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
                timeout=1800,
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
            return None, "ffmpeg timed out (30 min limit). Try a shorter video or compress the file."
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
    # Explicit audio/* (e.g. audio/webm from browser recorder) is never video
    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        if ct.startswith("audio/"):
            return False
        if ct in VIDEO_CONTENT_TYPES:
            return True
    ext = os.path.splitext(filename or "")[1].lower()
    return ext in VIDEO_EXTENSIONS


def process_audio_upload(
    session_id: str,
    audio_data: bytes,
    mime_type: Optional[str] = None,
    filename: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Process uploaded audio: transcribe with Cloud Speech-to-Text only.
    When the session already has chunks (e.g. live segments), new chunk timestamps
    are offset by the current session duration so timestamps and total_duration stay correct.
    Returns (success, message).
    """
    logger.info(f"Processing audio upload for session {session_id} (Google Cloud STT)")
    try:
        chunks, detail = transcribe_audio_bytes(
            audio_data,
            mime_type=mime_type or DEFAULT_AUDIO_MIME,
            filename=filename or "",
        )
        if not chunks:
            return False, detail or "Transcription returned no text."

        existing = vector_store.get_all_chunks(session_id)
        offset_sec = 0.0
        if existing:
            for c in existing:
                t = _hhmmss_to_seconds(c["timestamp"])
                if t > offset_sec:
                    offset_sec = t
        if offset_sec > 0:
            from app.models import TranscriptChunk
            chunks = [
                TranscriptChunk(
                    timestamp=_seconds_to_hhmmss(_hhmmss_to_seconds(c.timestamp) + offset_sec),
                    text=c.text,
                    speaker=c.speaker,
                )
                for c in chunks
            ]
            logger.info(f"Offset new segment by {offset_sec:.0f}s for cumulative timestamps")

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
            success, msg = process_audio_upload(
                session_id, audio_data, mime_type=audio_mime or "audio/mpeg", filename=filename
            )
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
    return process_audio_upload(
        session_id, file_data, mime_type=content_type or None, filename=filename
    )


def stream_audio_transcription(session_id: str, audio_stream) -> None:
    """
    Real-time streaming transcription (stub).
    Could use Cloud Speech-to-Text streaming_recognize in future.
    """
    logger.info(f"Streaming transcription for session {session_id} (stub)")


def get_inperson_session_id(lecture_id: str) -> str:
    """Convert lecture ID to internal session ID."""
    return f"inperson_{lecture_id}"
