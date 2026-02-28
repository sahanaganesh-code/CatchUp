from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.models import (
    IngestTranscriptRequest,
    QuestionRequest,
    QuestionResponse,
    RecapRequest,
    RecapResponse,
    ProposeActionsRequest,
    ProposeActionsResponse,
    ApproveActionRequest,
    ApproveActionResponse,
    GoogleMeetWebhookPayload,
    AudioUploadRequest,
    CreateNoteRequest,
    UpdateNoteRequest,
    Note,
    TodoItem,
    CalendarEvent,
    GetTranscriptRequest,
    TranscriptResponse,
    ChatbotRequest,
    ChatbotResponse,
    ErrorResponse,
    NotFoundError,
)
from app.rag import answer_question, generate_recap
from app.actions import propose_actions, approve_action, list_actions
from app.meet import process_meet_webhook, simulate_meet_transcript
from app.stt import process_audio_upload, transcribe_audio
from app.store import vector_store
from app.config import settings
from app.content_manager import (
    create_note, get_note, list_notes, update_note, delete_note,
    generate_todos_from_meeting, list_todos, get_todo, complete_todo, delete_todo,
    generate_calendar_events, list_events, get_event, delete_event
)
from app.chatbot import chat_with_content
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter (key by IP; default_limits apply to all routes)
_rate_limit_str = f"{settings.rate_limit_per_minute}/minute" if settings.rate_limit_enabled else "10000/minute"
limiter = Limiter(key_func=get_remote_address, default_limits=[_rate_limit_str])

app = FastAPI(
    title="CatchUp API",
    description="Real-time meeting recap and Q&A with evidence-based answers. All answers include 2-5 evidence quotes from transcripts.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Health", "description": "Health check and API status"},
        {"name": "Ingest & Transcript", "description": "Ingest transcript chunks and retrieve full transcript"},
        {"name": "Q&A & Recap", "description": "Ask questions and generate meeting recap with evidence"},
        {"name": "Actions", "description": "Propose and approve actions (Google Tasks, Calendar, Gmail, Slides)"},
        {"name": "Google Meet & Audio", "description": "Google Meet transcript webhook and audio upload (Gemini/Whisper)"},
        {"name": "Session", "description": "Session lifecycle (delete)"},
        {"name": "Notes", "description": "Create, read, update, delete notes"},
        {"name": "Todos", "description": "Generate and manage todos from meetings"},
        {"name": "Events", "description": "Generate and manage calendar events"},
        {"name": "Chatbot", "description": "AI chatbot over all content with evidence"},
    ],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Authentication (optional API key)
# ---------------------------------------------------------------------------
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Depends(API_KEY_HEADER)) -> str | None:
    """If API_KEY is set in config, require valid X-API-Key header. Otherwise allow all."""
    if not settings.api_key:
        return None
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide X-API-Key header.",
        )
    return api_key


# ---------------------------------------------------------------------------
# Global exception handlers (improved error handling)
# ---------------------------------------------------------------------------
@app.exception_handler(NotFoundError)
def not_found_handler(request, exc: NotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message, "status_code": 404},
    )


@app.exception_handler(Exception)
def unhandled_exception_handler(request, exc: Exception):
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred.", "status_code": 500},
    )


@app.get("/", tags=["Health"])
def read_root():
    """Health check endpoint. No authentication required."""
    return {
        "status": "healthy",
        "service": "CatchUp API",
        "version": "1.0.0"
    }


@app.get("/api/status", tags=["Health"])
def api_status():
    """
    API status, config, and integration contracts for coordination (Person 1 & 2).
    Use this to align on session_id format, modes, and response shapes without editing shared modules.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "rate_limit_enabled": settings.rate_limit_enabled,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "auth_required": bool(settings.api_key),
        "integration": {
            "ingest_mode": ["google_meet", "in-person"],
            "session_id_prefix": {"google_meet": "meet_", "in-person": "any"},
            "action_types": ["google_tasks", "google_calendar", "gmail_followup", "google_slides"],
            "evidence_rule": "2-5 quotes with timestamps; insufficient -> 404-style or has_sufficient_evidence=false",
        },
    }


@app.post(
    "/api/ingest",
    tags=["Ingest & Transcript"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse, "description": "Ingest failed"}},
)
def ingest_transcript(request: IngestTranscriptRequest, _=Depends(verify_api_key)):
    """
    Ingest transcript chunks into the vector store.
    Modes: google_meet (Meet live captions/recording) or in-person (upload/STT).
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


