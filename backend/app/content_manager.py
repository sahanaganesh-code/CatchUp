"""
Content manager for notes, todos, and calendar events.
Optimized for meeting transcripts and Google Calendar integration.
In production, these would be stored in a database and synced with Google Workspace.
"""
from typing import List, Dict, Optional
from datetime import datetime
from app.models import Note, TodoItem, CalendarEvent, Evidence
from app.store import vector_store
from app.gemini_client import generate_text, generate_structured_output
from app.config import settings
import uuid
import logging
import json
import re

logger = logging.getLogger(__name__)

# System instruction for content extraction
CONTENT_EXTRACTION_SYSTEM_INSTRUCTION = """You are an expert at analyzing meeting transcripts and extracting structured information.
You excel at:
- Identifying actionable tasks and their owners
- Detecting meeting scheduling discussions
- Recognizing deadlines and time commitments
- Understanding context and implicit action items
- Extracting Google Calendar-compatible event details
Always provide precise, actionable information with supporting evidence."""

# In-memory stores (in production, use PostgreSQL)
notes_store: Dict[str, Note] = {}
todos_store: Dict[str, TodoItem] = {}
events_store: Dict[str, CalendarEvent] = {}


def create_note(session_id: str, title: str, content: str, date: str) -> Note:
    """Create a new note."""
    note_id = str(uuid.uuid4())
    note = Note(
        note_id=note_id,
        session_id=session_id,
        title=title,
        content=content,
        date=date
    )
    notes_store[note_id] = note
    logger.info(f"Created note {note_id}: {title}")
    return note


def get_note(note_id: str) -> Optional[Note]:
    """Get a note by ID."""
    return notes_store.get(note_id)


def list_notes(session_id: str = None) -> List[Note]:
    """List all notes, optionally filtered by session."""
    if session_id:
        return [n for n in notes_store.values() if n.session_id == session_id]
    return list(notes_store.values())


def update_note(note_id: str, title: str = None, content: str = None) -> Optional[Note]:
    """Update a note."""
    if note_id not in notes_store:
        return None
    
    note = notes_store[note_id]
    if title:
        note.title = title
    if content:
        note.content = content
    note.updated_at = datetime.utcnow()
    
    logger.info(f"Updated note {note_id}")
    return note


def delete_note(note_id: str) -> bool:
    """Delete a note."""
    if note_id in notes_store:
        del notes_store[note_id]
        logger.info(f"Deleted note {note_id}")
        return True
    return False


def generate_todos_from_meeting(session_id: str) -> List[TodoItem]:
    """
    Auto-generate todo list from meeting transcript.
    Extracts action items with dates and priorities.
    """
    logger.info(f"Generating todos for session {session_id}")
    
    all_chunks = vector_store.get_all_chunks(session_id)
    if not all_chunks:
        return []
    
    context = "\n\n".join([
        f"[{chunk['timestamp']}] {chunk.get('speaker', 'Speaker')}: {chunk['text']}"
        for chunk in all_chunks[:30]
    ])
    
    prompt = f"""Analyze this meeting transcript and extract TODO items.

Meeting Transcript:
{context}

For each actionable todo item, extract:
1. **Title**: Brief, actionable task description (start with verb)
2. **Description**: Detailed explanation including context and owner if mentioned
3. **Priority**: Assess urgency/importance as "low", "medium", or "high"
4. **Due Date**: Extract or infer deadline (format: YYYY-MM-DD)
5. **Timestamps**: Relevant timestamps where this task was discussed

Guidelines:
- Only include concrete, actionable tasks (not general discussions)
- Look for phrases like "we need to", "action item", "follow up", "by [date]"
- If someone is assigned, include their name in the description
- Prioritize based on urgency words (ASAP, urgent, by EOD = high)
- Include both explicit and implicit action items

Provide response as a JSON array:
[
  {{
    "title": "Complete project proposal",
    "description": "Write and submit the Q2 project proposal. Assigned to: Sarah",
    "priority": "high",
    "due_date": "2024-03-15",
    "timestamps": ["00:01:20", "00:02:30"]
  }}
]"""
    
    try:
        content = generate_text(
            prompt, 
            model=settings.gemini_model,
            temperature=0.2,  # Low temperature for precise extraction
            system_instruction=CONTENT_EXTRACTION_SYSTEM_INSTRUCTION
        ).strip()
        
        # Extract JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        todos_data = json.loads(content)
        
        todos = []
        for todo_data in todos_data:
            todo_id = str(uuid.uuid4())
            
            # Find evidence
            evidence = []
            for ts in todo_data.get("timestamps", [])[:settings.max_evidence_quotes]:
                matching = [c for c in all_chunks if c["timestamp"] == ts]
                if matching:
                    evidence.append(Evidence(
                        timestamp=matching[0]["timestamp"],
                        quote=matching[0]["text"][:200],
                        speaker=matching[0].get("speaker")
                    ))
            
            # Ensure minimum evidence
            if len(evidence) < settings.min_evidence_quotes:
                for chunk in all_chunks[:settings.max_evidence_quotes]:
                    if len(evidence) >= settings.max_evidence_quotes:
                        break
                    evidence.append(Evidence(
                        timestamp=chunk["timestamp"],
                        quote=chunk["text"][:200],
                        speaker=chunk.get("speaker")
                    ))
            
            todo = TodoItem(
                todo_id=todo_id,
                title=todo_data["title"],
                description=todo_data["description"],
                priority=todo_data.get("priority", "medium"),
                due_date=todo_data.get("due_date"),
                evidence=evidence[:settings.max_evidence_quotes]
            )
            
            todos_store[todo_id] = todo
            todos.append(todo)
        
        logger.info(f"Generated {len(todos)} todos for session {session_id}")
        return todos
    
    except Exception as e:
        logger.error(f"Error generating todos: {e}")
        return []


