# Team Setup Guide - For New Team Members

Welcome to the CatchUp team! This guide will help you get set up quickly.

---

## 🚀 Quick Setup (10 minutes)

### Step 1: Clone the Repository

```bash
# Clone the repo (replace YOUR_USERNAME with actual username)
git clone https://github.com/YOUR_USERNAME/catchup.git
cd catchup
```

### Step 2: Get Gemini API Key

1. Go to: https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)

### Step 3: Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=AIza...your-key-here
```

### Step 4: Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Create .env.local file
cp .env.local.example .env.local

# No changes needed - defaults to http://localhost:8000
```

### Step 5: Test Everything Works

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Browser:**
Open http://localhost:3000

---

## 📁 Project Structure

```
catchup/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py      # API endpoints
│   │   ├── models.py    # Data models
│   │   ├── rag.py       # Q&A logic
│   │   ├── actions.py   # Action proposals
│   │   ├── content_manager.py  # Notes/Todos/Events
│   │   ├── chatbot.py   # AI chatbot
│   │   ├── store.py     # Vector database
│   │   └── gemini_client.py  # Gemini API wrapper
│   └── requirements.txt
│
└── frontend/            # Next.js frontend
    ├── app/
    │   ├── components/  # React components
    │   │   ├── ZoomMode.tsx
    │   │   ├── InPersonMode.tsx
    │   │   ├── TranscriptViewer.tsx
    │   │   ├── TodoPanel.tsx
    │   │   ├── CalendarPanel.tsx
    │   │   ├── NotesPanel.tsx
    │   │   ├── AIChatbot.tsx
    │   │   └── ...
    │   ├── lib/
    │   │   └── api.ts   # API client
    │   └── page.tsx     # Home page
    └── package.json
```

---

## 🎯 Who Should Work on What?

### Backend Developer
**Focus**: API endpoints, Gemini integration, data management

**Key Files:**
- `backend/app/main.py` - API routes
- `backend/app/rag.py` - Q&A logic
- `backend/app/content_manager.py` - Notes/todos/events
- `backend/app/chatbot.py` - AI chatbot

**Tasks:**
- Improve todo/event extraction accuracy
- Add real Zoom integration
- Add real STT integration
- Optimize vector search

### Frontend Developer
**Focus**: UI/UX, components, user experience

**Key Files:**
- `frontend/app/components/*.tsx` - All components
- `frontend/app/page.tsx` - Home page
- `frontend/app/globals.css` - Styling

**Tasks:**
- Improve UI/UX design
- Add animations and transitions
- Mobile responsiveness
- Accessibility features (keyboard nav, screen readers)

### Full-Stack / Integration
**Focus**: Testing, deployment, documentation

**Key Files:**
- `backend/test_api.py` - Tests
- Documentation files
- Configuration files

**Tasks:**
- Write comprehensive tests
- Set up CI/CD
- Deploy to production
- Update documentation

---

## 🔄 Git Workflow

### Daily Routine

```bash
# Morning: Get latest changes
git checkout main
git pull origin main

# Create your feature branch
git checkout -b feature/your-feature-name

# Work on your feature...
# (make changes, test locally)

# Commit your changes
git add .
git commit -m "Add: description of your changes"

# Push to GitHub
git push origin feature/your-feature-name

# Create pull request on GitHub
# Ask teammate to review
# Merge when approved
```

### Commit Message Format

```
Type: Brief description

Longer description if needed

Examples:
- Add: transcript export functionality
- Fix: chatbot evidence display bug
- Update: README with new features
- Refactor: API client for better error handling
```

---

## 🧪 Testing Your Changes

### Backend Testing

```bash
cd backend
source venv/bin/activate

# Run test suite
python test_api.py

# Test specific endpoint
curl http://localhost:8000/api/todos
```

### Frontend Testing

```bash
cd frontend

# Check for TypeScript errors
npm run build

# Run dev server
npm run dev

# Test in browser
open http://localhost:3000
```

### Integration Testing

1. Start both backend and frontend
2. Test full user flow:
   - Connect to meeting
   - Generate todos
   - Extract calendar events
   - Create notes
   - Ask chatbot questions
3. Check browser console for errors (F12)
4. Check backend terminal for logs

---

## 🐛 Common Issues

### "Module not found"
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### "Port already in use"
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python -m uvicorn app.main:app --reload --port 8001
```

### "Merge conflict"
```bash
# Pull latest
git pull origin main

# Resolve conflicts in files (look for <<<<<<< markers)
# Edit files to keep correct version

# Mark as resolved
git add .
git commit -m "Resolve merge conflicts"
git push
```

### ".env file missing"
```bash
# Backend
cd backend
cp .env.example .env
# Add your GEMINI_API_KEY

# Frontend
cd frontend
cp .env.local.example .env.local
```

---

## 📞 Communication

### Use GitHub Issues
- Create issues for bugs and features
- Assign to team members
- Use labels: `bug`, `enhancement`, `documentation`

### Use Pull Request Comments
- Review each other's code
- Ask questions
- Suggest improvements

### Daily Standup (Recommended)
- What did you work on yesterday?
- What will you work on today?
- Any blockers?

---

## 🎯 Hackathon Tips

### Divide and Conquer
- **Person 1**: Backend improvements (real integrations)
- **Person 2**: Frontend polish (UI/UX)
- **Person 3**: Testing, docs, deployment

### Stay Synced
- Push code frequently
- Pull before starting work
- Communicate what you're working on

### Focus on Demo
- Make sure core features work perfectly
- Polish the user experience
- Practice the demo together

### Documentation
- Update README as you add features
- Document new API endpoints
- Keep HACKATHON_PITCH.md current

---

## 🔐 Security Reminders

### DO NOT commit:
- ❌ API keys (GEMINI_API_KEY)
- ❌ .env files
- ❌ Personal credentials
- ❌ Database files

### DO commit:
- ✅ Source code
- ✅ .env.example templates
- ✅ Documentation
- ✅ Configuration files

### If someone commits API keys:
1. Immediately rotate the key (get new one)
2. Remove from Git history (see above)
3. Update .env files locally

---

## 📚 Resources

- **Project Docs**: See README.md, ARCHITECTURE.md
- **Pitch Materials**: HACKATHON_PITCH.md, EXECUTIVE_SUMMARY.md
- **Demo Script**: DEMO_SCRIPT.md
- **Git Help**: This file!

---

## ✅ Setup Checklist

- [ ] Cloned repository
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] .env file created with GEMINI_API_KEY
- [ ] Backend runs successfully
- [ ] Frontend runs successfully
- [ ] Can access app at http://localhost:3000
- [ ] Tested basic features
- [ ] Read project documentation
- [ ] Understand Git workflow
- [ ] Added as collaborator on GitHub

---

## 🎉 You're Ready!

Once you've completed the checklist, you're ready to start contributing!

**Questions?** Ask in your team chat or create a GitHub issue.

**Happy hacking!** 🚀
