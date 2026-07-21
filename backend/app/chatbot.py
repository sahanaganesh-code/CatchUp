"""
AI Chatbot that can answer questions about all content:
meeting transcripts, notes, todos, and calendar events.
"""
from typing import List
from app.models import ChatbotResponse, Evidence
from app.store import vector_store
from app.content_manager import notes_store, todos_store, events_store
from app.gemini_client import generate_text
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# System instruction for the workspace-aware chatbot
WORKSPACE_CHATBOT_SYSTEM_INSTRUCTION = """You are an intelligent assistant specializing in meeting analysis.
You help users by:
- Answering questions about meeting transcripts
- Tracking action items and todos
- Managing calendar events and schedules
- Organizing meeting notes
- Providing context-aware insights across all meeting content

Always provide evidence-based answers with specific references."""


def build_context_from_all_content(question: str, context_types: List[str]) -> tuple[str, List[Evidence]]:
    """
    Build context from all available content types.
    Returns (context_text, evidence_list)
    """
    context_parts = []
    all_evidence = []
    
    # Search meeting transcripts
    if "transcripts" in context_types:
        # Get all sessions and search across them
        # For MVP, we'll search recent chunks
        # In production, maintain a session index
        try:
            # This is a simplified approach - in production, track all session IDs
            logger.info("Searching meeting transcripts...")
            context_parts.append("=== MEETING TRANSCRIPTS ===")
            # For now, we'll note this limitation
            context_parts.append("(Full transcript search requires session_id - use Q&A panel for a specific session)")
        except Exception as e:
            logger.error(f"Error searching transcripts: {e}")
    
    # Search notes
    if "notes" in context_types:
        logger.info("Searching notes...")
        context_parts.append("\n=== NOTES ===")
        for note in list(notes_store.values())[:10]:  # Limit to recent notes
            context_parts.append(f"\nTitle: {note.title} (Date: {note.date})")
            context_parts.append(f"Content: {note.content[:300]}")
            # Add as evidence
            all_evidence.append(Evidence(
                timestamp=note.date,
                quote=f"Note: {note.title} - {note.content[:150]}",
                speaker="User Note"
            ))
    
    # Search todos
    if "todos" in context_types:
        logger.info("Searching todos...")
        context_parts.append("\n=== TODO ITEMS ===")
        for todo in list(todos_store.values())[:10]:
            status = "✓ Completed" if todo.completed else "○ Pending"
            context_parts.append(f"\n{status}: {todo.title}")
            context_parts.append(f"Description: {todo.description}")
            if todo.due_date:
                context_parts.append(f"Due: {todo.due_date}")
            # Add as evidence
            all_evidence.append(Evidence(
                timestamp=todo.due_date or "No date",
                quote=f"Todo: {todo.title} - {todo.description[:150]}",
                speaker="Todo List"
            ))
    
    # Search Google Calendar events
    if "events" in context_types:
        logger.info("Searching Google Calendar events...")
        context_parts.append("\n=== GOOGLE CALENDAR EVENTS ===")
        for event in list(events_store.values())[:10]:
            context_parts.append(f"\nEvent: {event.title}")
            context_parts.append(f"Description: {event.description}")
            if event.date:
                context_parts.append(f"Date: {event.date}")
            if event.time:
                context_parts.append(f"Time: {event.time}")
            if event.duration_minutes:
                context_parts.append(f"Duration: {event.duration_minutes} minutes")
            # Add as evidence
            all_evidence.append(Evidence(
                timestamp=f"{event.date} {event.time}" if event.date and event.time else event.date or "No date",
                quote=f"Calendar Event: {event.title} - {event.description[:150]}",
                speaker="Google Calendar"
            ))
    
    context_text = "\n".join(context_parts)
    return context_text, all_evidence


def chat_with_content(question: str, context_types: List[str]) -> ChatbotResponse:
    """
    Answer questions about all content (transcripts, notes, todos, events).
    HARD RULE: Must include evidence quotes.
    """
    logger.info(f"Chatbot question: {question}")
    logger.info(f"Context types: {context_types}")
    
    # Build context from all content
    context_text, all_evidence = build_context_from_all_content(question, context_types)
    
    if not context_text or len(all_evidence) < settings.min_evidence_quotes:
        logger.warning("Insufficient content for chatbot question")
        return ChatbotResponse(
            answer="Insufficient content available to answer this question. Please add notes, todos, or calendar events first.",
            evidence=[],
            sources=[],
            has_sufficient_evidence=False
        )
    
    # Limit evidence to 2-5 quotes
    evidence = all_evidence[:settings.max_evidence_quotes]
    
    # Format evidence for prompt
    evidence_text = "\n".join([
        f"{i+1}. [{ev.timestamp}] ({ev.speaker}) \"{ev.quote}\""
        for i, ev in enumerate(evidence)
    ])
    
    prompt = f"""You are answering a question about meeting content.

Question: {question}

Available Content:
{context_text}

Evidence:
{evidence_text}

Instructions:
1. Answer the question using ONLY the information in the evidence above
2. Reference specific dates, times, and sources (e.g., "According to the meeting transcript...", "In the calendar event...")
3. For action items, mention assignees and deadlines if available
4. For calendar events, include date, time, and duration details
5. If the evidence doesn't fully answer the question, clearly state what information is missing
6. Be helpful, concise, and professional
7. If relevant, suggest how the user might find more information (e.g., "Check the full transcript for session X")

Provide a comprehensive, evidence-based answer:"""
    
    try:
        answer = generate_text(
            prompt, 
            model=settings.gemini_model,
            temperature=0.4,  # Slightly higher for conversational responses
            system_instruction=WORKSPACE_CHATBOT_SYSTEM_INSTRUCTION
        ).strip()
        
        # Determine which sources were used
        sources = []
        if "notes" in context_types and any(n for n in notes_store.values()):
            sources.append("notes")
        if "todos" in context_types and any(t for t in todos_store.values()):
            sources.append("todos")
        if "events" in context_types and any(e for e in events_store.values()):
            sources.append("events")
        if "transcripts" in context_types:
            sources.append("transcripts")
        
        return ChatbotResponse(
            answer=answer,
            evidence=evidence,
            sources=sources,
            has_sufficient_evidence=True
        )
    
    except Exception as e:
        logger.error(f"Error in chatbot: {e}")
        return ChatbotResponse(
            answer=f"Error generating answer: {str(e)}",
            evidence=evidence,
            sources=[],
            has_sufficient_evidence=False
        )
