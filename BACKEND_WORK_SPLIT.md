# Backend Work Split - 3 People

## 📊 File Overview

| File | Lines | Complexity | Category |
|------|-------|------------|----------|
| `main.py` | 449 | High | API Routes |
| `content_manager.py` | 315 | High | Content Logic |
| `actions.py` | 211 | Medium | Actions |
| `rag.py` | 194 | High | AI/RAG |
| `models.py` | 183 | Low | Data Models |
| `chatbot.py` | 167 | High | AI/Chatbot |
| `store.py` | 124 | Medium | Database |
| `stt.py` | 104 | Medium | Audio |
| `gemini_client.py` | 77 | Medium | AI Client |
| `meet.py` | 62 | Low | Google Meet stub |
| `config.py` | 33 | Low | Config |

**Total:** 1,920 lines

---

## 🎯 Recommended Split (Balanced by Complexity & Dependencies)

### Person 1: AI & RAG Expert 🤖
**Focus:** AI logic, embeddings, prompts, intelligent features

**Primary Files (640 lines):**
- ✅ `rag.py` (194 lines) - Q&A engine, recap generation
- ✅ `chatbot.py` (167 lines) - AI chatbot logic
- ✅ `content_manager.py` (315 lines) - Todo/event extraction with AI
- ✅ `gemini_client.py` (77 lines) - Gemini API wrapper

**Secondary Files (Read/Coordinate):**
- 📖 `models.py` - Read data models
- 🤝 `main.py` - Coordinate on AI endpoints

**Tasks:**
- Improve AI prompt engineering
- Optimize RAG retrieval accuracy
- Enhance todo/event extraction
- Add more intelligent features
- Fine-tune Gemini parameters

**Why this person:**
- All AI/ML logic in one place
- Can optimize prompts holistically
- Minimal dependencies on others

---

### Person 2: Data & Integration Engineer 💾
**Focus:** Database, storage, external integrations, data flow

**Primary Files (290 lines):**
- ✅ `store.py` (124 lines) - ChromaDB vector store (with list_session_ids, chunks cache)
- ✅ `meet.py` (62 lines) - Google Meet transcript ingestion (webhook verification ready)
- ✅ `stt.py` (104 lines) - Speech-to-text (Gemini/Whisper path ready)

**Secondary Files (Read/Coordinate):**
- 📖 `models.py` - Read data models
- 🤝 `main.py` - Coordinate on data endpoints
- 📖 `config.py` - Read configuration

**Tasks:**
- Implement real Google Meet / live captions integration
- Implement real STT (Whisper or Gemini audio)
- Optimize ChromaDB queries
- Add data persistence for notes/todos
- Add caching layer (chunks cache in store)
- Database migrations

**Why this person:**
- All external integrations
- Data storage and retrieval
- Can work independently on integrations

---

### Person 3: API & Orchestration Lead 🔌
**Focus:** API endpoints, request/response, coordination, models

**Primary Files (632 lines):**
- ✅ `main.py` (449 lines) - FastAPI routes
- ✅ `actions.py` (211 lines) - Action proposals & execution
- ✅ `models.py` (183 lines) - Pydantic models
- ✅ `config.py` (33 lines) - Configuration

**Secondary Files (Coordinate with Others):**
- 🤝 All other files - Coordinates integration

**Tasks:**
- Add new API endpoints
- Improve error handling
- Add request validation
- Add API documentation (Swagger)
- Add rate limiting
- Add authentication
- Coordinate between Person 1 & 2

**Why this person:**
- Central coordination point
- Defines contracts (models)
- Ensures everything integrates

---

## 📋 Detailed Task Breakdown

### Person 1: AI & RAG Expert

#### Week 1 Tasks
- [ ] Improve recap generation prompts in `rag.py`
- [ ] Enhance Q&A accuracy with better retrieval
- [ ] Optimize todo extraction in `content_manager.py`
- [ ] Improve calendar event extraction accuracy
- [ ] Add priority scoring to todos

#### Files to Edit
```
backend/app/rag.py
backend/app/chatbot.py
backend/app/content_manager.py
backend/app/gemini_client.py
```

#### Example Changes
```python
# rag.py - Improve prompts
def generate_recap(chunks):
    prompt = f"""
    Generate a concise meeting recap with:
    1. Key decisions made
    2. Action items identified
    3. Important discussions
    
    Context: {chunks}
    """
    # Better structured prompts
```

#### Branch Naming
- `ai/improve-rag`
- `ai/better-extraction`
- `ai/chatbot-enhancement`

---

### Person 2: Data & Integration Engineer

#### Week 1 Tasks
- [ ] Implement real Google Meet / live captions in `meet.py`
- [ ] Implement Whisper or Gemini audio STT in `stt.py`
- [ ] Optimize ChromaDB indexing in `store.py` (list_session_ids, cache in place)
- [ ] Add data persistence for notes/todos
- [ ] Add caching for frequent queries (chunks cache in store)