@app.post(
    "/api/question",
    response_model=QuestionResponse,
    tags=["Q&A & Recap"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse, "description": "Question failed"}},
)
def ask_question(request: QuestionRequest, _=Depends(verify_api_key)):
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
        
        return response
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/recap",
    response_model=RecapResponse,
    tags=["Q&A & Recap"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse, "description": "Recap failed"}},
)
def get_recap(request: RecapRequest, _=Depends(verify_api_key)):
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


@app.post(
    "/api/actions/propose",
    response_model=ProposeActionsResponse,
    tags=["Actions"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse, "description": "Propose failed"}},
)
def propose_meeting_actions(request: ProposeActionsRequest, _=Depends(verify_api_key)):
    """
    Propose actions from the meeting transcript.
    HARD RULE: Each action includes evidence quotes.
    """
    try:
        logger.info(f"Proposing actions for session {request.session_id}")
        actions = propose_actions(request.session_id)
        return ProposeActionsResponse(actions=actions)
    except Exception as e:
        logger.error(f"Error proposing actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/actions/approve",
    response_model=ApproveActionResponse,
    tags=["Actions"],
    responses={401: {"description": "Invalid or missing API key"}, 404: {"model": ErrorResponse, "description": "Action not found"}, 500: {"model": ErrorResponse, "description": "Approve failed"}},
)
def approve_meeting_action(request: ApproveActionRequest, _=Depends(verify_api_key)):
    """
    Approve and execute an action.
    HARD RULE: Action only executes if approved=True.
    """
    try:
        logger.info(f"Approving action {request.action_id}: approved={request.approved}")
        if not request.approved:
            logger.info(f"Action {request.action_id} not approved, skipping execution")
        response = approve_action(request.action_id, request.approved)
        return response
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Error approving action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/actions",
    tags=["Actions"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse}},
)
def get_actions(_=Depends(verify_api_key)):
    """Get all proposed actions."""
    try:
        actions = list_actions()
        return {"actions": actions}
    except Exception as e:
        logger.error(f"Error getting actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/meet/webhook",
    tags=["Google Meet & Audio"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse}},
)
def meet_webhook(payload: GoogleMeetWebhookPayload, _=Depends(verify_api_key)):
    """
    Google Meet transcript webhook (live captions or recording).
    In production: Meet API, Pub/Sub, or Drive/YouTube transcript ingestion.
    """
    try:
        logger.info(f"Received Google Meet webhook for meeting {payload.meeting_id}")
        success = process_meet_webhook(payload)
        return {"status": "success" if success else "error"}
    except Exception as e:
        logger.error(f"Error processing Meet webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/api/audio/upload",
    tags=["Google Meet & Audio"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse}},
)
async def upload_audio(session_id: str, audio: UploadFile = File(...), _=Depends(verify_api_key)):
    """
    Upload audio file for transcription (in-person mode stub).
    In production, this would transcribe using Whisper API.
    """
    try:
        logger.info(f"Received audio upload for session {session_id}: {audio.filename}")
        
        # Read audio data
        audio_data = await audio.read()
        
        # Process audio (stub)
        success = process_audio_upload(session_id, audio_data)
        
        return {
            "status": "success" if success else "error",
            "session_id": session_id,
            "filename": audio.filename,
            "size_bytes": len(audio_data)
        }
    except Exception as e:
        logger.error(f"Error uploading audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/sessions",
    tags=["Session"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse}},
)
def list_sessions(_=Depends(verify_api_key)):
    """List all session IDs that have transcript data (for coordination and UI)."""
    try:
        session_ids = vector_store.list_session_ids()
        return {"sessions": session_ids}
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete(
    "/api/session/{session_id}",
    tags=["Session"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse}},
)
def delete_session(session_id: str, _=Depends(verify_api_key)):
    """Delete a session and all its data."""
    try:
        logger.info(f"Deleting session {session_id}")
        vector_store.delete_session(session_id)
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEW FEATURES: Transcripts, Notes, Todos, Calendar, Chatbot
# ============================================================================

