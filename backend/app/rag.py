from typing import List, Dict, Any
from app.config import settings
from app.models import Evidence, QuestionResponse, RecapResponse
from app.store import vector_store
from app.gemini_client import generate_text, generate_text_with_system, GeminiQuotaExceeded
from app.summarizer import local_recap_from_chunks
from app.openai_recap import recap_with_openai, parse_openai_bullets
from app import local_llm
import logging
import re

logger = logging.getLogger(__name__)


def extract_evidence_from_chunks(chunks: List[Dict[str, Any]]) -> List[Evidence]:
    """Extract evidence from retrieved chunks."""
    evidence = []
    for chunk in chunks[:settings.max_evidence_quotes]:
        evidence.append(Evidence(
            timestamp=chunk["timestamp"],
            quote=chunk["text"][:200],  # Truncate long quotes
            speaker=chunk.get("speaker")
        ))
    return evidence


def format_evidence_for_prompt(evidence: List[Evidence]) -> str:
    """Format evidence for LLM prompt."""
    formatted = []
    for i, ev in enumerate(evidence, 1):
        speaker_prefix = f"[{ev.speaker}] " if ev.speaker else ""
        formatted.append(f"{i}. [{ev.timestamp}] {speaker_prefix}\"{ev.quote}\"")
    return "\n".join(formatted)


def _synthesize_answer_local(question: str, evidence: List[Evidence]) -> str:
    """
    Build an evidence-based answer without any LLM. Meets project rule: grounded in transcript.
    Returns a short synthesis + pointer to the supporting quotes (which are always shown).
    """
    if not evidence:
        return "Insufficient evidence in the transcript to answer this question."
    # One-sentence summary from the first (strongest) quote
    first = evidence[0].quote.strip()
    if len(first) > 120:
        first = first[:117].rstrip() + "..."
    return f"Based on the transcript: \"{first}\" The supporting quotes below provide the full evidence with timestamps."


def answer_question(session_id: str, question: str) -> QuestionResponse:
    """
    Answer a question with evidence-based grounding.
    HARD RULE: Must return 2-5 evidence quotes or say insufficient evidence.
    When qa_use_local=True: no API — keyword retrieval + local synthesis.
    """
    logger.info(f"Answering question for session {session_id}: {question}")

    if getattr(settings, "qa_use_local", True):
        chunks = vector_store.query_chunks_by_keywords(session_id, question, top_k=settings.retrieval_top_k)
    else:
        chunks = vector_store.query_chunks(session_id, question, top_k=settings.retrieval_top_k)

    if not chunks or len(chunks) < settings.min_evidence_quotes:
        return QuestionResponse(
            answer="Insufficient evidence in the transcript to answer this question.",
            evidence=[],
            has_sufficient_evidence=False,
        )

    evidence = extract_evidence_from_chunks(chunks)
    evidence = evidence[: settings.max_evidence_quotes]
    if len(evidence) < settings.min_evidence_quotes:
        return QuestionResponse(
            answer="Insufficient evidence in the transcript to answer this question.",
            evidence=evidence,
            has_sufficient_evidence=False,
        )

    if getattr(settings, "qa_use_local", True):
        evidence_text = format_evidence_for_prompt(evidence)
        answer = local_llm.generate_answer(question, evidence_text)
        if not answer or len(answer.strip()) < 5:
            answer = _synthesize_answer_local(question, evidence)
        return QuestionResponse(answer=answer.strip(), evidence=evidence, has_sufficient_evidence=True)

    evidence_text = format_evidence_for_prompt(evidence)
    prompt = f"""You are answering a question about a meeting transcript. You MUST base your answer ONLY on the provided evidence.

Question: {question}

Evidence from transcript:
{evidence_text}

Instructions:
1. Answer the question using ONLY the information in the evidence above
2. Reference specific timestamps when making points
3. If the evidence doesn't fully answer the question, acknowledge the limitation
4. Be concise and direct

Answer:"""
    try:
        answer = generate_text(prompt, model=settings.gemini_model).strip()
        return QuestionResponse(answer=answer, evidence=evidence, has_sufficient_evidence=True)
    except GeminiQuotaExceeded:
        raise
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return QuestionResponse(
            answer=f"Error generating answer: {str(e)}",
            evidence=evidence,
            has_sufficient_evidence=False,
        )


def _clean_summary_text(raw: str) -> str:
    """Make summary readable: normalize whitespace, clear paragraph breaks."""
    if not raw or not raw.strip():
        return raw
    # Collapse multiple newlines to at most two (paragraph break)
    lines = [line.strip() for line in raw.strip().splitlines() if line.strip()]
    return "\n\n".join(lines) if lines else raw.strip()


