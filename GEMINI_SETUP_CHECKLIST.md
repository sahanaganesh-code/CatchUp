# Gemini Setup Checklist

Use this checklist to set up CatchUp with Google Gemini.

## ☑️ Pre-Setup

- [ ] Python 3.9+ installed
- [ ] Node.js 18+ installed
- [ ] Git repository cloned/available

## ☑️ Get Gemini API Key

1. [ ] Go to https://aistudio.google.com/app/apikey
2. [ ] Sign in with Google account
3. [ ] Click "Create API Key"
4. [ ] Copy the API key (starts with `AI...`)
5. [ ] Save it securely (you'll need it in the next step)

## ☑️ Backend Setup

### 1. Navigate to Backend
```bash
cd catchup/backend
```
- [ ] Confirmed in backend directory

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```
- [ ] Virtual environment created
- [ ] Virtual environment activated (you should see `(venv)` in prompt)

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
- [ ] All packages installed successfully
- [ ] No error messages
- [ ] Confirm `google-genai` is installed: `pip list | grep google-genai`

### 4. Configure Environment
```bash
cp .env.example .env
```
- [ ] `.env` file created

Edit `.env` file and add your Gemini API key:
```bash
GEMINI_API_KEY=AIza...your-key-here
CHROMA_PERSIST_DIR=./chroma_db
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_EMBED_MODEL=text-embedding-004
```
- [ ] `GEMINI_API_KEY` added
- [ ] Other settings configured (or left as defaults)

### 5. Start Backend Server
```bash
python -m uvicorn app.main:app --reload
```
- [ ] Server starts without errors
- [ ] See message: "Initialized ChromaDB collection: catchup_transcripts_gemini"
- [ ] Server running at http://localhost:8000

### 6. Test Backend (New Terminal)
```bash
# Keep server running, open new terminal
cd catchup/backend
source venv/bin/activate
python test_api.py
```
- [ ] Health check passes ✓
- [ ] Transcript ingestion works ✓
- [ ] Q&A with evidence works ✓
- [ ] Recap generation works ✓
- [ ] Action proposal works ✓
- [ ] Approval gating verified ✓
- [ ] All tests show "✓ All tests passed!"

## ☑️ Frontend Setup

### 1. Navigate to Frontend (New Terminal)
```bash
cd catchup/frontend
```
- [ ] Confirmed in frontend directory

### 2. Install Dependencies
```bash
npm install
```
- [ ] All packages installed successfully
- [ ] No error messages
- [ ] `node_modules/` directory created

### 3. Configure Environment
```bash
cp .env.local.example .env.local
```
- [ ] `.env.local` file created

Content should be:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```
- [ ] API URL configured

### 4. Start Frontend Server
```bash
npm run dev
```
- [ ] Server starts without errors
- [ ] Server running at http://localhost:3000
- [ ] No compilation errors

## ☑️ End-to-End Testing

### 1. Open Application
- [ ] Navigate to http://localhost:3000
- [ ] Home page loads with two mode cards
- [ ] No console errors (F12 → Console)

### 2. Test Zoom Mode
- [ ] Click "Zoom Meeting Mode"
- [ ] Enter meeting ID: `test-meeting-123`
- [ ] Click "Connect to Meeting"
- [ ] See green "Connected" status
- [ ] Mock transcript data loads

#### Test Recap
- [ ] Click "Generate Recap"
- [ ] Summary appears (2-3 sentences)
- [ ] Key points listed
- [ ] Evidence section shows 2-5 quotes with timestamps

#### Test Q&A
- [ ] Type question: "What topics were discussed?"
- [ ] Press Enter or click Send
- [ ] Answer appears
- [ ] Evidence shows 2-5 quotes
- [ ] Each quote has timestamp `[HH:MM:SS]` and text

#### Test Actions
- [ ] Click "Propose Actions"
- [ ] Actions appear (tasks, events, emails, slides)
- [ ] Each action has evidence
- [ ] Click "Show Evidence" on an action
- [ ] Evidence quotes appear
- [ ] Click "Approve & Execute"
- [ ] Action status changes to executed ✓
- [ ] Green success message appears

### 3. Test In-Person Mode
- [ ] Go back to home
- [ ] Click "In-Person Lecture Mode"
- [ ] Enter lecture ID: `CS101-Lecture5`
- [ ] Click "Start Session"
- [ ] Mock lecture data loads
- [ ] Test Recap, Q&A, and Actions (same as above)

## ☑️ Verification

### Hard Rules Check
- [ ] **Evidence Requirement**: All Q&A answers have 2-5 quotes
- [ ] **Evidence Requirement**: Quotes include timestamps
- [ ] **Evidence Requirement**: Quotes are exact text from transcript
- [ ] **Approval Gating**: Actions don't execute without approval
- [ ] **Approval Gating**: Rejected actions never execute
- [ ] **Modular Architecture**: Code is clean and organized

### Backend Logs Check
Open backend terminal and verify:
- [ ] See "Embedding X texts with task_type=RETRIEVAL_DOCUMENT" (when ingesting)
- [ ] See "Embedding X texts with task_type=RETRIEVAL_QUERY" (when querying)
- [ ] See "Generating text with model=gemini-2.0-flash-exp"
- [ ] See "Successfully generated X embeddings"
- [ ] No error messages

### ChromaDB Check
- [ ] `backend/chroma_db/` directory exists
- [ ] Collection name is `catchup_transcripts_gemini`
- [ ] No old OpenAI data mixed in

## ☑️ Troubleshooting

If you encounter issues:

### "GEMINI_API_KEY not found"
- [ ] Check `.env` file exists in `backend/`
- [ ] Check `GEMINI_API_KEY=` line is present
- [ ] Check API key is correct (no extra spaces)
- [ ] Restart backend server

### "Module 'google.genai' not found"
- [ ] Activate virtual environment: `source venv/bin/activate`
- [ ] Reinstall: `pip install google-genai`
- [ ] Check: `pip list | grep google-genai`

### "Connection refused" / Frontend can't reach backend
- [ ] Backend server is running (http://localhost:8000)
- [ ] Check backend terminal for errors
- [ ] Check `.env.local` has correct API URL
- [ ] Try: `curl http://localhost:8000` (should return JSON)

### "No evidence in answers"
- [ ] Ensure transcript was ingested first
- [ ] Check backend logs for embedding generation
- [ ] Try deleting `chroma_db/` and restarting
- [ ] Re-ingest transcript data

### "Rate limit exceeded"
- [ ] Check Gemini API quota at https://aistudio.google.com/
- [ ] Wait a few minutes and retry
- [ ] Consider upgrading API plan if needed

### Port already in use
- [ ] Backend: Kill process on 8000: `lsof -ti:8000 | xargs kill`
- [ ] Frontend: Use different port: `npm run dev -- -p 3001`

## ☑️ Success Criteria

You're all set when:
- [x] Backend server running without errors
- [x] Frontend server running without errors
- [x] Can generate recaps with evidence
- [x] Can ask questions and get answers with 2-5 quotes
- [x] Can propose and approve actions
- [x] All hard rules are enforced
- [x] No console errors
- [x] Test suite passes

## 🎉 Next Steps

Now you can:
1. Explore the code in `backend/app/` and `frontend/app/`
2. Read the documentation:
   - `README.md` - Complete guide
   - `ARCHITECTURE.md` - System design
   - `DEMO_SCRIPT.md` - Demo walkthrough
3. Customize the system for your needs
4. Deploy to production (see deployment guides)

## 📚 Additional Resources

- Gemini API Docs: https://ai.google.dev/docs
- Get API Key: https://aistudio.google.com/app/apikey
- CatchUp Docs: See `README.md`, `QUICKSTART.md`, `ARCHITECTURE.md`
- Migration Guide: See `MIGRATION_GEMINI.md`

---

**Setup Complete!** 🚀

If you followed all steps and checked all boxes, your CatchUp instance is ready to use with Google Gemini!
