"""
Local LLM via Ollama — no API keys, no rate limits.
Run: ollama serve && ollama run llama3.2
Then recap and Q&A use this model instead of Gemini/OpenAI.
"""
import json
import logging
import urllib.request
import urllib.error
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Timeout for generation (long transcript = long prompt)
OLLAMA_TIMEOUT = 180


def _ollama_chat(system: str, user: str, model: str) -> Optional[str]:
    """
    Call Ollama /api/chat. Returns assistant message content or None on failure.
    """
    base = getattr(settings, "ollama_base_url", "http://localhost:11434") or "http://localhost:11434"
    url = base.rstrip("/") + "/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
            out = json.loads(resp.read().decode())
            msg = out.get("message") or {}
            return (msg.get("content") or "").strip()
    except urllib.error.URLError as e:
        logger.warning(f"Ollama not available: {e}")
        return None
    except Exception as e:
        logger.warning(f"Ollama request failed: {e}")
        return None


def is_available() -> bool:
    """True if Ollama is configured and reachable."""
    base = getattr(settings, "ollama_base_url", "http://localhost:11434") or ""
    if not base.strip():
        return False
    url = base.rstrip("/") + "/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            models = data.get("models") or []
            if models:
                logger.info("Ollama available, models: %s", [m.get("name") for m in models])
            return bool(models)
    except Exception as e:
        logger.debug("Ollama not reachable: %s", e)
        return False


def generate_recap(transcript: str) -> Optional[str]:
    """
    Use local LLM to generate bullet-point key points from transcript.
    Returns raw model output (bullets) or None if Ollama unavailable.
    """
    if not getattr(settings, "use_local_llm", True):
        return None
    model = getattr(settings, "ollama_model", "llama3.2") or "llama3.2"
    system = """You are a meeting note-taker. Convert the meeting content (spoken + any on-screen/slide text) into short bullet-point key points.
- Use BOTH what was said and any text from slides or on-screen (e.g. [On-screen] or Slide). Include important points that appear only on screen.
- Write in your own words. No quotes. No timestamps or speaker names in output.
- Keep each bullet short (under 25 words). Complete thoughts only.
- Output ONLY the bullet list, one per line. No intro line."""
    user = "Here is the meeting content (transcript and any slide/on-screen text). Give only a bullet list of key points.\n\n" + transcript
    return _ollama_chat(system, user, model)


def generate_answer(question: str, evidence_text: str) -> Optional[str]:
    """
    Use local LLM to answer the question using only the provided evidence.
    Returns answer text or None if Ollama unavailable.
    """
    if not getattr(settings, "use_local_llm", True):
        return None
    model = getattr(settings, "ollama_model", "llama3.2") or "llama3.2"
    system = "You answer questions about the meeting using ONLY the provided evidence (may include spoken transcript and on-screen/slide text). Be concise. Do not speculate."
    user = f"Question: {question}\n\nEvidence (transcript and/or on-screen content):\n{evidence_text}\n\nAnswer:"
    return _ollama_chat(system, user, model)
