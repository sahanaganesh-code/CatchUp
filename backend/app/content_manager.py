"""
Content manager for notes, todos, and calendar events.
Optimized for meeting transcripts and calendar integration.
Persisted in Postgres (see app/db.py).
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select
from app.models import Note, TodoItem, CalendarEvent, Evidence
from app.db import SessionLocal, NoteRow, TodoRow, CalendarEventRow, SessionRecord
from app.store import vector_store
from app.gemini_client import generate_text
from app.config import settings
import uuid
import logging
import json

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


def _reference_date_str(session_id: str) -> str:
    """
    Transcripts only contain relative day references ("let's meet Thursday",
    "next week") with no anchor - the LLM has no idea what day the meeting
    actually happened on. Use the session's creation date as "today" so
    relative dates resolve to real calendar dates instead of guesses.
    """
    with SessionLocal() as db:
        session_row = db.get(SessionRecord, session_id)
    reference_date = session_row.created_at if session_row else datetime.utcnow()
    return reference_date.strftime("%A, %Y-%m-%d")


def _note_to_model(row: NoteRow) -> Note:
    return Note(
        note_id=row.id, session_id=row.session_id, title=row.title,
        content=row.content, date=row.date, created_at=row.created_at, updated_at=row.updated_at,
    )


def _todo_to_model(row: TodoRow) -> TodoItem:
    return TodoItem(
        todo_id=row.id, session_id=row.session_id, title=row.title, description=row.description,
        priority=row.priority, due_date=row.due_date,
        evidence=[Evidence(**e) for e in row.evidence], completed=row.completed, created_at=row.created_at,
    )


def _event_to_model(row: CalendarEventRow) -> CalendarEvent:
    return CalendarEvent(
        event_id=row.id, session_id=row.session_id, title=row.title, description=row.description,
        date=row.date, time=row.time, duration_minutes=row.duration_minutes,
        evidence=[Evidence(**e) for e in row.evidence], created_at=row.created_at,
    )


def create_note(session_id: str, title: str, content: str, date: str) -> Note:
    """Create a new note."""
    with SessionLocal() as db:
        row = NoteRow(id=str(uuid.uuid4()), session_id=session_id, title=title, content=content, date=date)
        db.add(row)
        db.commit()
        db.refresh(row)
        logger.info(f"Created note {row.id}: {title}")
        return _note_to_model(row)


def get_note(note_id: str) -> Optional[Note]:
    """Get a note by ID."""
    with SessionLocal() as db:
        row = db.get(NoteRow, note_id)
        return _note_to_model(row) if row else None


def list_notes(session_id: str = None) -> List[Note]:
    """List all notes, optionally filtered by session."""
    with SessionLocal() as db:
        query = select(NoteRow)
        if session_id:
            query = query.where(NoteRow.session_id == session_id)
        rows = db.execute(query).scalars().all()
        return [_note_to_model(r) for r in rows]


def update_note(note_id: str, title: str = None, content: str = None) -> Optional[Note]:
    """Update a note."""
    with SessionLocal() as db:
        row = db.get(NoteRow, note_id)
        if not row:
            return None
        if title:
            row.title = title
        if content:
            row.content = content
        row.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(row)
        logger.info(f"Updated note {note_id}")
        return _note_to_model(row)


def delete_note(note_id: str) -> bool:
    """Delete a note."""
    with SessionLocal() as db:
        row = db.get(NoteRow, note_id)
        if not row:
            return False
        db.delete(row)
        db.commit()
        logger.info(f"Deleted note {note_id}")
        return True


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

    reference_date = _reference_date_str(session_id)

    prompt = f"""Analyze this meeting transcript and extract TODO items.

Today's date (the date this meeting is taking place) is {reference_date}. Use this
as the reference point when resolving any relative date mentioned in the
transcript (e.g. "by Thursday", "next week", "tomorrow", "end of the month").

Meeting Transcript:
{context}

