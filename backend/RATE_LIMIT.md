# When you hit rate limit (429 / quota exceeded)

Do this so **Recap** still works with no API calls.

---

## 1. In `backend/.env` add or change this line:

```env
RECAP_USE_LOCAL=true
```

Save the file.

---

## 2. Restart the backend

Stop the server (Ctrl+C), then start it again:

```bash
cd backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 3. Use Recap again

**Generate Recap** will now use only the local summarizer. It does **not** call OpenAI or Gemini, so there is **no rate limit** for recap. You get key points extracted from the transcript (short bullets, no API).

When your quota resets, set `RECAP_USE_LOCAL=false` again and restart if you want AI paraphrased bullets.

---

## Other features (Q&A, Propose actions, Chatbot)

Those still use Gemini. If you hit rate limit there, you’ll see “Gemini rate limit reached” and need to wait a bit (e.g. a minute) or try again later. Recap is the only part we can run fully offline with the local summarizer.
