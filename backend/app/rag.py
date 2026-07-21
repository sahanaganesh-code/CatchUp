from typing import List, Dict, Any, Optional
from app.config import settings
from app.models import Evidence, QuestionResponse, RecapResponse
from app.store import vector_store
from app.gemini_client import generate_text
import logging
import re

logger = logging.getLogger(__name__)

TIME_WINDOW_DETECTION_PROMPT = """Determine if this question is asking about a RECENT TIME WINDOW of a meeting/lecture (e.g. "what happened in the last 10 minutes", "what did I miss", "recently", "just now", "since I stepped away", "catch me up") as opposed to a question about a specific topic, person, or decision.

Question: "{question}"

If it IS a time-window question, respond with ONLY the number of minutes that window should cover (your best estimate - explicit numbers like "last 10 minutes" use that exact number; vague phrasing like "what did I miss" or "recently" defaults to 5; "just now" or "in the last minute" defaults to 2).

If it is NOT a time-window question, respond with exactly: NONE

Respond with ONLY the number or NONE, nothing else."""

# System instruction for meeting analysis
MEETING_ANALYSIS_SYSTEM_INSTRUCTION = """You are an expert meeting analyst.
Your role is to provide accurate, evidence-based answers about meeting content. You excel at:
- Identifying key decisions and action items
- Tracking participant contributions
- Summarizing technical discussions
- Extracting deadlines and commitments
Always ground your responses in the provided evidence."""


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


def _timestamp_to_seconds(timestamp: str) -> int:
    """Convert an HH:MM:SS timestamp string to total elapsed seconds."""
    h, m, s = (int(p) for p in timestamp.split(":"))
    return h * 3600 + m * 60 + s


