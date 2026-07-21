from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from app.models import (
    IngestTranscriptRequest,
    QuestionRequest,
    QuestionResponse,
    RecapRequest,
    RecapResponse,
    SessionIdRequest,
    CreateNoteRequest,
    UpdateNoteRequest,
    UpdateEventRequest,
    UpdateTodoRequest,
    Note,
    TodoItem,
    CalendarEvent,
    GetTranscriptRequest,
    TranscriptResponse,
    ChatbotRequest,
    ChatbotResponse,
    CreateSessionRequest,
)
from app.rag import answer_question, generate_recap
from app.stt import process_audio_upload
from app.store import vector_store
from app.config import settings
from app.content_manager import (
    create_note, get_note, list_notes, update_note, delete_note,
    generate_todos_from_meeting, list_todos, get_todo, complete_todo, update_todo, delete_todo,
    generate_calendar_events, list_events, get_event, update_event, delete_event
)
from app.chatbot import chat_with_content
from app.sessions import register_session, list_sessions
from app.qa_history import save_qa, list_qa_history
from app.db import init_db, SessionLocal, NoteRow, TodoRow, CalendarEventRow, SessionRecord, QAHistoryRow
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CatchUp API",
    description="Real-time meeting recap and Q&A with evidence-based answers",
    version="1.0.0"
)

# CORS middleware
allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Create tables/extension if they don't exist yet. Idempotent, safe on every boot."""
    init_db()
    logger.info("Database initialized")


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "CatchUp API",
        "version": "1.0.0"
    }


