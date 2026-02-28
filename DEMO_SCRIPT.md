# CatchUp Demo Script

This script will help you demo the CatchUp MVP effectively.

## Pre-Demo Setup (5 minutes)

### 1. Start Backend
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
```
✅ Verify: http://localhost:8000 shows `{"status":"healthy"}`

### 2. Start Frontend
```bash
cd frontend
npm run dev
```
✅ Verify: http://localhost:3000 loads

### 3. Optional: Run API Tests
```bash
cd backend
python test_api.py
```
✅ Verify: All tests pass with "✓"

## Demo Flow (10 minutes)

### Part 1: Introduction (1 minute)

**Say:**
> "CatchUp is an accessible meeting assistant built for the Health & Lifestyle theme. It empowers people with disabilities - whether hearing impairments, ADHD, dyslexia, or cognitive challenges - to fully participate in meetings and lectures. 
>
> Imagine being a student with ADHD trying to take notes while staying focused. Or being deaf and missing critical information in a meeting. CatchUp solves this with real-time transcription, evidence-based Q&A, and smart action proposals. Let me show you."

**Show:** Home page with accessibility messaging

### Part 2: Zoom Mode Demo (4 minutes)

#### Step 1: Connect to Meeting
**Do:**
1. Click "Zoom Meeting Mode"
2. Enter meeting ID: `demo-meeting-123`
3. Click "Connect to Meeting"

**Say:**
> "In production, this would connect to Zoom's Real-Time Meeting Streaming API. For the demo, we're using mock transcript data that loads automatically."

**Show:** Green "Connected" status bar

#### Step 2: Generate Recap
**Do:**
1. Click "Generate Recap" button
2. Wait for response (2-3 seconds)

**Say:**
> "The system uses RAG - Retrieval-Augmented Generation - to create a summary with key points. Notice the evidence section at the bottom."

**Point out:**
- Summary text
- Key points list
- Evidence quotes with timestamps: `[00:00:00] "quote"`

#### Step 3: Ask Questions
**Do:**
1. Type: "What topics were discussed?"
2. Press Enter or click Send
3. Wait for response

**Say:**
> "This is where our first hard rule comes in: EVERY answer must include 2-5 evidence quotes with timestamps. This is critical for accessibility - people with memory challenges or learning disabilities need verifiable information they can trust. If there isn't enough evidence, the system says 'Insufficient evidence' instead of making something up. No hallucination."

**Point out:**
- Answer text
- Evidence section (2-5 quotes)
- Timestamps and exact quotes

**Do:** Ask another question:
- "Who is responsible for the authentication work?"

**Show:** New answer with evidence

#### Step 4: Propose Actions
**Do:**
1. Click "Propose Actions" button
2. Wait for response (3-4 seconds)

**Say:**
> "The system analyzes the meeting and proposes actionable items. These could be Notion tasks, calendar events, email follow-ups, or slide decks. Each action has supporting evidence."

**Point out:**
- Different action types (📝 📅 ✉️ 📊)
- Action titles and descriptions
- "Show Evidence" link

**Do:**
1. Click "Show Evidence" on first action
2. Show the evidence quotes

**Say:**
> "Here's our second hard rule: NO actions execute unless you explicitly approve them. This is critical for people with cognitive challenges or executive function difficulties - the system reduces cognitive load by proposing actions, but YOU maintain control. It's assistance, not automation."

**Do:**
1. Click "Approve & Execute" on first action
2. Wait for confirmation

**Point out:**
- Green checkmark appears
- "Action executed successfully" message
- Warning banner about approval requirement

**Do:**
1. Click "Reject" on second action

**Say:**
> "Rejected actions never execute. You have complete control."

### Part 3: In-Person Mode Demo (3 minutes)

**Do:**
1. Click Back button
2. Click "In-Person Lecture Mode"
3. Enter lecture ID: `CS101-Lecture5`
4. Click "Start Session"

**Say:**
> "In-person mode is designed for live lectures, therapy sessions, or support groups. This is perfect for students with ADHD who struggle with note-taking, or anyone who needs to focus on participating rather than recording. In production, this would use your microphone and transcribe in real-time. For the demo, we have mock lecture data."

**Show:**
- Green session status
- Recording controls (stub)
- Upload audio button (stub)

**Do:**
1. Click "Generate Recap"
2. Show the lecture summary

**Say:**
> "Same features work here: recap, Q&A with evidence, and action proposals. The system might suggest creating homework tasks or scheduling office hours."

### Part 4: Health & Accessibility Impact (1 minute)

**Say:**
> "Let me highlight why this matters for health and lifestyle:
> 
> 1. **Evidence-Based Answers**: People with memory challenges or learning disabilities need verifiable information. Our 2-5 timestamped quotes provide that trust and reliability.
> 
> 2. **Approval Gating**: For people with ADHD or executive function challenges, we reduce cognitive load while maintaining user control. The system proposes, you decide.
> 
> 3. **Real-Time Accessibility**: Deaf and hard-of-hearing individuals get instant captions. People with ADHD can focus on the conversation instead of frantically taking notes.
>
> This isn't just a productivity tool - it's a mental health tool. It reduces anxiety, prevents burnout, and makes meetings inclusive for everyone."

### Part 5: Architecture Overview (1 minute)

**Say:**
> "The tech stack is:
> - Backend: FastAPI with ChromaDB vector store for semantic search
> - Frontend: Next.js with TypeScript
> - AI: Google Gemini for embeddings and text generation
> 
> The system uses RAG - we embed transcript chunks with Gemini, retrieve relevant ones for each question, and ground the LLM's answer in that evidence."

**Show:** (Optional) Open `ARCHITECTURE.md` diagram

## Q&A Preparation

### Expected Questions

**Q: "How does the evidence extraction work?"**
A: "We use ChromaDB to store transcript chunks with Gemini embeddings. When you ask a question, we do semantic search to find the most relevant chunks, then extract 2-5 quotes. Gemini generates an answer based only on those quotes."

**Q: "What happens if there's not enough evidence?"**
A: "The system returns 'Insufficient evidence in the transcript to answer this question.' We never let the LLM hallucinate or guess."

**Q: "How do you prevent actions from running without approval?"**
A: "The backend has a hard check: `if not approved: return`. Actions are stored in pending state until you explicitly approve them. The API validates the `approved=true` flag."

**Q: "Can this work with real Zoom meetings?"**
A: "Yes! Zoom has an RTMS (Real-Time Meeting Streaming) API that sends transcript chunks via webhooks. We have a stub implementation in `app/zoom.py` that would handle that."

**Q: "What about real-time transcription for in-person mode?"**
A: "We'd use a speech-to-text service like OpenAI Whisper API or Google Speech-to-Text. The browser captures audio, sends it to the backend, the service transcribes it with timestamps, and we add chunks to the vector store in real-time."

**Q: "How accurate is the action proposal?"**
A: "It depends on the LLM and the transcript quality. Gemini is quite good at identifying action items. The key is that users review and approve, so accuracy isn't critical - it's a proposal system, not an automation system."

**Q: "Can you show the code?"**
A: "Sure!" (Open relevant files)
- Evidence extraction: `backend/app/rag.py`
- Approval gating: `backend/app/actions.py`
- Frontend approval UI: `frontend/app/components/ActionsPanel.tsx`

**Q: "How would you scale this?"**
A: "For production:
- Replace in-memory action store with PostgreSQL
- Use distributed ChromaDB or Pinecone for vectors
- Add Redis for caching
- WebSocket for real-time updates
- Horizontal scaling with load balancer
- Add authentication and rate limiting"

**Q: "What's the latency?"**
A: "Current demo:
- Recap: 2-3 seconds
- Q&A: 1-2 seconds
- Action proposal: 3-4 seconds
Most time is LLM API calls. With caching and optimization, we could get Q&A under 1 second."

## Demo Tips

### Do's ✅
- Emphasize the hard rules (evidence + approval)
- Show the evidence quotes prominently
- Demonstrate both approval and rejection
- Highlight the timestamps in evidence
- Show how "insufficient evidence" works (ask a question about something not in the transcript)

### Don'ts ❌
- Don't skip showing the evidence - it's the key differentiator
- Don't forget to mention approval gating
- Don't claim real Zoom/STT integration (be clear it's a stub)
- Don't gloss over the modular architecture

### Pro Tips 💡
- Have the test script output ready to show passing tests
- Open the code files to show the hard rule enforcement
- Mention the ~3,000 lines of code in 30 files
- Highlight the comprehensive documentation (5 docs)
- Show the `.cursorrules` file that enforces standards

## Backup Demo (If Live Demo Fails)

### Option 1: Show Test Script
```bash
cd backend
python test_api.py
```
Walk through the test output showing:
- Evidence validation
- Approval gating
- API responses

### Option 2: Show Code
Open and explain:
1. `backend/app/rag.py` - Evidence extraction logic
2. `backend/app/actions.py` - Approval gating
3. `frontend/app/components/ActionsPanel.tsx` - Approval UI

### Option 3: Show Documentation
Walk through:
1. `README.md` - Feature overview
2. `ARCHITECTURE.md` - System design
3. `.cursorrules` - Hard rules

## Post-Demo

### Key Takeaways to Emphasize
1. ✅ Evidence-based answers (no hallucination)
2. ✅ User control via approval gating
3. ✅ Dual mode (Zoom + in-person)
4. ✅ Production-ready architecture
5. ✅ Comprehensive documentation

### Next Steps to Mention
- Real Zoom RTMS integration
- OpenAI Whisper for STT
- Notion/Calendar/Email API integration
- User authentication
- Production deployment

## Time Allocation

- Introduction: 1 min
- Zoom Mode: 4 min
- In-Person Mode: 3 min
- Hard Rules: 1 min
- Architecture: 1 min
- **Total: 10 minutes**
- Q&A: 5-10 minutes

## Success Metrics

Demo is successful if audience understands:
1. ✅ What CatchUp does (recap + Q&A + actions)
2. ✅ Why evidence matters (grounding, no hallucination)
3. ✅ Why approval matters (user control)
4. ✅ How it's architected (modular, scalable)

Good luck! 🚀
