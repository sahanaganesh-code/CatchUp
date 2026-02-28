# CatchUp Architecture

## System Overview

CatchUp is a real-time meeting transcription and analysis system that provides evidence-based Q&A and intelligent action proposals.

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Zoom Mode   │  │ In-Person    │  │   Actions    │      │
│  │   Component  │  │   Component  │  │   Component  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                      API Client (Axios)                      │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ HTTP/REST
                             │
┌────────────────────────────┴────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   API Routes                          │   │
│  │  /ingest  /question  /recap  /actions/*              │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────┴─────────────────────────────────────────┐   │
│  │              Core Business Logic                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │   │
│  │  │   RAG    │  │ Actions  │  │  Zoom/   │           │   │
│  │  │  Engine  │  │ Proposal │  │   STT    │           │   │
│  │  └──────────┘  └──────────┘  └──────────┘           │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                              │
│  ┌────────────┴─────────────────────────────────────────┐   │
│  │              Data Layer                               │   │
│  │  ┌──────────────┐         ┌──────────────┐           │   │
│  │  │  ChromaDB    │         │   Actions    │           │   │
│  │  │ Vector Store │         │    Store     │           │   │
│  │  └──────────────┘         └──────────────┘           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             │
                             │ API Calls
                             │
                    ┌────────┴────────┐
                    │  Gemini API     │
                    │  Embeddings +   │
                    │      LLM        │
                    └─────────────────┘
```

## Backend Architecture

### Module Breakdown

#### `app/main.py` - API Layer
- FastAPI application and route definitions
- Request/response handling
- CORS configuration
- Error handling

#### `app/config.py` - Configuration
- Pydantic settings management
- Environment variable loading
- Application constants
- Model configurations

#### `app/models.py` - Data Models
- Pydantic models for request/response validation
- Type definitions
- Data structures for:
  - Transcript chunks
  - Evidence quotes
  - Q&A pairs
  - Proposed actions

#### `app/store.py` - Vector Store
- ChromaDB client management
- Chunk storage and retrieval
- Semantic search
- Session management

#### `app/gemini_client.py` - Gemini Client
- Gemini API wrapper
- Text embedding generation
- Text generation
- Task type handling (RETRIEVAL_DOCUMENT vs RETRIEVAL_QUERY)

#### `app/rag.py` - RAG Engine
- **Evidence-based Q&A** (Hard Rule #1)
  - Query processing
  - Evidence extraction (2-5 quotes)
  - LLM answer generation (via Gemini)
  - Insufficient evidence detection
- **Recap generation**
  - Meeting summarization
  - Key point extraction
  - Evidence collection

#### `app/actions.py` - Action System
- **Action proposal**
  - LLM-based action extraction
  - Evidence linking
  - Action categorization
- **Approval gating** (Hard Rule #2)
  - Approval validation
  - Execution control
  - Status tracking
- **Action execution** (stubs)
  - Notion task creation
  - Calendar event scheduling
  - Email follow-ups
  - Slide generation

#### `app/zoom.py` - Zoom Integration (Stub)
- RTMS webhook handling
- Real-time transcript streaming
- Meeting lifecycle management

#### `app/stt.py` - Speech-to-Text (Stub)
- Audio file transcription
- Real-time audio streaming
- Timestamp generation
- Speaker diarization

## Frontend Architecture

### Component Hierarchy

```
App (page.tsx)
├── ZoomMode
│   ├── RecapPanel
│   ├── QAPanel
│   └── ActionsPanel
│       └── EvidenceList
└── InPersonMode
    ├── RecapPanel
    ├── QAPanel
    └── ActionsPanel
        └── EvidenceList
```

### Key Components

#### `page.tsx` - Home
- Mode selection UI
- Navigation

#### `ZoomMode.tsx`
- Zoom meeting connection
- Transcript ingestion
- Feature panels

#### `InPersonMode.tsx`
- Recording controls
- Audio upload
- Feature panels

#### `RecapPanel.tsx`
- Recap generation trigger
- Summary display
- Evidence presentation

#### `QAPanel.tsx`
- Question input
- Q&A history
- Evidence display
- Insufficient evidence handling

#### `ActionsPanel.tsx`
- Action proposal trigger
- Action list with evidence
- **Approval UI** (Hard Rule #2)
- Execution status

#### `EvidenceList.tsx`
- Timestamp formatting
- Quote display
- Speaker attribution

## Data Flow

### 1. Transcript Ingestion

```
User Input → Frontend → POST /api/ingest → Vector Store
                                          → ChromaDB
```

### 2. Question Answering

```
Question → POST /api/question → RAG Engine
                              → Vector Store (retrieve chunks with Gemini embeddings)
                              → Gemini (generate answer)
                              → Evidence Extraction (2-5 quotes)
                              → Response with Evidence
```

### 3. Action Proposal & Execution

```
Propose → POST /api/actions/propose → RAG Engine
                                    → LLM (extract actions)
                                    → Link Evidence
                                    → Store Actions (pending)

Approve → POST /api/actions/approve → Validate approval=true
                                    → Execute Action (if approved)
                                    → Update Status
```

## Hard Rules Implementation

### Rule 1: Evidence Requirement (2-5 quotes)

**Implementation:**
- `app/rag.py:answer_question()`
  - Retrieves top-k chunks from vector store
  - Validates minimum evidence count
  - Returns "Insufficient evidence" if < 2 quotes
  - Caps evidence at 5 quotes
- `app/config.py`
  - `min_evidence_quotes = 2`
  - `max_evidence_quotes = 5`

**Enforcement:**
- Backend validation in RAG engine
- Frontend displays evidence count
- UI shows warning for insufficient evidence

### Rule 2: Approval Gating

**Implementation:**
- `app/actions.py:approve_action()`
  - Checks `approved` parameter
  - Only calls `execute_action()` if `approved=True`
  - Returns execution status
- `app/main.py:/api/actions/approve`
  - Validates approval flag
  - Logs approval decisions

**Enforcement:**
- Backend blocks execution without approval
- Frontend requires explicit button click
- UI shows pending/approved/executed states

### Rule 3: Modular Architecture

**Implementation:**
- Separation of concerns across modules
- Single responsibility principle
- Clear interfaces between layers
- Type hints and Pydantic models

**Enforcement:**
- `.cursorrules` file
- Code review guidelines
- Import restrictions

## Scalability Considerations

### Current (MVP)
- In-memory action store
- Local ChromaDB
- Single-instance deployment

### Production Enhancements
- PostgreSQL for persistent storage
- Distributed ChromaDB or Pinecone
- Redis for caching
- Message queue (RabbitMQ/Kafka) for real-time events
- Horizontal scaling with load balancer
- WebSocket for real-time updates
- CDN for frontend assets

## Security Considerations

### Current
- CORS configuration
- Environment variable protection
- Input validation with Pydantic

### Production Enhancements
- JWT authentication
- API rate limiting
- Webhook signature verification
- Data encryption at rest
- HTTPS/TLS
- Input sanitization
- SQL injection prevention
- XSS protection

## Testing Strategy

### Unit Tests
- RAG engine evidence extraction
- Action approval gating
- Vector store operations
- Model validation

### Integration Tests
- API endpoint flows
- Database interactions
- LLM integration

### E2E Tests
- Full user workflows
- Mode switching
- Action approval flow

## Monitoring & Observability

### Logging
- Structured logging with Python `logging`
- Request/response logging
- Error tracking

### Metrics (Future)
- API latency
- Evidence retrieval time
- Action approval rate
- LLM token usage

### Tracing (Future)
- Distributed tracing with OpenTelemetry
- Request flow visualization