For each actionable todo item, extract:
1. **Title**: Brief, actionable task description (start with verb)
2. **Description**: Detailed explanation including context and owner if mentioned
3. **Priority**: Assess urgency/importance as "low", "medium", or "high"
4. **Due Date**: Extract or infer deadline (format: YYYY-MM-DD), resolved against today's date above
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
        with SessionLocal() as db:
            for todo_data in todos_data:
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

                evidence = evidence[:settings.max_evidence_quotes]
                row = TodoRow(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    title=todo_data["title"],
                    description=todo_data["description"],
                    priority=todo_data.get("priority", "medium"),
                    due_date=todo_data.get("due_date"),
                    evidence=[e.model_dump() for e in evidence],
                )
                db.add(row)
                db.flush()
                todos.append(_todo_to_model(row))
            db.commit()

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

    reference_date = _reference_date_str(session_id)

    prompt = f"""Analyze this meeting transcript and extract calendar events for Google Calendar.

Today's date (the date this meeting is taking place) is {reference_date}. Use this
as the reference point when resolving any relative date mentioned in the
transcript - e.g. if today is Tuesday 2026-07-21 and someone says "let's meet
Thursday", that resolves to 2026-07-23 (the NEXT occurrence of that weekday,
not a past one).

Meeting Transcript:
{context}

For each mentioned meeting or event, extract:
1. **Title**: Meeting/event name (clear and descriptive)
2. **Description**: Purpose, agenda, attendees, or notes
3. **Date**: Event date (format: YYYY-MM-DD), resolved against today's date above
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
        with SessionLocal() as db:
            for event_data in events_data:
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

                evidence = evidence[:settings.max_evidence_quotes]
                row = CalendarEventRow(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    title=event_data["title"],
                    description=event_data["description"],
                    date=event_data.get("date"),
                    time=event_data.get("time"),
                    duration_minutes=event_data.get("duration_minutes"),
                    evidence=[e.model_dump() for e in evidence],
                )
                db.add(row)
                db.flush()
                events.append(_event_to_model(row))
            db.commit()

        logger.info(f"Extracted {len(events)} calendar events for session {session_id}")
        return events

    except Exception as e:
        logger.error(f"Error extracting calendar events: {e}")
        return []


def get_todo(todo_id: str) -> Optional[TodoItem]:
    """Get a todo by ID."""
    with SessionLocal() as db:
        row = db.get(TodoRow, todo_id)
        return _todo_to_model(row) if row else None


def list_todos(session_id: str = None) -> List[TodoItem]:
    """List all todos, optionally filtered by session."""
    with SessionLocal() as db:
        query = select(TodoRow)
        if session_id:
            query = query.where(TodoRow.session_id == session_id)
        rows = db.execute(query).scalars().all()
        return [_todo_to_model(r) for r in rows]


def update_todo(
    todo_id: str,
    title: str = None,
    description: str = None,
    priority: str = None,
    due_date: str = None,
) -> Optional[TodoItem]:
    """Update a todo's fields."""
    with SessionLocal() as db:
        row = db.get(TodoRow, todo_id)
        if not row:
            return None
        if title is not None:
            row.title = title
        if description is not None:
            row.description = description
        if priority is not None:
            row.priority = priority
        if due_date is not None:
            row.due_date = due_date
        db.commit()
        db.refresh(row)
        logger.info(f"Updated todo {todo_id}")
        return _todo_to_model(row)


def complete_todo(todo_id: str, completed: bool) -> Optional[TodoItem]:
    """Mark a todo as completed."""
    with SessionLocal() as db:
        row = db.get(TodoRow, todo_id)
        if not row:
            return None
        row.completed = completed
        db.commit()
        db.refresh(row)
        logger.info(f"Todo {todo_id} completed={completed}")
        return _todo_to_model(row)


def get_event(event_id: str) -> Optional[CalendarEvent]:
    """Get a calendar event by ID."""
    with SessionLocal() as db:
        row = db.get(CalendarEventRow, event_id)
        return _event_to_model(row) if row else None


def list_events(session_id: str = None) -> List[CalendarEvent]:
    """List all calendar events, optionally filtered by session."""
    with SessionLocal() as db:
        query = select(CalendarEventRow)
        if session_id:
            query = query.where(CalendarEventRow.session_id == session_id)
        rows = db.execute(query).scalars().all()
        return [_event_to_model(r) for r in rows]


def update_event(
    event_id: str,
    title: str = None,
    description: str = None,
    date: str = None,
    time: str = None,
    duration_minutes: int = None,
) -> Optional[CalendarEvent]:
    """Update a calendar event's fields."""
    with SessionLocal() as db:
        row = db.get(CalendarEventRow, event_id)
        if not row:
            return None
        if title is not None:
            row.title = title
        if description is not None:
            row.description = description
        if date is not None:
            row.date = date
        if time is not None:
            row.time = time
        if duration_minutes is not None:
            row.duration_minutes = duration_minutes
        db.commit()
        db.refresh(row)
        logger.info(f"Updated event {event_id}")
        return _event_to_model(row)


def delete_todo(todo_id: str) -> bool:
    """Delete a todo."""
    with SessionLocal() as db:
        row = db.get(TodoRow, todo_id)
        if not row:
            return False
        db.delete(row)
        db.commit()
        return True


def delete_event(event_id: str) -> bool:
    """Delete a calendar event."""
    with SessionLocal() as db:
        row = db.get(CalendarEventRow, event_id)
        if not row:
            return False
        db.delete(row)
        db.commit()
        return True
