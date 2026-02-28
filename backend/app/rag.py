from typing import List, Dict, Any
from app.config import settings
from app.models import Evidence, QuestionResponse, RecapResponse
from app.store import vector_store
from app.gemini_client import generate_text
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


def answer_question(session_id: str, question: str) -> QuestionResponse:
    """
    Answer a question with evidence-based grounding.
    HARD RULE: Must return 2-5 evidence quotes or say insufficient evidence.
    """
    logger.info(f"Answering question for session {session_id}: {question}")
    
    # Retrieve relevant chunks
    chunks = vector_store.query_chunks(session_id, question, top_k=settings.retrieval_top_k)
    
    if not chunks or len(chunks) < settings.min_evidence_quotes:
        logger.warning(f"Insufficient evidence for question in session {session_id}")
        return QuestionResponse(
            answer="Insufficient evidence in the transcript to answer this question.",
            evidence=[],
            has_sufficient_evidence=False
        )
    
    # Extract evidence
    evidence = extract_evidence_from_chunks(chunks)
    
    # Ensure we have 2-5 evidence quotes
    if len(evidence) < settings.min_evidence_quotes:
        return QuestionResponse(
            answer="Insufficient evidence in the transcript to answer this question.",
            evidence=evidence,
            has_sufficient_evidence=False
        )
    
    evidence = evidence[:settings.max_evidence_quotes]
    
    # Build prompt with evidence
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
    
    prompt = f"""Summarize this meeting transcript. Provide:
1. A brief summary (2-3 sentences)
2. 3-5 key points discussed

Transcript:
{context}

Format your response as:
SUMMARY: <summary>
KEY POINTS:
- <point 1>
- <point 2>
- <point 3>
"""
    
    try:
        content = generate_text(prompt, model=settings.gemini_model).strip()
        
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
