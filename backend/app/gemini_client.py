"""
Gemini API client wrapper for embeddings and text generation.
Uses google.generativeai package with REST transport to avoid gRPC issues.
"""
import re
import time
import google.generativeai as genai
from app.config import settings
import logging
import os

logger = logging.getLogger(__name__)


class GeminiQuotaExceeded(Exception):
    """Raised when Gemini API returns 429 (quota/rate limit exceeded)."""
    def __init__(self, message: str = "Gemini rate limit reached.", retry_after_seconds: int = 60):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message)

# Set environment variable to use REST instead of gRPC
os.environ['GOOGLE_API_USE_CLIENT_CERTIFICATE'] = 'false'

# Configure Gemini with API key (allow None when using local embeddings/recap/QA only)
genai.configure(api_key=settings.gemini_api_key or "no-key", transport='rest')


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """
    Embed texts using Gemini embedding model.
    
    Args:
        texts: List of text strings to embed
        task_type: Either "RETRIEVAL_DOCUMENT" for stored chunks or "RETRIEVAL_QUERY" for queries
    
    Returns:
        List of embedding vectors (list of floats)
    """
    try:
        logger.info(f"Embedding {len(texts)} texts with task_type={task_type}")
        
        # Use google.generativeai.embed_content
        result = genai.embed_content(
            model=settings.gemini_embed_model,
            content=texts,
            task_type=task_type
        )
        
        # result['embedding']: single text -> 1D list; multiple texts -> list of lists
        raw = result['embedding']
        if not raw:
            return []
        if isinstance(raw[0], (int, float)):
            raw = [raw]
        logger.info(f"Successfully generated {len(raw)} embeddings")
        return raw
    
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise


def _is_quota_error(exc: Exception) -> bool:
    """Only treat as rate limit when the API actually returned 429 (avoids false 503)."""
    return "429" in str(exc)


def _parse_retry_seconds(exc: Exception) -> int:
    """Parse 'Please retry in 20.5s' or similar from error message."""
    msg = str(exc)
    m = re.search(r"retry in (\d+(?:\.\d+)?)\s*s", msg, re.I)
    if m:
        return max(1, min(30, int(float(m.group(1)))))  # cap at 30s for retry wait
    return 15  # default wait 15s for RPM limit


def generate_text_with_system(system_instruction: str, user_content: str, model: str = None) -> str:
    """
    Generate text using Gemini with a system instruction and separate user content.
    Use for recap: system sets role/constraints, user content is the transcript.
    On 429: wait and retry up to 2 times, then try fallback model, then raise.
    """
    if model is None:
        model = settings.gemini_model

    def _generate(m: str) -> str:
        gen_model = genai.GenerativeModel(m, system_instruction=system_instruction)
        response = gen_model.generate_content(user_content)
        return response.text

    last_error = None
    retry_after = 15
    max_retries = 2

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Generating with system instruction, model={model} (attempt {attempt + 1})")
            text = _generate(model).strip()
            logger.info(f"Successfully generated {len(text)} characters")
            return text
        except Exception as e:
            last_error = e
            if not _is_quota_error(e):
                logger.error(f"Gemini error (not 429): {e}")
                raise
            retry_after = _parse_retry_seconds(e)
            if attempt < max_retries:
                logger.warning(f"Gemini 429 (model={model}), waiting {retry_after}s before retry...")
                time.sleep(retry_after)
            else:
                break

    if getattr(settings, "gemini_model_fallback", None) and settings.gemini_model_fallback != model:
        try:
            logger.info(f"Trying fallback model {settings.gemini_model_fallback}")
            text = _generate(settings.gemini_model_fallback).strip()
            logger.info(f"Fallback succeeded, generated {len(text)} characters")
            return text
        except Exception as e2:
            if _is_quota_error(e2):
                retry_after = _parse_retry_seconds(e2)
            last_error = e2

    raise GeminiQuotaExceeded(
        "Gemini rate limit reached. Please try again in a minute or check your API quota.",
        retry_after_seconds=retry_after,
    )


def generate_text(prompt: str, model: str = None) -> str:
    """
    Generate text using Gemini model.
    On 429: wait and retry up to 2 times, then try fallback model, then raise.
    """
    if model is None:
        model = settings.gemini_model

    def _generate(m: str) -> str:
        gen_model = genai.GenerativeModel(m)
        response = gen_model.generate_content(prompt)
        return response.text

    last_error = None
    retry_after = 15
    max_retries = 2  # wait and retry same model up to 2 times (3 attempts total)

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Generating text with model={model} (attempt {attempt + 1})")
            text = _generate(model).strip()
            logger.info(f"Successfully generated {len(text)} characters")
            return text
        except Exception as e:
            last_error = e
            if not _is_quota_error(e):
                logger.error(f"Gemini error (not 429): {e}")
                raise  # surface real error (403, 404, 500, etc.) so you see actual message
            retry_after = _parse_retry_seconds(e)
            if attempt < max_retries:
                logger.warning(f"Gemini 429 (model={model}), waiting {retry_after}s before retry...")
                time.sleep(retry_after)
            else:
                break

    # All retries failed; try fallback model once
    if getattr(settings, "gemini_model_fallback", None) and settings.gemini_model_fallback != model:
        try:
            logger.info(f"Trying fallback model {settings.gemini_model_fallback}")
            text = _generate(settings.gemini_model_fallback).strip()
            logger.info(f"Fallback succeeded, generated {len(text)} characters")
            return text
        except Exception as e2:
            if _is_quota_error(e2):
                retry_after = _parse_retry_seconds(e2)
            last_error = e2

    raise GeminiQuotaExceeded(
        "Gemini rate limit reached. Please try again in a minute or check your API quota.",
        retry_after_seconds=retry_after,
    )