@app.post("/api/ingest")
def ingest_transcript(request: IngestTranscriptRequest):
    """
    Ingest transcript chunks into the vector store.
    """
    try:
        logger.info(f"Ingesting {len(request.chunks)} chunks for session {request.session_id} (mode: {request.mode})")
        vector_store.add_chunks(request.session_id, request.chunks)
        return {
            "status": "success",
            "session_id": request.session_id,
            "chunks_ingested": len(request.chunks)
        }
    except Exception as e:
        logger.error(f"Error ingesting transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/question", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    """
    Ask a question about the transcript.
    HARD RULE: Returns 2-5 evidence quotes or says insufficient evidence.
    """
    try:
        logger.info(f"Question for session {request.session_id}: {request.question}")
        response = answer_question(request.session_id, request.question)
        
        # Validate evidence requirement
        if response.has_sufficient_evidence and len(response.evidence) < settings.min_evidence_quotes:
            logger.warning("Response has insufficient evidence, overriding to insufficient")
            response.has_sufficient_evidence = False
            response.answer = "Insufficient evidence in the transcript to answer this question."

        try:
            save_qa(request.session_id, request.question, response)
        except Exception as e:
            logger.error(f"Error saving Q&A history (answer still returned): {e}")

        return response
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/qa-history")
def get_qa_history(session_id: str):
    """Get past Q&A for a session, oldest first."""
    try:
        history = list_qa_history(session_id)
        return {"history": history}
    except Exception as e:
        logger.error(f"Error getting Q&A history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recap", response_model=RecapResponse)
def get_recap(request: RecapRequest):
    """
    Generate a meeting recap with evidence.
    HARD RULE: Must include evidence quotes.
    """
    try:
        logger.info(f"Generating recap for session {request.session_id}")
        response = generate_recap(request.session_id)
        return response
    except Exception as e:
        logger.error(f"Error generating recap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sessions")
def create_session(request: CreateSessionRequest):
    """Register a new session with its display name (for the history view)."""
    try:
        logger.info(f"Registering session {request.id}: {request.display_name} ({request.mode})")
        session = register_session(request.id, request.display_name, request.mode)
        return session
    except Exception as e:
        logger.error(f"Error registering session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sessions")
def get_sessions():
    """List all sessions, newest first."""
    try:
        sessions = list_sessions()
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/audio/upload")
def upload_audio(session_id: str, audio: UploadFile = File(...)):
    """
    Upload a full audio file for transcription (in-person mode).

    Plain `def`, not `async def`: transcription is a slow, blocking Gemini
    call (10-20+ seconds). FastAPI runs plain-`def` endpoints in a thread
    pool automatically, so one slow upload doesn't freeze the whole server
    the way it would inside an `async def` handler.
    """
    try:
        logger.info(f"Received audio upload for session {session_id}: {audio.filename}")

        audio_data = audio.file.read()
        success = process_audio_upload(session_id, audio_data, mime_type="audio/webm", start_offset_seconds=0)

        return {
            "status": "success" if success else "no_speech_or_error",
            "session_id": session_id,
            "filename": audio.filename,
            "size_bytes": len(audio_data)
        }
    except Exception as e:
        logger.error(f"Error uploading audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/audio/chunk")
def upload_audio_chunk(
    session_id: str,
    start_offset_seconds: float,
    mime_type: str = "audio/webm",
    audio: UploadFile = File(...)
):
    """
    Upload one live audio chunk (screen-share/tab-audio capture mode) for
    real transcription. Chunks arrive periodically from the frontend's
    MediaRecorder and are stitched into one continuous session transcript
    using start_offset_seconds.

    Plain `def`, not `async def` - see upload_audio() above for why: this
    avoids one slow transcription call blocking every other request
    (including other chunks, transcript polling, Q&A) on the event loop.
    """
    try:
        logger.info(f"Received audio chunk for session {session_id} @ {start_offset_seconds}s")

        audio_data = audio.file.read()
        success = process_audio_upload(session_id, audio_data, mime_type, start_offset_seconds)

        return {
            "status": "success" if success else "no_speech_or_error",
            "session_id": session_id,
            "start_offset_seconds": start_offset_seconds,
            "size_bytes": len(audio_data)
        }
    except Exception as e:
        logger.error(f"Error uploading audio chunk: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/session/{session_id}")
def delete_session(session_id: str):
    """Delete a session and all its data (transcript chunks, notes, todos, events, Q&A history)."""
    try:
        logger.info(f"Deleting session {session_id}")
        vector_store.delete_session(session_id)
        with SessionLocal() as db:
            db.query(NoteRow).filter(NoteRow.session_id == session_id).delete()
            db.query(TodoRow).filter(TodoRow.session_id == session_id).delete()
            db.query(CalendarEventRow).filter(CalendarEventRow.session_id == session_id).delete()
            db.query(QAHistoryRow).filter(QAHistoryRow.session_id == session_id).delete()
            db.query(SessionRecord).filter(SessionRecord.id == session_id).delete()
            db.commit()
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEW FEATURES: Transcripts, Notes, Todos, Calendar, Chatbot
# ============================================================================

@app.get("/api/transcript/{session_id}", response_model=TranscriptResponse)
def get_transcript(session_id: str):
    """Get full transcript for a session."""
    try:
        logger.info(f"Getting transcript for session {session_id}")
        chunks = vector_store.get_all_chunks(session_id)
        
        if not chunks:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Calculate total duration
        last_timestamp = chunks[-1]["timestamp"] if chunks else "00:00:00"
        
        from app.models import TranscriptChunk
        transcript_chunks = [
            TranscriptChunk(
                timestamp=chunk["timestamp"],
                text=chunk["text"],
                speaker=chunk.get("speaker")
            )
            for chunk in chunks
        ]
        
        return TranscriptResponse(
            session_id=session_id,
            chunks=transcript_chunks,
            total_duration=last_timestamp
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/notes", response_model=Note)
def create_new_note(request: CreateNoteRequest):
    """Create a new note."""
    try:
        logger.info(f"Creating note: {request.title}")
        note = create_note(request.session_id, request.title, request.content, request.date)
        return note
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/notes")
def get_notes(session_id: str = None):
    """Get all notes, optionally filtered by session."""
    try:
        notes = list_notes(session_id)
        return {"notes": notes}
    except Exception as e:
        logger.error(f"Error getting notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/notes/{note_id}", response_model=Note)
def get_note_by_id(note_id: str):
    """Get a specific note."""
    try:
        note = get_note(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return note
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/notes/{note_id}", response_model=Note)
def update_existing_note(note_id: str, request: UpdateNoteRequest):
    """Update a note."""
    try:
        note = update_note(note_id, request.title, request.content)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return note
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/notes/{note_id}")
def delete_note_by_id(note_id: str):
    """Delete a note."""
    try:
        success = delete_note(note_id)
        if not success:
            raise HTTPException(status_code=404, detail="Note not found")
        return {"status": "success", "note_id": note_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/todos/generate")
def generate_todos(request: SessionIdRequest):
    """Generate todo list from meeting transcript."""
    try:
        logger.info(f"Generating todos for session {request.session_id}")
        todos = generate_todos_from_meeting(request.session_id)
        return {"todos": todos}
    except Exception as e:
        logger.error(f"Error generating todos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/todos")
def get_todos(session_id: str = None):
    """Get all todos, optionally filtered by session."""
    try:
        todos = list_todos(session_id)
        return {"todos": todos}
    except Exception as e:
        logger.error(f"Error getting todos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/todos/{todo_id}/complete")
def mark_todo_complete(todo_id: str, completed: bool = True):
    """Mark a todo as completed."""
    try:
        todo = complete_todo(todo_id, completed)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        return todo
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing todo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/todos/{todo_id}", response_model=TodoItem)
def update_existing_todo(todo_id: str, request: UpdateTodoRequest):
    """Update a todo's fields."""
    try:
        todo = update_todo(todo_id, request.title, request.description, request.priority, request.due_date)
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        return todo
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating todo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/todos/{todo_id}")
def delete_todo_by_id(todo_id: str):
    """Delete a todo."""
    try:
        success = delete_todo(todo_id)
        if not success:
            raise HTTPException(status_code=404, detail="Todo not found")
        return {"status": "success", "todo_id": todo_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting todo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/events/generate")
def generate_events(request: SessionIdRequest):
    """Extract calendar events from meeting transcript."""
    try:
        logger.info(f"Extracting calendar events for session {request.session_id}")
        events = generate_calendar_events(request.session_id)
        return {"events": events}
    except Exception as e:
        logger.error(f"Error generating events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events")
def get_calendar_events(session_id: str = None):
    """Get all calendar events, optionally filtered by session."""
    try:
        events = list_events(session_id)
        return {"events": events}
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/events/{event_id}", response_model=CalendarEvent)
def update_existing_event(event_id: str, request: UpdateEventRequest):
    """Update a calendar event's fields."""
    try:
        event = update_event(event_id, request.title, request.description, request.date, request.time, request.duration_minutes)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/events/{event_id}")
def delete_event_by_id(event_id: str):
    """Delete a calendar event."""
    try:
        success = delete_event(event_id)
        if not success:
            raise HTTPException(status_code=404, detail="Event not found")
        return {"status": "success", "event_id": event_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chatbot", response_model=ChatbotResponse)
def chatbot_query(request: ChatbotRequest):
    """
    AI chatbot that can answer questions about all content.
    HARD RULE: Returns evidence-based answers.
    """
    try:
        logger.info(f"Chatbot question: {request.question}")
        response = chat_with_content(request.question, request.context_types)
        
        # Validate evidence requirement
        if response.has_sufficient_evidence and len(response.evidence) < settings.min_evidence_quotes:
            logger.warning("Chatbot response has insufficient evidence")
            response.has_sufficient_evidence = False
            response.answer = "Insufficient content available to answer this question."
        
        return response
    except Exception as e:
        logger.error(f"Error in chatbot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
