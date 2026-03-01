from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
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
    ZoomWebhookPayload,
    AudioUploadRequest,
    CreateNoteRequest,
    UpdateNoteRequest,
    Note,
    TodoItem,
    CalendarEvent,
    GetTranscriptRequest,
    TranscriptResponse,
    ChatbotRequest,
    ChatbotResponse
)
from app.rag import answer_question, generate_recap
from app.gemini_client import GeminiQuotaExceeded
from app.actions import propose_actions, approve_action, list_actions
from app.zoom import process_zoom_webhook, simulate_zoom_transcript
from app.stt import process_media_upload, transcribe_audio
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

app = FastAPI(
    title="CatchUp API",
    description="Real-time meeting recap and Q&A with evidence-based answers",
    version="1.0.0"
)


@app.on_event("startup")
def startup_log():
    """Log which Gemini key and model are loaded so you can verify .env is used."""
    key = getattr(settings, "gemini_api_key", "") or ""
    suffix = key[-4:] if len(key) >= 4 else "????"
    logger.info("Gemini config: model=%s, key ends with ...%s", settings.gemini_model, suffix)
    recap_local = getattr(settings, "recap_use_local", True)
    qa_local = getattr(settings, "qa_use_local", True)
    use_llm = getattr(settings, "use_local_llm", True)
    from app import local_llm as llm
    ollama_ok = use_llm and llm.is_available()
    logger.info("Local LLM (Ollama): %s", "on" if ollama_ok else "off (run: ollama serve && ollama run llama3.2)")
    openai_set = bool(getattr(settings, "openai_api_key", None) and (settings.openai_api_key or "").strip())
    logger.info("Recap: %s", "local (Ollama)" if (recap_local and ollama_ok) else ("local (extractive)" if recap_local else ("OpenAI" if openai_set else "Gemini")))
    logger.info("Q&A: %s (evidence-based, 2-5 quotes)", "local (Ollama)" if (qa_local and ollama_ok) else ("local (synthesis)" if qa_local else "Gemini"))

# CORS: allow all origins in dev so frontend can reach backend from any URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


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
    Supports both Zoom and in-person modes.
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
        
        return response
    except GeminiQuotaExceeded as e:
        raise HTTPException(status_code=503, detail="Gemini rate limit reached. Please try again in a minute or check your API quota at https://ai.google.dev/gemini-api/docs/rate-limits")
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recap", response_model=RecapResponse)
def get_recap(request: RecapRequest):
    """
    Generate a meeting recap (Gemini only).
    Returns a clean bulleted list of key points in the model's own words — no quotes, no timestamps.
    """
    try:
        logger.info(f"Generating recap for session {request.session_id}")
        response = generate_recap(request.session_id)
        return response
    except GeminiQuotaExceeded:
        raise HTTPException(status_code=503, detail="Gemini rate limit reached. Please try again in a minute or check your API quota at https://ai.google.dev/gemini-api/docs/rate-limits")
    except Exception as e:
        logger.error(f"Error generating recap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/actions/propose", response_model=ProposeActionsResponse)
def propose_meeting_actions(request: ProposeActionsRequest):
    """
    Propose actions from the meeting transcript.
    HARD RULE: Each action includes evidence quotes.
    """
    try:
        logger.info(f"Proposing actions for session {request.session_id}")
        actions = propose_actions(request.session_id)
        return ProposeActionsResponse(actions=actions)
    except GeminiQuotaExceeded:
        raise HTTPException(status_code=503, detail="Gemini rate limit reached. Please try again in a minute or check your API quota at https://ai.google.dev/gemini-api/docs/rate-limits")
    except Exception as e:
        logger.error(f"Error proposing actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/actions/approve", response_model=ApproveActionResponse)
def approve_meeting_action(request: ApproveActionRequest):
    """
    Approve and execute an action.
    HARD RULE: Action only executes if approved=True.
    """
    try:
        logger.info(f"Approving action {request.action_id}: approved={request.approved}")
        
        # HARD RULE ENFORCEMENT: Only execute if approved=True
        if not request.approved:
            logger.info(f"Action {request.action_id} not approved, skipping execution")
        
        response = approve_action(request.action_id, request.approved)
        return response
    except Exception as e:
        logger.error(f"Error approving action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/actions")
def get_actions():
    """Get all proposed actions."""
    try:
        actions = list_actions()
        return {"actions": actions}
    except Exception as e:
        logger.error(f"Error getting actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/zoom/webhook")
def zoom_webhook(payload: ZoomWebhookPayload):
    """
    Meeting transcript webhook (Google Meet). Same payload shape for compatibility.
    """
    try:
        logger.info(f"Received Zoom webhook for meeting {payload.meeting_id}")
        success = process_zoom_webhook(payload)
        return {"status": "success" if success else "error"}
    except Exception as e:
        logger.error(f"Error processing Zoom webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Allow lecture-length uploads (e.g. 60–120 min); 300MB max for audio or video
MAX_MEDIA_UPLOAD_BYTES = 300 * 1024 * 1024


@app.post("/api/audio/upload")
async def upload_audio(request: Request, session_id: str):
    """
    Upload audio or video for transcription (in-person mode).
    Video: audio track is extracted with ffmpeg then transcribed.
    Supports long files via chunked Speech-to-Text / GCS batch.
    """
    try:
        try:
            form = await request.form(max_part_size=MAX_MEDIA_UPLOAD_BYTES)
        except TypeError:
            form = await request.form()
        file_obj = form.get("audio") or form.get("file")
        if not file_obj or not hasattr(file_obj, "read"):
            raise HTTPException(status_code=400, detail="Missing file (field 'audio' or 'file')")
        filename = getattr(file_obj, "filename", "audio") or "audio"
        content_type = getattr(file_obj, "content_type", None) or ""
        logger.info(f"Received media upload for session {session_id}: {filename} ({content_type})")
        file_data = await file_obj.read()
        if len(file_data) > MAX_MEDIA_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail=f"File too large (max {MAX_MEDIA_UPLOAD_BYTES // (1024*1024)}MB)")
        success, message = process_media_upload(session_id, file_data, filename=filename, content_type=content_type)
        return {
            "status": "success" if success else "error",
            "session_id": session_id,
            "filename": filename,
            "size_bytes": len(file_data),
            "detail": message if not success else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading media: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/session/{session_id}")
def delete_session(session_id: str):
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
def generate_todos(request: ProposeActionsRequest):
    """Generate todo list from meeting transcript."""
    try:
        logger.info(f"Generating todos for session {request.session_id}")
        todos = generate_todos_from_meeting(request.session_id)
        return {"todos": todos}
    except Exception as e:
        logger.error(f"Error generating todos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/todos")
def get_todos():
    """Get all todos."""
    try:
        todos = list_todos()
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
def generate_events(request: ProposeActionsRequest):
    """Extract calendar events from meeting transcript."""
    try:
        logger.info(f"Extracting calendar events for session {request.session_id}")
        events = generate_calendar_events(request.session_id)
        return {"events": events}
    except Exception as e:
        logger.error(f"Error generating events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/events")
def get_calendar_events():
    """Get all calendar events."""
    try:
        events = list_events()
        return {"events": events}
    except Exception as e:
        logger.error(f"Error getting events: {e}")
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
    except GeminiQuotaExceeded:
        raise HTTPException(status_code=503, detail="Gemini rate limit reached. Please try again in a minute or check your API quota at https://ai.google.dev/gemini-api/docs/rate-limits")
    except Exception as e:
        logger.error(f"Error in chatbot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