def generate_calendar_events(session_id: str) -> List[CalendarEvent]:
    """
    Extract calendar events from meeting transcript.
    Looks for dates, times, and meeting mentions.
    """
    logger.info(f"Extracting calendar events for session {session_id}")
    
    all_chunks = vector_store.get_all_chunks(session_id)
    if not all_chunks:
        return []
    
    context = "\n\n".join([
        f"[{chunk['timestamp']}] {chunk.get('speaker', 'Speaker')}: {chunk['text']}"
        for chunk in all_chunks[:30]
    ])
    
    prompt = f"""Analyze this meeting transcript and extract calendar events for Google Calendar.

Meeting Transcript:
{context}

For each mentioned meeting or event, extract:
1. **Title**: Meeting/event name (clear and descriptive)
2. **Description**: Purpose, agenda, attendees, or notes
3. **Date**: Event date (format: YYYY-MM-DD)
4. **Time**: Start time (format: HH:MM in 24-hour format)
5. **Duration**: Length in minutes (default to 60 if not specified)
6. **Timestamps**: Where in the transcript this was discussed

Guidelines for Google Calendar compatibility:
- Look for scheduling discussions: "let's meet", "schedule", "next week", "tomorrow"
- Extract both explicit dates/times and relative references (e.g., "next Monday at 2pm")
- Include recurring meeting mentions (e.g., "weekly standup")
- Note if it's a follow-up meeting or new event
- Include participant names if mentioned
- For time zones, assume meeting timezone unless specified

Provide response as a JSON array:
[
  {{
    "title": "Project kickoff meeting",
    "description": "Q2 project kickoff with stakeholders. Attendees: Sarah, John, Team leads",
    "date": "2024-03-20",
    "time": "14:00",
    "duration_minutes": 60,
    "timestamps": ["00:01:45", "00:02:10"]
  }}
]

Only include meetings/events that have at least a date or time reference."""
    
    try:
        content = generate_text(
            prompt, 
            model=settings.gemini_model,
            temperature=0.2,  # Low temperature for precise extraction
            system_instruction=CONTENT_EXTRACTION_SYSTEM_INSTRUCTION
        ).strip()
        
        # Extract JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        events_data = json.loads(content)
        
        events = []
        for event_data in events_data:
            event_id = str(uuid.uuid4())
            
            # Find evidence
            evidence = []
            for ts in event_data.get("timestamps", [])[:settings.max_evidence_quotes]:
                matching = [c for c in all_chunks if c["timestamp"] == ts]
                if matching:
                    evidence.append(Evidence(
                        timestamp=matching[0]["timestamp"],
                        quote=matching[0]["text"][:200],
                        speaker=matching[0].get("speaker")
                    ))
            
            # Ensure minimum evidence
            if len(evidence) < settings.min_evidence_quotes:
                for chunk in all_chunks[:settings.max_evidence_quotes]:
                    if len(evidence) >= settings.max_evidence_quotes:
                        break
                    evidence.append(Evidence(
                        timestamp=chunk["timestamp"],
                        quote=chunk["text"][:200],
                        speaker=chunk.get("speaker")
                    ))
            
            event = CalendarEvent(
                event_id=event_id,
                title=event_data["title"],
                description=event_data["description"],
                date=event_data.get("date"),
                time=event_data.get("time"),
                duration_minutes=event_data.get("duration_minutes"),
                evidence=evidence[:settings.max_evidence_quotes]
            )
            
            events_store[event_id] = event
            events.append(event)
        
        logger.info(f"Extracted {len(events)} calendar events for session {session_id}")
        return events
    
    except Exception as e:
        logger.error(f"Error extracting calendar events: {e}")
        return []


def get_todo(todo_id: str) -> Optional[TodoItem]:
    """Get a todo by ID."""
    return todos_store.get(todo_id)


def list_todos(session_id: str = None) -> List[TodoItem]:
    """List all todos."""
    return list(todos_store.values())


def complete_todo(todo_id: str, completed: bool) -> Optional[TodoItem]:
    """Mark a todo as completed."""
    if todo_id in todos_store:
        todos_store[todo_id].completed = completed
        logger.info(f"Todo {todo_id} completed={completed}")
        return todos_store[todo_id]
    return None


def get_event(event_id: str) -> Optional[CalendarEvent]:
    """Get a calendar event by ID."""
    return events_store.get(event_id)


def list_events(session_id: str = None) -> List[CalendarEvent]:
    """List all calendar events."""
    return list(events_store.values())


def delete_todo(todo_id: str) -> bool:
    """Delete a todo."""
    if todo_id in todos_store:
        del todos_store[todo_id]
        return True
    return False


def delete_event(event_id: str) -> bool:
    """Delete a calendar event."""
    if event_id in events_store:
        del events_store[event_id]
        return True
    return False
