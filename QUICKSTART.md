# CatchUp - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.9+
- Node.js 18+
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

## Step 1: Clone & Navigate

```bash
cd catchup
```

## Step 2: Backend Setup (2 minutes)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env and add your Gemini API key:
# GEMINI_API_KEY=your-key-here
# Note: GEMINI_EMBED_MODEL should be models/text-embedding-004

# Start backend
python -m uvicorn app.main:app --reload
```

Backend runs at: http://localhost:8000

## Step 3: Frontend Setup (2 minutes)

Open a new terminal:

```bash
cd catchup/frontend

# Install dependencies
npm install

# Setup environment
cp .env.local.example .env.local

# Start frontend
npm run dev
```

Frontend runs at: http://localhost:3000

## Step 4: Try It Out! (1 minute)

1. Open http://localhost:3000
2. Choose "Zoom Meeting Mode" or "In-Person Lecture Mode"
3. Enter a session ID (e.g., "test-meeting-123")
4. Click "Connect" or "Start Session"

### Test the Features:

**Generate Recap:**
- Click "Generate Recap" button
- See summary with evidence quotes

**Ask Questions:**
- Type: "What were the main topics discussed?"
- Get answer with 2-5 timestamped evidence quotes

**Propose Actions:**
- Click "Propose Actions"
- Review suggested tasks/events
- Click "Approve & Execute" (note: stubs for hackathon)

## Quick Test with Sample Data

The app includes mock transcript data that loads automatically when you connect. This lets you test all features immediately without real audio!

## Troubleshooting

**"Module not found" error:**
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

**"Gemini API key not found":**
- Edit `backend/.env`
- Add: `GEMINI_API_KEY=your-key-here`

**Port already in use:**
- Backend: Change port in `backend/app/config.py`
- Frontend: Use `npm run dev -- -p 3001`

## What's Next?

- Read the full [README.md](README.md) for detailed documentation
- Check [.cursorrules](.cursorrules) for project rules
- Explore the code structure in `backend/app/` and `frontend/app/`

## Need Help?

- Check backend logs in terminal
- Open browser console (F12) for frontend errors
- Verify both servers are running

Happy hacking! 🚀