def _parse_bullet_list(raw: str) -> List[str]:
    """Parse Gemini's bullet list into key_points. Strip common prefixes, keep substantial lines."""
    if not raw or not raw.strip():
        return []
    lines = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line or len(line) < 10:
            continue
        # Strip bullet prefixes: "- ", "* ", "• ", number. or number)
        for prefix in ("- ", "* ", "• ", "– "):
            if line.startswith(prefix):
                line = line[len(prefix):].strip()
                break
        if re.match(r"^\d+[.)]\s*", line):
            line = re.sub(r"^\d+[.)]\s*", "", line).strip()
        if line:
            lines.append(line)
    return lines


RECAP_SYSTEM_INSTRUCTION = """You are an AI meeting intelligence assistant.
Your job is to convert meeting content (transcript + any on-screen/slide text) into SHORT, clear bullet-point notes.

You MUST:
- Use BOTH what was said aloud AND any text from slides or on-screen (e.g. "[On-screen] ..." or speaker "Slide"). Include key points that appear only visually if they matter.
- Rewrite in your own words. PARAPHRASE. Do NOT quote verbatim.
- Keep each bullet SHORT: one line, 5–15 words when possible.
- Do NOT include timestamps or speaker labels in the output.
- Group related ideas. Include important points: decisions, action items, main ideas, outcomes, and notable slide/visual content.

Output ONLY the bullet list. No intro line—just bullets, one per line."""


def generate_recap(session_id: str) -> RecapResponse:
    """
    Generate a meeting recap: short, paraphrased key points (no quotes).
    Tries: 1) OpenAI (if key set), 2) Gemini, 3) local summarizer fallback.
    """
    logger.info(f"Generating recap for session {session_id}")

    all_chunks = vector_store.get_all_chunks(session_id)

    if not all_chunks:
        return RecapResponse(
            summary="No transcript data available for this session.",
            key_points=[],
            evidence=[],
        )

    full_transcript = "\n\n".join(
        f"[{chunk['timestamp']}] {chunk.get('speaker', 'Speaker')}: {chunk['text']}"
        for chunk in all_chunks
    )

    # Local path: try local LLM (Ollama) first, then extractive summarizer
    if settings.recap_use_local:
        content = local_llm.generate_recap(full_transcript)
        if content and len(content) >= 20:
            for prefix in ("Summary:", "Notes:", "Key points:", "KEY POINTS:", "Here are the key points:", "Bullet summary:"):
                if content.lower().startswith(prefix.lower()):
                    content = content[len(prefix) :].strip()
            content = _clean_summary_text(content)
            key_points = _parse_bullet_list(content)
            if key_points:
                return RecapResponse(summary="", key_points=key_points, evidence=[])
        summary, key_points = local_recap_from_chunks(all_chunks)
        return RecapResponse(summary=summary, key_points=key_points, evidence=[])

    # 1) Try OpenAI if key is set (paraphrased, short key points)
    openai_key = getattr(settings, "openai_api_key", None) and (settings.openai_api_key or "").strip()
    if openai_key:
        try:
            content = recap_with_openai(full_transcript)
            if content and len(content) >= 20:
                key_points = parse_openai_bullets(content)
                if not key_points:
                    key_points = [line.strip() for line in content.splitlines() if line.strip() and len(line.strip()) > 10]
                summary = _clean_summary_text(content)
                return RecapResponse(summary=summary, key_points=key_points, evidence=[])
        except Exception as e:
            logger.warning(f"OpenAI recap failed, trying Gemini: {e}")

    # 2) Try Gemini (paraphrased, short key points)
    user_message = (
        "Here is the full meeting transcript. Generate a concise bulleted list of key points discussed. "
        "Short bullets, your own words, no quotes, no timestamps.\n\n" + full_transcript
    )
    try:
        content = generate_text_with_system(
            system_instruction=RECAP_SYSTEM_INSTRUCTION,
            user_content=user_message,
            model=settings.gemini_model,
        ).strip()
        if content and len(content) >= 20:
            for prefix in ("Summary:", "Notes:", "Key points:", "KEY POINTS:", "Here are the key points:", "Bullet summary:"):
                if content.lower().startswith(prefix.lower()):
                    content = content[len(prefix) :].strip()
            content = _clean_summary_text(content)
            key_points = _parse_bullet_list(content)
            if not key_points:
                key_points = [line.strip() for line in content.splitlines() if line.strip() and len(line.strip()) > 10]
            if key_points:
                return RecapResponse(summary=content, key_points=key_points, evidence=[])
    except GeminiQuotaExceeded:
        logger.warning("Gemini rate limit for recap, using local summarizer")
    except Exception as e:
        logger.warning(f"Gemini recap failed, using local summarizer: {e}")

    # 3) Local summarizer fallback — no API, always works
    summary, key_points = local_recap_from_chunks(all_chunks)
    return RecapResponse(summary=summary, key_points=key_points, evidence=[])
