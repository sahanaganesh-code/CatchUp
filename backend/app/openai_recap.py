"""
OpenAI-based recap: paraphrased, shortened bullet points (no quotes, lecture-style).
Use when OPENAI_API_KEY is set to avoid Gemini rate limits for recap.
"""
import logging
from typing import List

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM = """You are a meeting note-taker. Your job is to turn a transcript into short, clear bullet points.

RULES:
- Write in your own words. PARAPHRASE. Do not quote or copy sentences from the transcript.
- Keep each bullet SHORT: one line, like jotted lecture notes. 5–15 words per bullet when possible.
- No timestamps. No speaker names in the bullets.
- Group related ideas. Only include important points: decisions, action items, main ideas, outcomes.
- Output ONLY the bullet list. No intro line, no "Key points:", no JSON. Just bullets, one per line."""


def recap_with_openai(transcript: str) -> str:
    """
    Call OpenAI to get paraphrased, shortened bullet points. Returns raw model response text.
    """
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_recap_model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Here is the meeting transcript. Give me short bullet-point key points in your own words.\n\n" + transcript},
        ],
        max_tokens=1500,
    )
    text = (response.choices[0].message.content or "").strip()
    logger.info(f"OpenAI recap returned {len(text)} chars")
    return text


def parse_openai_bullets(raw: str) -> List[str]:
    """Strip labels and split into key_points list."""
    import re
    s = raw.strip()
    for prefix in ("Summary:", "Notes:", "Key points:", "KEY POINTS:", "Here are the key points:", "Bullet points:"):
        if s.lower().startswith(prefix.lower()):
            s = s[len(prefix):].strip()
    for prefix in ("• ", "— ", "– "):
        if s.startswith(prefix):
            s = s[len(prefix):].strip()
    points = []
    for line in s.splitlines():
        line = line.strip()
        if not line or len(line) < 5:
            continue
        for p in ("- ", "* ", "• ", "– ", "— "):
            if line.startswith(p):
                line = line[len(p):].strip()
                break
        if re.match(r"^\d+[.)]\s*", line):
            line = re.sub(r"^\d+[.)]\s*", "", line).strip()
        if line:
            points.append(line)
    return points if points else [line.strip() for line in s.splitlines() if line.strip() and len(line.strip()) > 5]
