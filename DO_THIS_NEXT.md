# Fix "503 / TypeError: fetch failed" — Do This Next

The **503** and **"TypeError: fetch failed"** on audio upload mean the **frontend cannot reach the backend**. The app code and merge are fine; the backend process just has to be running.

## 1. Start the backend (required)

Open a terminal and run:

```bash
cd /Users/niyati/Desktop/CatchUp/backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

(Use `python3` if `python` is not available.)

Leave this terminal open. You should see something like:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

If the backend **crashes on startup** (e.g. `ModuleNotFoundError` or exit code 139):

- Install deps: `pip install -r requirements.txt`
- Ensure you have a `backend/.env` with at least `GEMINI_API_KEY=...` (see `backend/.env.example`)

## 2. Start the frontend

In a **second** terminal:

```bash
cd /Users/niyati/Desktop/CatchUp/frontend
npm run dev
```

## 3. Check the UI

- Open the app in the browser (e.g. http://localhost:3000).
- If the backend is not running, you’ll see an amber banner: **"Backend not connected"** with the start command.
- Once the backend is running, that banner should disappear (it refreshes every 10 seconds).

Then try **In-Person Lecture Mode** → start a session → upload audio again. The 503 should stop.

## If the backend still won’t start

- **Port in use:** Something else may be using port 8000. Stop it or use another port, e.g. `--port 8001`, and set in the frontend: `BACKEND_URL=http://127.0.0.1:8001` (e.g. in `frontend/.env.local`).
- **Chromadb / segfault (exit 139):** Try a fresh virtualenv and `pip install -r requirements.txt` again. If it still crashes, say what you see in the backend terminal and we can narrow it down.

Nothing was overwritten by the merge that would break this; the backend and proxy are still set to port 8000. You just need the backend process running whenever you use the app.
