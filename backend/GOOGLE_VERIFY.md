# Verify Google Setup – CatchUp

Use this checklist to confirm everything is using Google services and working.

---

## 1. Environment (backend)

From the **backend** folder, confirm your `.env` has:

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Gemini (embeddings, RAG, fallback STT) |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID – **required for Cloud Speech-to-Text** |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to `gcp-key.json` (e.g. `./gcp-key.json` from backend dir) |
| `GOOGLE_CLOUD_STT_BUCKET` | **Optional.** For audio longer than ~1 min (e.g. lectures): create a GCS bucket in your project and set its name here. Long audio is uploaded to this bucket and transcribed via batch API—**no ffmpeg or pydub needed**. |

**Path tip:** If you run the server from `backend/`, use `./gcp-key.json`. If you run from project root, use `backend/gcp-key.json` or an absolute path.

---

## 2. Backend starts without errors

```bash
cd backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- You should see: `Uvicorn running on http://0.0.0.0:8000`
- Ignore the `google.generativeai` FutureWarning for now.

---

## 3. Health check

```bash
curl http://localhost:8000/
```

Expected: `{"status":"healthy","service":"CatchUp API","version":"1.0.0"}`

---

## 4. Google Cloud Speech-to-Text (audio upload)

1. Create a short audio file (e.g. 5–10 seconds, MP3 or WAV) or use any short recording.
2. Upload it:

```bash
curl -X POST "http://localhost:8000/api/audio/upload?session_id=verify-google-stt" \
  -F "audio=@/path/to/your/audio.mp3"
```

- **Success:** `{"status":"success", ...}`
- Then get the transcript:

```bash
curl "http://localhost:8000/api/transcript/verify-google-stt"
```

You should see `chunks` with transcribed text. If `GOOGLE_CLOUD_PROJECT` and credentials are set, transcription is from **Google Cloud Speech-to-Text**.

---

## 4b. Long audio (lectures 60–120 min) – no ffmpeg

Sync recognition is limited to 60 seconds. For longer files (e.g. full lectures):

1. **Create a GCS bucket** in the same project:
   - Open [Cloud Console → Storage](https://console.cloud.google.com/storage).
   - Create bucket (e.g. `catchup-stt`), same region if you prefer.
2. **Grant the service account write access** (required or you get 403):
   - Open the bucket → **Permissions** tab → **Grant access**.
   - New principal: `catchup-speech@niyati-cheesehacks.iam.gserviceaccount.com` (or the `client_email` from your `gcp-key.json`).
   - Role: **Storage Object Creator** → Save.
   - See **backend/GCS_BUCKET_FIX.md** for step-by-step.
3. **In `.env` add:**  
   `GOOGLE_CLOUD_STT_BUCKET=catchup-stt`  
   (use your bucket name.)
4. **Restart the backend.** Uploads larger than ~1 MB will be sent to this bucket and transcribed via the batch API (takes a few minutes for long files). No ffmpeg or pydub required. Transcription uses only Cloud Speech-to-Text (no Gemini).

---

## 5. Google Meet path (webhook = Meet under the hood)

The endpoint is still called `/api/zoom/webhook` for API compatibility, but it **uses Google Meet** logic (`app.meet`):

```bash
curl -X POST "http://localhost:8000/api/zoom/webhook" \
  -H "Content-Type: application/json" \
  -d '{"meeting_id":"test-meet-1","transcript_chunk":{"timestamp":"00:00:00","text":"Hello from Google Meet flow","speaker":"Speaker 1"}}'
```

Expected: `{"status":"success"}`. Session ID in the store will be `meet_test-meet-1`.

---

## 6. What’s already Google

| Feature | Google service | Where |
|---------|----------------|------|
| Embeddings | Gemini | `gemini_client.py`, `store.py` |
| RAG / recap / Q&A | Gemini | `rag.py`, `chatbot.py`, `content_manager.py` |
| Speech-to-text | **Cloud Speech-to-Text** (primary) + Gemini fallback | `stt.py` |
| Meeting transcript webhook | **Google Meet** (via `meet.py`) | `zoom.py` → `meet.py` |
| Optional: fetch Meet transcript | Meet REST API | `meet.py` (when enabled) |

---

## 7. If something fails

- **Cloud Speech-to-Text:**  
  - Enable [Cloud Speech-to-Text API](https://console.cloud.google.com/apis/library/speech.googleapis.com) for your project.  
  - Check `GOOGLE_CLOUD_PROJECT` and `GOOGLE_APPLICATION_CREDENTIALS`; restart the server after changing `.env`.
- **Import errors:** Ensure `vector_store` is defined at the bottom of `app/store.py` and that you’re in the `backend` directory (or `PYTHONPATH` includes it).
- **Gemini:** Ensure `GEMINI_API_KEY` is set and valid.

Once 1–5 pass, your app is using Google (Gemini + Cloud Speech-to-Text + Meet) end to end.