def _sample_evenly(chunks: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    """Pick n chunks evenly spaced across the list, so evidence represents the
    whole span rather than just its earliest moments."""
    if len(chunks) <= n:
        return chunks
    step = len(chunks) / n
    return [chunks[int(i * step)] for i in range(n)]


def detect_time_window_minutes(question: str) -> Optional[int]:
    """
    Ask Gemini whether this question is asking about a recent time window
    (e.g. "what happened in the last 10 minutes") rather than a topic. Returns
    the window size in minutes, or None if this isn't a time-relative question.
    """
    try:
        response = generate_text(
            TIME_WINDOW_DETECTION_PROMPT.format(question=question),
            temperature=0.0,
        ).strip()
        if response.upper() == "NONE":
            return None
        return int(response)
    except Exception as e:
        logger.warning(f"Time window detection failed, falling back to semantic search: {e}")
        return None


def get_recent_chunks(session_id: str, minutes: int) -> List[Dict[str, Any]]:
    """
    Get all chunks within the last N minutes, relative to the most recently
    transcribed moment (chunk timestamps are elapsed session time, not wall
    clock) - in chronological order, not similarity-ranked.
    """
    all_chunks = vector_store.get_all_chunks(session_id)
    if not all_chunks:
        return []
    latest_seconds = _timestamp_to_seconds(all_chunks[-1]["timestamp"])
    cutoff_seconds = max(0, latest_seconds - minutes * 60)
    return [c for c in all_chunks if _timestamp_to_seconds(c["timestamp"]) >= cutoff_seconds]


def format_evidence_for_prompt(evidence: List[Evidence]) -> str:
    """Format evidence for LLM prompt."""
    formatted = []
    for i, ev in enumerate(evidence, 1):
        speaker_prefix = f"[{ev.speaker}] " if ev.speaker else ""
        formatted.append(f"{i}. [{ev.timestamp}] {speaker_prefix}\"{ev.quote}\"")
    return "\n".join(formatted)


def answer_question(session_id: str, question: str) -> QuestionResponse:
    """
    Answer a question with evidence-based grounding.
    HARD RULE: Must return 2-5 evidence quotes or say insufficient evidence.
    """
    logger.info(f"Answering question for session {session_id}: {question}")

    # Time-relative questions ("what happened in the last 10 minutes") don't
    # match well semantically - no chunk's content is "about" recency - so
    # they need chronological retrieval instead of similarity search.
    time_window_minutes = detect_time_window_minutes(question)

    if time_window_minutes is not None:
        chunks = get_recent_chunks(session_id, time_window_minutes)
        logger.info(
            f"Time-relative question detected (last {time_window_minutes} min): "
            f"{len(chunks)} chunks in window for session {session_id}"
        )
    else:
        chunks = vector_store.query_chunks(session_id, question, top_k=settings.retrieval_top_k)

    if not chunks or len(chunks) < settings.min_evidence_quotes:
        logger.warning(f"Insufficient evidence for question in session {session_id}")
        return QuestionResponse(
            answer="Insufficient evidence in the transcript to answer this question.",
            evidence=[],
            has_sufficient_evidence=False
        )

    # For time-window questions, sample evidence evenly across the window so
    # the displayed quotes represent the whole span, not just its earliest
    # moments (chunks here are chronological, not similarity-ranked).
    if time_window_minutes is not None:
        evidence = extract_evidence_from_chunks(_sample_evenly(chunks, settings.max_evidence_quotes))
    else:
        evidence = extract_evidence_from_chunks(chunks)

    # Ensure we have 2-5 evidence quotes
    if len(evidence) < settings.min_evidence_quotes:
        return QuestionResponse(
            answer="Insufficient evidence in the transcript to answer this question.",
            evidence=evidence,
            has_sufficient_evidence=False
        )

    evidence = evidence[:settings.max_evidence_quotes]

    # For time-window questions, the model needs the FULL window (not just
    # the capped evidence quotes) to narrate what actually happened - the
    # evidence list above is only a representative sample for display.
    if time_window_minutes is not None:
        full_context = "\n".join(
            f"[{c['timestamp']}] {c.get('speaker', 'Speaker')}: {c['text']}" for c in chunks
        )
        prompt = f"""You are analyzing a meeting transcript to summarize a recent time window.

Question: {question}

Full transcript of the last {time_window_minutes} minute(s):
{full_context}

Instructions:
1. Summarize what happened during this time window, using ONLY the transcript above
2. Reference specific timestamps (e.g., "At [00:05:23]...") when making points
3. If multiple speakers were involved, note who said/did what
4. Be concise, direct, and professional

Provide a clear, evidence-based summary:"""
    else:
        evidence_text = format_evidence_for_prompt(evidence)
        prompt = f"""You are analyzing a meeting transcript to answer a specific question.

Question: {question}

Evidence from the transcript:
{evidence_text}

Instructions:
1. Answer the question using ONLY the information in the evidence above
2. Reference specific timestamps (e.g., "At [00:05:23]...") when making points
3. If multiple speakers discussed the topic, acknowledge different perspectives
4. If the evidence doesn't fully answer the question, clearly state what information is missing
5. Be concise, direct, and professional
6. For action items or decisions, be explicit about who is responsible (if mentioned)

Provide a clear, evidence-based answer:"""

    try:
        answer = generate_text(
            prompt,
            model=settings.gemini_model,
            temperature=0.2,  # Lower temperature for more factual responses
            system_instruction=MEETING_ANALYSIS_SYSTEM_INSTRUCTION
        ).strip()

        return QuestionResponse(
            answer=answer,
            evidence=evidence,
            has_sufficient_evidence=True
        )

    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        return QuestionResponse(
            answer=f"Error generating answer: {str(e)}",
            evidence=evidence,
            has_sufficient_evidence=False
        )


def generate_recap(session_id: str) -> RecapResponse:
    """
    Generate a meeting recap with evidence.
    HARD RULE: Must include evidence quotes.
    """
    logger.info(f"Generating recap for session {session_id}")
    
    # Get all chunks for the session
    all_chunks = vector_store.get_all_chunks(session_id)
    
    if not all_chunks:
        return RecapResponse(
            summary="No transcript data available for this session.",
            key_points=[],
            evidence=[]
        )
    
    # Sample chunks for evidence (beginning, middle, end)
    evidence_indices = []
    if len(all_chunks) >= 3:
        evidence_indices = [0, len(all_chunks) // 2, len(all_chunks) - 1]
    else:
        evidence_indices = list(range(len(all_chunks)))
    
    evidence = [
        Evidence(
            timestamp=all_chunks[i]["timestamp"],
            quote=all_chunks[i]["text"][:200],
            speaker=all_chunks[i].get("speaker")
        )
        for i in evidence_indices
    ]
    
    # Add more evidence to meet minimum requirement
    for chunk in all_chunks:
        if len(evidence) >= settings.max_evidence_quotes:
            break
        if chunk not in [all_chunks[i] for i in evidence_indices]:
            evidence.append(Evidence(
                timestamp=chunk["timestamp"],
                quote=chunk["text"][:200],
                speaker=chunk.get("speaker")
            ))
    
    # Build context from all chunks
    context = "\n\n".join([
        f"[{chunk['timestamp']}] {chunk.get('speaker', 'Speaker')}: {chunk['text']}"
        for chunk in all_chunks[:20]  # Limit context size
    ])
    
    prompt = f"""Analyze this meeting transcript and create a comprehensive meeting recap.

Meeting Transcript:
{context}

Generate a professional meeting recap with:

1. SUMMARY (2-3 sentences):
   - What was the main purpose/topic of the meeting?
   - What was the overall outcome or conclusion?

2. KEY POINTS (3-5 bullet points):
   - Major topics discussed
   - Important decisions made
   - Action items identified
   - Key concerns or blockers raised
   - Notable insights or recommendations

Format your response EXACTLY as:
SUMMARY: <your summary here>

KEY POINTS:
- <point 1>
- <point 2>
- <point 3>
- <point 4>
- <point 5>

Focus on actionable information and concrete outcomes. Be specific and professional."""
    
    try:
        content = generate_text(
            prompt, 
            model=settings.gemini_model,
            temperature=0.3,  # Balanced temperature for summaries
            system_instruction=MEETING_ANALYSIS_SYSTEM_INSTRUCTION
        ).strip()
        
        # Parse response
        summary_match = re.search(r"SUMMARY:\s*(.+?)(?=KEY POINTS:|$)", content, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else content
        
        key_points = []
        key_points_match = re.search(r"KEY POINTS:\s*(.+)", content, re.DOTALL)
        if key_points_match:
            points_text = key_points_match.group(1).strip()
            key_points = [
                line.strip().lstrip("-•*").strip()
                for line in points_text.split("\n")
                if line.strip() and line.strip().startswith(("-", "•", "*"))
            ]
        
        return RecapResponse(
            summary=summary,
            key_points=key_points,
            evidence=evidence[:settings.max_evidence_quotes]
        )
    
    except Exception as e:
        logger.error(f"Error generating recap: {e}")
        return RecapResponse(
            summary=f"Error generating recap: {str(e)}",
            key_points=[],
            evidence=evidence
        )
