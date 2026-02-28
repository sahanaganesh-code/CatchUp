# CatchUp - Accessible Meeting Assistant for Health & Lifestyle

**Hackathon Theme: Health and Lifestyle**

An accessibility-focused MVP that empowers students with disabilities, people with ADHD, hearing impairments, or cognitive challenges to fully participate in meetings and lectures through real-time transcription, intelligent recap generation, and evidence-based Q&A.

## 🎯 Health & Lifestyle Impact

CatchUp addresses critical accessibility needs:
- **Hearing Accessibility**: Real-time transcripts for deaf/hard-of-hearing individuals
- **Cognitive Support**: Structured recaps and evidence-based Q&A for people with ADHD, dyslexia, or memory challenges
- **Mental Health**: Reduces anxiety by allowing users to focus on conversation instead of note-taking
- **Learning Disabilities**: Provides multiple ways to review and understand content (recap, Q&A, timestamped evidence)
- **Work-Life Balance**: Automated action items reduce cognitive load and prevent burnout

## Features

### 🎥 Two Accessible Modes

1. **Zoom Meeting Mode**: RTMS (Real-Time Meeting Streaming) transcript ingestion
   - Perfect for remote work, online classes, telehealth appointments
   - Provides real-time captions and searchable transcripts

2. **In-Person Lecture Mode**: Browser-based microphone recording with backend transcription
   - Ideal for in-person classes, therapy sessions, support groups
   - Enables participation without the stress of note-taking

### 🎯 Accessibility-First Features

- **Real-Time CatchUp Recap**: Generate intelligent meeting summaries with key points
  - Helps users with ADHD or cognitive challenges quickly understand main topics
  - Reduces cognitive load by providing structured information

- **Grounded Q&A**: Ask questions and get answers with 2-5 evidence quotes (timestamps + exact quotes)
  - Supports people with memory challenges or learning disabilities
  - Provides verifiable, timestamped information for review
  - Reduces anxiety about missing important details

- **FlowPilot Actions**: Propose and approve actions with evidence:
  - 📝 Notion tasks - Never forget follow-ups or assignments
  - 📅 Calendar events - Automatic scheduling support
  - ✉️ Email follow-ups - Communication assistance
  - 📊 Slide generation - Study material creation
  - Reduces executive function burden for people with ADHD or cognitive challenges

### 🔒 Hard Rules (Enforced)

1. **Evidence Requirement**: Every answer MUST include 2-5 evidence quotes with timestamps. If insufficient evidence exists, the system responds: "Insufficient evidence in the transcript to answer this question."

2. **Approval Gating**: NO actions execute unless `approved=true` is sent from the frontend. All actions require explicit user approval.

3. **Modular Architecture**: Clean separation of concerns across backend modules.

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Pydantic**: Data validation and settings management
- **ChromaDB**: Vector database for semantic search
- **Google Gemini**: Embeddings and LLM for RAG

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe frontend code
- **Tailwind CSS**: Utility-first styling
- **Axios**: HTTP client

## Project Structure

```
catchup/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app & routes
│   │   ├── config.py        # Configuration & settings
│   │   ├── models.py        # Pydantic models
│   │   ├── store.py         # ChromaDB vector store
│   │   ├── rag.py           # RAG & Q&A logic
│   │   ├── actions.py       # Action proposal & execution
│   │   ├── zoom.py          # Zoom RTMS ingestion stub
│   │   └── stt.py           # Speech-to-text stub
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                 # Create this (see setup)
├── frontend/
│   ├── app/
│   │   ├── components/      # React components
│   │   ├── lib/             # API client
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── .env.local.example
│   └── .env.local           # Create this (see setup)
├── .cursorrules             # Project rules
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Edit `.env` and add your Gemini API key:
```
GEMINI_API_KEY=your-key-here
CHROMA_PERSIST_DIR=./chroma_db
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_EMBED_MODEL=models/text-embedding-004
```

6. Run the backend:
```bash
python -m uvicorn app.main:app --reload
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env.local` file:
```bash
cp .env.local.example .env.local
```

4. Edit `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

5. Run the frontend:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage Guide

### 1. Choose Your Mode

On the home page, select either:
- **Zoom Meeting Mode** for virtual meetings
- **In-Person Lecture Mode** for live recordings

### 2. Start a Session

**Zoom Mode:**
- Enter a Zoom Meeting ID
- Click "Connect to Meeting"
- The system will simulate transcript ingestion (stub)