#### Files to Edit
```
backend/app/store.py
backend/app/meet.py
backend/app/stt.py
```

#### Example Changes
```python
# meet.py - Real Google Meet integration
# Use Meet recording → Drive/YouTube transcript, or Pub/Sub for live captions
def process_meet_webhook(payload: GoogleMeetWebhookPayload) -> bool:
    if settings.google_meet_webhook_secret and not verify_meet_webhook_signature(...):
        return False
    # Ingest transcript chunk...
```

#### Branch Naming
- `data/meet-integration`
- `data/stt-whisper`
- `data/optimize-storage`

---

### Person 3: API & Orchestration Lead

#### Week 1 Tasks
- [ ] Add authentication to API in `main.py`
- [ ] Improve error handling across all endpoints
- [ ] Add new models in `models.py` as needed
- [ ] Add API documentation (Swagger)
- [ ] Coordinate integration between Person 1 & 2

#### Files to Edit
```
backend/app/main.py
backend/app/actions.py
backend/app/models.py
backend/app/config.py
```

#### Example Changes
```python
# main.py - Add authentication
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/api/upload")
async def upload_transcript(
    request: UploadRequest,
    token: str = Depends(security)
):
    # Verify token
    if not verify_token(token):
        raise HTTPException(401, "Unauthorized")
    # ... rest of logic
```

#### Branch Naming
- `api/add-auth`
- `api/error-handling`
- `api/new-endpoints`

---

## 🚫 Conflict Avoidance Rules

### Person 1 (AI Expert)
**✅ Can Edit Freely:**
- `rag.py` - Full ownership
- `chatbot.py` - Full ownership
- `content_manager.py` - Full ownership
- `gemini_client.py` - Full ownership

**🤝 Must Coordinate:**
- `main.py` - Only AI-related endpoints (tell Person 3)
- `models.py` - Only AI-related models (tell Person 3)

**❌ Don't Touch:**
- `store.py` - Person 2's territory
- `meet.py` - Person 2's territory
- `stt.py` - Person 2's territory

---

### Person 2 (Data Engineer)
**✅ Can Edit Freely:**
- `store.py` - Full ownership
- `meet.py` - Full ownership
- `stt.py` - Full ownership

**🤝 Must Coordinate:**
- `main.py` - Only data endpoints (tell Person 3)
- `models.py` - Only data models (tell Person 3)

**❌ Don't Touch:**
- `rag.py` - Person 1's territory
- `chatbot.py` - Person 1's territory
- `content_manager.py` - Person 1's territory
- `actions.py` - Person 3's territory

---

### Person 3 (API Lead)
**✅ Can Edit Freely:**
- `main.py` - Full ownership (but coordinate changes)
- `actions.py` - Full ownership
- `models.py` - Full ownership
- `config.py` - Full ownership

**🤝 Must Coordinate:**
- `main.py` - Tell others before major refactors
- `models.py` - Tell others before changing existing models

**❌ Don't Touch:**
- `rag.py` - Person 1's territory
- `chatbot.py` - Person 1's territory
- `content_manager.py` - Person 1's territory
- `store.py` - Person 2's territory
- `meet.py` - Person 2's territory
- `stt.py` - Person 2's territory
- `gemini_client.py` - Person 1's territory

---

## 📞 Communication Protocol

### Before Editing Shared Files

**Shared files that need coordination:**
- `main.py` - Person 3 owns, but others may need to add endpoints
- `models.py` - Person 3 owns, but others may need new models

**Protocol:**
1. Post in team chat: "Need to add [endpoint/model] to [file]"
2. Wait for Person 3 to confirm timing
3. Make changes
4. Push immediately
5. Notify: "Done with [file]"

### Example Communication

**Person 1:** "Need to add a new model `TodoPriority` to `models.py` for AI scoring"

**Person 3:** "Go ahead, I'm not editing models.py today"

**Person 1:** *Makes changes, pushes*

**Person 1:** "Added `TodoPriority` to models.py, line 150. Please pull!"

---

## 🔄 Daily Workflow

### Morning Standup (5 min)
Each person shares:
1. What files will you edit today?
2. Any shared files you need?
3. When will you push?

### Work Session
```bash
# Person 1
git checkout -b ai/improve-rag
# Edit rag.py, chatbot.py, content_manager.py
git add backend/app/rag.py backend/app/chatbot.py
git commit -m "AI: Improve RAG prompts and accuracy"
git push origin ai/improve-rag

# Person 2
git checkout -b data/meet-integration
# Edit meet.py, stt.py
git add backend/app/meet.py backend/app/stt.py
git commit -m "Data: Add real Google Meet integration"
git push origin data/meet-integration

# Person 3
git checkout -b api/add-auth
# Edit main.py, config.py
git add backend/app/main.py backend/app/config.py
git commit -m "API: Add authentication to endpoints"
git push origin api/add-auth
```

