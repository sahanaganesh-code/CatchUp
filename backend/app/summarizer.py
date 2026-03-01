"""
Local extractive summarizer for meeting transcripts.
No API calls — uses scoring and deduplication to pick key points from chunks.
Use for fast, free recap when RECAP_USE_LOCAL=true (default).
"""
import re
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Filler prefixes to strip from the start of a point (cleaner bullets)
FILLER_PREFIXES = (
    "so ", "um ", "uh ", "and ", "and then ", "like ", "you know ", "i mean ",
    "so we ", "so the ", "so i ", "okay so ", "right so ",
)


def _words(text: str) -> set:
    """Simple word tokenization: alphanumeric tokens, lowercased."""
    if not text:
        return set()
    return set(re.findall(r"\b\w+\b", text.lower()))


def _jaccard(a: set, b: set) -> float:
    """Jaccard similarity between two sets. 0 = disjoint, 1 = identical."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# Max words per bullet: complete thoughts only, cap at 25
MAX_WORDS_PER_POINT = 25


def _shorten_to_key_point(text: str, max_words: int = MAX_WORDS_PER_POINT) -> str:
    """Shorten to complete thought(s): full sentences only, up to max_words total."""
    s = " ".join(text.split()).strip()
    if not s:
        return s
    words = s.split()
    if len(words) <= max_words:
        return s
    # Build from complete sentences so each bullet is a complete thought
    sentences = re.split(r"(?<=[.!?])\s+", s)
    result: List[str] = []
    count = 0
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        w = sent.split()
        if count + len(w) <= max_words:
            result.append(sent)
            count += len(w)
        elif not result and len(w) > max_words:
            # One long sentence: truncate at last word before max_words
            result.append(" ".join(w[:max_words]) + ("…" if len(w) > max_words else ""))
            break
        else:
            break
    return " ".join(result) if result else " ".join(words[:max_words]) + ("…" if len(words) > max_words else "")


def _clean_point(text: str) -> str:
    """One-line cleanup: strip filler, shorten, normalize whitespace, capitalize."""
    if not text or not text.strip():
        return text
    s = " ".join(text.split()).strip()
    lower = s.lower()
    for prefix in FILLER_PREFIXES:
        if lower.startswith(prefix) and len(s) > len(prefix) + 5:
            s = s[len(prefix) :].strip()
            lower = s.lower()
    s = _shorten_to_key_point(s)
    if s and s[0].islower():
        s = s[0].upper() + s[1:]
    return s


def _score_chunk(chunk: Dict[str, Any], index: int, total: int) -> float:
    """
    Score a chunk for importance. Higher = more likely to be a key point.
    - Prefer medium-length content (not one word, not a wall of text).
    - Slight boost for early/late positions (intro/conclusion).
    """
    text = (chunk.get("text") or "").strip()
    if not text or len(text) < 10:
        return -1.0
    score = 0.0
    # Length: sweet spot roughly 25–200 chars
    ln = len(text)
    if 25 <= ln <= 200:
        score += 2.0
    elif 15 <= ln <= 400:
        score += 1.0
    # Position: first 15% and last 15% get a small boost
    if total > 0:
        pct = index / max(total - 1, 1)
        if pct < 0.15 or pct > 0.85:
            score += 0.5
    return score


def summarize_chunks(chunks: List[Dict[str, Any]], max_points: int = 25) -> List[str]:
    """
    Extract key points from transcript chunks using local scoring and deduplication.
    No API calls. Returns a list of cleaned bullet strings in transcript order.
    """
    if not chunks:
        return []

    total = len(chunks)
    # Score each chunk; keep index for ordering later
    scored: List[tuple] = []
    for i, c in enumerate(chunks):
        s = _score_chunk(c, i, total)
        if s >= 0:
            scored.append((s, i, c.get("text", "").strip()))
    if not scored:
        # Fallback: take first N chunks with enough text
        for i, c in enumerate(chunks):
            t = (c.get("text") or "").strip()
            if len(t) >= 15:
                scored.append((0.5, i, t))
    # Sort by score descending, then take top candidates
    scored.sort(key=lambda x: (-x[0], x[1]))
    candidates = scored[: max_points * 2]  # take extra before dedupe
    # Deduplicate by similarity: if a candidate is too similar to an already-selected one, skip
    selected: List[tuple] = []  # (index, text)
    for _s, idx, text in candidates:
        words = _words(text)
        if len(words) < 3:
            continue
        duplicate = False
        for _idx_prev, text_prev in selected:
            if _jaccard(words, _words(text_prev)) > 0.55:
                duplicate = True
                break
        if not duplicate:
            selected.append((idx, text))
        if len(selected) >= max_points:
            break
    # Order by original position and clean
    selected.sort(key=lambda x: x[0])
    points = [_clean_point(t) for _, t in selected if _clean_point(t)]
    return points


def local_recap_from_chunks(chunks: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
    """
    Build recap from chunks using local summarizer only. No summary block — only key points.
    Returns (summary, key_points). For local recap, summary is empty; key_points is the list (each ≤25 words, complete thought).
    """
    key_points = summarize_chunks(chunks)
    return "", key_points