@app.get(
    "/api/transcript/{session_id}",
    response_model=TranscriptResponse,
    tags=["Ingest & Transcript"],
    responses={401: {"description": "Invalid or missing API key"}, 404: {"model": ErrorResponse, "description": "Session not found"}, 500: {"model": ErrorResponse}},
)
def get_transcript(session_id: str, _=Depends(verify_api_key)):
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


@app.post(
    "/api/notes",
    response_model=Note,
    tags=["Notes"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse}},
)
def create_new_note(request: CreateNoteRequest, _=Depends(verify_api_key)):
    """Create a new note."""
    try:
        logger.info(f"Creating note: {request.title}")
        note = create_note(request.session_id, request.title, request.content, request.date)
        return note
    except Exception as e:
        logger.error(f"Error creating note: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/notes",
    tags=["Notes"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse}},
)
def get_notes(session_id: str = None, _=Depends(verify_api_key)):
    """Get all notes, optionally filtered by session."""
    try:
        notes = list_notes(session_id)
        return {"notes": notes}
    except Exception as e:
        logger.error(f"Error getting notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/notes/{note_id}",
    response_model=Note,
    tags=["Notes"],
    responses={401: {"description": "Invalid or missing API key"}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def get_note_by_id(note_id: str, _=Depends(verify_api_key)):
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


@app.put(
    "/api/notes/{note_id}",
    response_model=Note,
    tags=["Notes"],
    responses={401: {"description": "Invalid or missing API key"}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def update_existing_note(note_id: str, request: UpdateNoteRequest, _=Depends(verify_api_key)):
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


@app.delete(
    "/api/notes/{note_id}",
    tags=["Notes"],
    responses={401: {"description": "Invalid or missing API key"}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def delete_note_by_id(note_id: str, _=Depends(verify_api_key)):
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


@app.post(
    "/api/todos/generate",
    tags=["Todos"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse}},
)
def generate_todos(request: ProposeActionsRequest, _=Depends(verify_api_key)):
    """Generate todo list from meeting transcript."""
    try:
        logger.info(f"Generating todos for session {request.session_id}")
        todos = generate_todos_from_meeting(request.session_id)
        return {"todos": todos}
    except Exception as e:
        logger.error(f"Error generating todos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/todos",
    tags=["Todos"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse}},
)
def get_todos(_=Depends(verify_api_key)):
    """Get all todos."""
    try:
        todos = list_todos()
        return {"todos": todos}
    except Exception as e:
        logger.error(f"Error getting todos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put(
    "/api/todos/{todo_id}/complete",
    tags=["Todos"],
    responses={401: {"description": "Invalid or missing API key"}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def mark_todo_complete(todo_id: str, completed: bool = True, _=Depends(verify_api_key)):
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


@app.delete(
    "/api/todos/{todo_id}",
    tags=["Todos"],
    responses={401: {"description": "Invalid or missing API key"}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def delete_todo_by_id(todo_id: str, _=Depends(verify_api_key)):
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


@app.post(
    "/api/events/generate",
    tags=["Events"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse}},
)
def generate_events(request: ProposeActionsRequest, _=Depends(verify_api_key)):
    """Extract calendar events from meeting transcript."""
    try:
        logger.info(f"Extracting calendar events for session {request.session_id}")
        events = generate_calendar_events(request.session_id)
        return {"events": events}
    except Exception as e:
        logger.error(f"Error generating events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/api/events",
    tags=["Events"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse}},
)
def get_calendar_events(_=Depends(verify_api_key)):
    """Get all calendar events."""
    try:
        events = list_events()
        return {"events": events}
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete(
    "/api/events/{event_id}",
    tags=["Events"],
    responses={401: {"description": "Invalid or missing API key"}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def delete_event_by_id(event_id: str, _=Depends(verify_api_key)):
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


@app.post(
    "/api/chatbot",
    response_model=ChatbotResponse,
    tags=["Chatbot"],
    responses={401: {"description": "Invalid or missing API key"}, 500: {"model": ErrorResponse, "description": "Chatbot failed"}},
)
def chatbot_query(request: ChatbotRequest, _=Depends(verify_api_key)):
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