### End of Day
- Create PR
- Others review
- Merge to main
- Everyone pulls latest

---

## 🎯 Feature Assignment Examples

### Feature: "Add Meeting Summary Email"

**Person 1 (AI):**
- Write prompt to generate email content
- Add function in `rag.py`: `generate_summary_email()`

**Person 2 (Data):**
- No work needed (unless email sending service)

**Person 3 (API):**
- Add new model: `EmailSummaryRequest` in `models.py`
- Add endpoint: `POST /api/email-summary` in `main.py`
- Call Person 1's function

**Coordination:**
1. Person 3 creates model first
2. Person 1 implements AI logic
3. Person 3 adds endpoint calling Person 1's function

---

### Feature: "Real-time Transcript Streaming"

**Person 1 (AI):**
- No work needed initially

**Person 2 (Data):**
- Implement WebSocket in `meet.py`
- Stream transcript chunks to backend

**Person 3 (API):**
- Add WebSocket endpoint in `main.py`
- Handle real-time connections
- Call Person 2's streaming function

**Coordination:**
1. Person 2 implements streaming logic
2. Person 3 adds WebSocket endpoint
3. Person 3 calls Person 2's function

---

### Feature: "Better Todo Prioritization"

**Person 1 (AI):**
- Add priority scoring in `content_manager.py`
- Update prompt to extract priority

**Person 2 (Data):**
- No work needed

**Person 3 (API):**
- Add `priority` field to `TodoItem` model in `models.py`
- Update endpoint response

**Coordination:**
1. Person 3 adds priority field to model
2. Person 1 implements priority logic
3. Test together

---

## 📊 Workload Balance

### By Lines of Code
- **Person 1:** 640 lines (33%)
- **Person 2:** 290 lines (15%)
- **Person 3:** 632 lines (33%)
- **Shared:** 366 lines (19%)

### By Complexity (Estimated Hours)
- **Person 1:** High complexity - AI/ML work (40 hours)
- **Person 2:** Medium complexity - Integration work (30 hours)
- **Person 3:** High complexity - API orchestration (40 hours)

**Note:** Person 2 has fewer lines but high-value integration work (Google Meet, STT). Person 3 has coordination overhead.

---

## 🚀 Getting Started

### Person 1: AI Expert
```bash
cd /Users/sahanaganesh/catchup
git checkout -b ai/initial-improvements

# Your files
code backend/app/rag.py
code backend/app/chatbot.py
code backend/app/content_manager.py
code backend/app/gemini_client.py

# Start improving AI prompts!
```

### Person 2: Data Engineer
```bash
cd /Users/sahanaganesh/catchup
git checkout -b data/integrations

# Your files
code backend/app/store.py
code backend/app/meet.py
code backend/app/stt.py

# Start building real integrations!
```

### Person 3: API Lead
```bash
cd /Users/sahanaganesh/catchup
git checkout -b api/improvements

# Your files
code backend/app/main.py
code backend/app/actions.py
code backend/app/models.py
code backend/app/config.py

# Start improving API!
```

---

## ✅ Success Checklist

Your backend split is working if:
- [ ] Each person knows their primary files
- [ ] No two people edit same file simultaneously
- [ ] Shared files (main.py, models.py) are coordinated
- [ ] Everyone pulls before pushing
- [ ] PRs are reviewed by others
- [ ] Main branch always works
- [ ] Features integrate smoothly

---

## 🆘 If Conflicts Happen

### Scenario: Both Person 1 and Person 3 edited `main.py`

```bash
# Person 3 (owner of main.py) resolves
git pull origin main
# Conflict in main.py

# Open main.py, look for:
<<<<<<< HEAD
# Person 3's endpoint
@app.post("/api/auth")
=======
# Person 1's endpoint
@app.post("/api/ai-analyze")
>>>>>>> main

# Keep both (they're different endpoints)
@app.post("/api/auth")
# ... Person 3's code

@app.post("/api/ai-analyze")
# ... Person 1's code

# Save, test, commit
git add backend/app/main.py
git commit -m "Merge: Combine auth and AI endpoints"
git push
```

---

## 🎯 Quick Reference

| Person | Primary Files | Focus Area | Branch Prefix |
|--------|--------------|------------|---------------|
| Person 1 | rag.py, chatbot.py, content_manager.py, gemini_client.py | AI/ML | `ai/` |
| Person 2 | store.py, meet.py, stt.py | Data/Integration | `data/` |
| Person 3 | main.py, actions.py, models.py, config.py | API/Orchestration | `api/` |

**Golden Rule:** Own your files, coordinate on shared files, communicate always! 🎉