**In-Person Mode:**
- Enter a Lecture ID
- Click "Start Session"
- Use recording controls or upload audio (stub)

### 3. Generate Recap

- Click "Generate Recap" to get a meeting summary
- View key points and supporting evidence with timestamps

### 4. Ask Questions

- Type your question in the Q&A panel
- Receive answers with 2-5 evidence quotes
- Each quote includes timestamp and exact text from transcript

### 5. Propose & Approve Actions

- Click "Propose Actions" to generate action items
- Review each action with its supporting evidence
- Click "Approve & Execute" to run the action
- Or click "Reject" to decline

**Important**: Actions only execute after explicit approval!

## API Endpoints

### Transcript Ingestion
```
POST /api/ingest
Body: {
  "session_id": "string",
  "mode": "zoom" | "in-person",
  "chunks": [{"timestamp": "HH:MM:SS", "text": "...", "speaker": "..."}]
}
```

### Ask Question
```
POST /api/question
Body: {
  "session_id": "string",
  "question": "string"
}
Response: {
  "answer": "string",
  "evidence": [{"timestamp": "HH:MM:SS", "quote": "...", "speaker": "..."}],
  "has_sufficient_evidence": boolean
}
```

### Generate Recap
```
POST /api/recap
Body: {
  "session_id": "string"
}
Response: {
  "summary": "string",
  "key_points": ["string"],
  "evidence": [...]
}
```

### Propose Actions
```
POST /api/actions/propose
Body: {
  "session_id": "string"
}
Response: {
  "actions": [...]
}
```

### Approve Action
```
POST /api/actions/approve
Body: {
  "action_id": "string",
  "approved": boolean
}
```

## Stub Implementations

The following features are **stubs** for the hackathon MVP:

1. **Zoom RTMS Integration** (`app/zoom.py`): In production, integrate with Zoom's Real-Time Meeting Streaming API
2. **Speech-to-Text** (`app/stt.py`): In production, use OpenAI Whisper API or similar
3. **Action Execution** (`app/actions.py`): In production, integrate with:
   - Notion API for task creation
   - Google Calendar API for events
   - Email service for follow-ups
   - Google Slides API for presentations

## Development

### Running Tests

Backend:
```bash
cd backend
pytest  # Add tests in tests/ directory
```

Frontend:
```bash
cd frontend
npm test  # Add tests with Jest/React Testing Library
```

### Code Quality

The project enforces hard rules via `.cursorrules`:
- Evidence-based answers (2-5 quotes)
- Approval gating for actions
- Modular code structure

## Troubleshooting

### Backend won't start
- Check that your `.env` file exists and has a valid Gemini API key
- Ensure port 8000 is not in use

### Frontend can't connect to backend
- Verify backend is running on `http://localhost:8000`
- Check `.env.local` has correct `NEXT_PUBLIC_API_URL`

### No evidence in answers
- Ensure you've ingested transcript chunks first
- Check that ChromaDB is properly initialized
- Verify Gemini API key is valid

### Actions not executing
- This is expected! Actions require explicit approval
- Click "Approve & Execute" button
- Check backend logs for execution confirmation

## Future Enhancements

- Real Zoom RTMS integration
- Live audio transcription with Whisper
- Speaker diarization
- Real-time streaming UI updates
- Persistent database (PostgreSQL)
- User authentication
- Session history
- Export functionality
- Mobile app

## Accessibility Statement

CatchUp is designed with accessibility at its core:
- ✅ Real-time transcription for hearing accessibility
- ✅ Evidence-based answers reduce cognitive load
- ✅ Structured recaps support learning disabilities
- ✅ Action automation assists with executive function
- ✅ Timestamped evidence enables self-paced review

## Target Users

- Students with hearing impairments or deafness
- People with ADHD who struggle with note-taking
- Individuals with dyslexia or reading challenges
- People with memory or cognitive challenges
- Anyone experiencing meeting fatigue or burnout
- Neurodivergent individuals who need structured information

## Health & Lifestyle Benefits

1. **Reduced Stress**: No pressure to capture everything in real-time
2. **Better Comprehension**: Review at your own pace with evidence
3. **Improved Participation**: Focus on conversation, not note-taking
4. **Mental Health**: Less anxiety about missing important information
5. **Work-Life Balance**: Automated action items prevent overwhelm

## License

MIT License - Built for Health & Lifestyle Hackathon

## Contributors

Built with ❤️ to make meetings accessible for everyone
