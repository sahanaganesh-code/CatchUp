from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class TranscriptChunk(BaseModel):
    """A chunk of transcript with timestamp."""
    timestamp: str = Field(..., description="Timestamp in HH:MM:SS format")
    text: str = Field(..., description="Transcript text")
    speaker: Optional[str] = Field(None, description="Speaker name if available")


class IngestTranscriptRequest(BaseModel):
    """Request to ingest transcript chunks."""
    session_id: str = Field(..., description="Unique session identifier")
    mode: Literal["in-person"] = Field(..., description="Meeting mode")
    chunks: List[TranscriptChunk] = Field(..., description="List of transcript chunks")


class Evidence(BaseModel):
    """Evidence quote with timestamp from transcript."""
    timestamp: str = Field(..., description="Timestamp in HH:MM:SS format")
    quote: str = Field(..., description="Exact quote from transcript")
    speaker: Optional[str] = Field(None, description="Speaker if available")


class QuestionRequest(BaseModel):
    """Request to ask a question about the transcript."""
    session_id: str = Field(..., description="Session identifier")
    question: str = Field(..., description="User's question")


class QuestionResponse(BaseModel):
    """Response to a question with evidence."""
    answer: str = Field(..., description="Answer to the question")
    evidence: List[Evidence] = Field(..., description="2-5 evidence quotes")
    has_sufficient_evidence: bool = Field(..., description="Whether sufficient evidence was found")


class QAHistoryItem(BaseModel):
    """A past question + answer for a session, for the history view."""
    question: str
    answer: str
    evidence: List[Evidence]
    has_sufficient_evidence: bool
    created_at: datetime


class RecapRequest(BaseModel):
    """Request to generate a recap."""
    session_id: str = Field(..., description="Session identifier")


class RecapResponse(BaseModel):
    """Recap of the meeting with evidence."""
    summary: str = Field(..., description="Meeting summary")
    key_points: List[str] = Field(..., description="Key discussion points")
    evidence: List[Evidence] = Field(..., description="Supporting evidence")


class ActionType(str):
    NOTION_TASK = "notion_task"
    CALENDAR_EVENT = "calendar_event"
    EMAIL_FOLLOWUP = "email_followup"
    SLIDES = "slides"


class ProposedAction(BaseModel):
    """A proposed action from the meeting."""
    action_id: str = Field(..., description="Unique action identifier")
    session_id: str = Field(..., description="Associated session")
    action_type: Literal["notion_task", "calendar_event", "email_followup", "slides"]
    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Action description")
    evidence: List[Evidence] = Field(..., description="Supporting evidence")
    metadata: dict = Field(default_factory=dict, description="Type-specific metadata")
    approved: bool = Field(default=False, description="Whether action is approved")
    executed: bool = Field(default=False, description="Whether action was executed")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProposeActionsRequest(BaseModel):
    """Request to propose actions from transcript."""
    session_id: str = Field(..., description="Session identifier")


class ProposeActionsResponse(BaseModel):
    """Response with proposed actions."""
    actions: List[ProposedAction] = Field(..., description="List of proposed actions")


class ApproveActionRequest(BaseModel):
    """Request to approve and execute an action."""
    action_id: str = Field(..., description="Action identifier")
    approved: bool = Field(..., description="Approval status")


class ApproveActionResponse(BaseModel):
    """Response after action approval."""
    action_id: str
    approved: bool
    executed: bool
    message: str


class TodoItem(BaseModel):
    """A todo item extracted from meeting."""
    todo_id: str = Field(..., description="Unique todo identifier")
    session_id: str = Field(..., description="Associated session")
    title: str = Field(..., description="Todo title")
    description: str = Field(..., description="Todo description")
    priority: Literal["low", "medium", "high"] = Field(default="medium")
    due_date: Optional[str] = Field(None, description="Due date if mentioned")
    evidence: List[Evidence] = Field(..., description="Supporting evidence")
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CalendarEvent(BaseModel):
    """A calendar event extracted from meeting."""
    event_id: str = Field(..., description="Unique event identifier")
    session_id: str = Field(..., description="Associated session")
    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    date: Optional[str] = Field(None, description="Event date (YYYY-MM-DD)")
    time: Optional[str] = Field(None, description="Event time (HH:MM)")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    evidence: List[Evidence] = Field(..., description="Supporting evidence")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Note(BaseModel):
    """A user-created note."""
    note_id: str = Field(..., description="Unique note identifier")
    session_id: str = Field(..., description="Associated session")
    title: str = Field(..., description="Note title")
    content: str = Field(..., description="Note content")
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CreateNoteRequest(BaseModel):
    """Request to create a note."""
    session_id: str
    title: str
    content: str
    date: str


class UpdateNoteRequest(BaseModel):
    """Request to update a note."""
    note_id: str
    title: Optional[str] = None
    content: Optional[str] = None


class UpdateEventRequest(BaseModel):
    """Request to update a calendar event."""
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    duration_minutes: Optional[int] = None


class UpdateTodoRequest(BaseModel):
    """Request to update a todo."""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Literal["low", "medium", "high"]] = None
    due_date: Optional[str] = None


class GetTranscriptRequest(BaseModel):
    """Request to get full transcript."""
    session_id: str = Field(..., description="Session identifier")


class TranscriptResponse(BaseModel):
    """Full transcript response."""
    session_id: str
    chunks: List[TranscriptChunk]
    total_duration: str = Field(..., description="Total duration in HH:MM:SS")


class ChatbotRequest(BaseModel):
    """Request to chat with AI about all content."""
    question: str = Field(..., description="User's question")
    context_types: List[Literal["transcripts", "notes", "todos", "events"]] = Field(
        default=["transcripts", "notes", "todos", "events"],
        description="Types of content to search"
    )


class ChatbotResponse(BaseModel):
    """Response from AI chatbot."""
    answer: str = Field(..., description="Answer to the question")
    evidence: List[Evidence] = Field(..., description="Supporting evidence")
    sources: List[str] = Field(..., description="Source types used (transcript/note/todo/event)")
    has_sufficient_evidence: bool = Field(..., description="Whether sufficient evidence was found")


class Session(BaseModel):
    """A registered meeting/capture session, for the history view."""
    id: str = Field(..., description="Session identifier")
    display_name: str = Field(..., description="User-facing session name")
    mode: Literal["in-person", "screen-share"] = Field(..., description="Capture mode")
    created_at: datetime = Field(..., description="When the session was created")


class CreateSessionRequest(BaseModel):
    """Request to register a new session."""
    id: str = Field(..., description="Session identifier")
    display_name: str = Field(..., description="User-facing session name")
    mode: Literal["in-person", "screen-share"] = Field(..., description="Capture mode")
