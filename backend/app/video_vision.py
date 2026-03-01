"""
Extract visual text from video (slides, on-screen text) via frame extraction + OCR.
Used so recap and Q&A can use both transcript and slide content.
"""
import os
import subprocess
import tempfile
import logging
from typing import List

from app.models import TranscriptChunk

logger = logging.getLogger(__name__)

# Sample 1 frame every N seconds to get slide text without too many frames
FRAME_INTERVAL_SEC = 5
# Max frames to OCR (cap for very long videos)
MAX_FRAMES = 120


def _seconds_to_hhmmss(seconds: float) -> str:
    s = int(round(seconds))
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _extract_frames(video_path: str, interval_sec: float = FRAME_INTERVAL_SEC) -> List[tuple]:
    """
    Use ffmpeg to extract one frame every interval_sec. Returns list of (timestamp_sec, frame_path).
    """
    out_dir = tempfile.mkdtemp()
    out_pattern = os.path.join(out_dir, "frame_%04d.png")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", video_path,
                "-vf", f"fps=1/{interval_sec}",
                "-vframes", str(MAX_FRAMES),
                out_pattern,
            ],
            capture_output=True,
            timeout=300,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        logger.warning("Frame extraction failed: %s", e)
        return []
    frames = []
    for i in range(1, MAX_FRAMES + 1):
        path = os.path.join(out_dir, f"frame_{i:04d}.png")
        if os.path.isfile(path):
            ts = (i - 1) * interval_sec
            frames.append((ts, path))
    return frames


def _ocr_image(image_path: str) -> str:
    """Run OCR on an image; return cleaned text or empty string."""
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        # Clean: drop empty lines, collapse whitespace, take meaningful lines
        lines = [line.strip() for line in text.splitlines() if line.strip() and len(line.strip()) > 1]
        return " ".join(lines).strip() if lines else ""
    except Exception as e:
        logger.debug("OCR failed for %s: %s", image_path, e)
        return ""


def extract_visual_chunks(video_path: str) -> List[TranscriptChunk]:
    """
    Extract on-screen/slide text from video: sample frames, OCR each, return chunks
    with timestamp and speaker="Slide" so they're merged with transcript for recap & Q&A.
    Returns [] if ffmpeg or tesseract unavailable or on error.
    """
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        logger.warning("pytesseract or Pillow not installed; install with: pip install pytesseract Pillow. Visual (slide) extraction skipped.")
        return []
    if not video_path or not os.path.isfile(video_path):
        return []
    frames = _extract_frames(video_path)
    if not frames:
        return []
    chunks = []
    seen_text: set = set()
    for ts_sec, frame_path in frames:
        try:
            text = _ocr_image(frame_path)
            try:
                os.unlink(frame_path)
            except OSError:
                pass
            if not text or len(text) < 3:
                continue
            # Dedupe: same slide often appears on consecutive frames
            key = text.lower().replace(" ", "")[:80]
            if key in seen_text:
                continue
            seen_text.add(key)
            chunks.append(TranscriptChunk(
                timestamp=_seconds_to_hhmmss(ts_sec),
                text=f"[On-screen] {text}",
                speaker="Slide",
            ))
        except Exception as e:
            logger.debug("Frame OCR error: %s", e)
    try:
        parent = os.path.dirname(frames[0][1]) if frames else None
        if parent and os.path.isdir(parent):
            for _, p in frames:
                if os.path.isfile(p):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass
            try:
                os.rmdir(parent)
            except OSError:
                pass
    except Exception:
        pass
    logger.info("Extracted %d visual (slide) chunks from video", len(chunks))
    return chunks
