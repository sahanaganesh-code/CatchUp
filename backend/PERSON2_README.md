# Person 2 (Data & Integration) – Niyati branch

This branch implements all Person 2 tasks from `BACKEND_WORK_SPLIT.md` using **Google** services (Google-sponsored hackathon).

## Summary of changes

### 1. Google Meet instead of Zoom
- **`app/meet.py`** (new): Google Meet integration.
  - `process_meet_webhook(meeting_id, transcript_chunk)` – same contract as Zoom webhook.
  - `simulate_meet_transcript(meeting_id, chunks)` – for testing.
  - `fetch_meet_transcript_entries(...)` – optional: fetch transcript from Meet REST API (`conferenceRecords.transcripts.entries`) when `GOOGLE_MEET_API_ENABLED=true` and credentials are set.
  - `ingest_meet_transcript_from_api(...)` – fetch + ingest in one call.
- **`app/zoom.py`** (updated): Keeps the same public API (`process_zoom_webhook`, `simulate_zoom_transcript`, `get_zoom_session_id`) but **delegates to `app.meet`**. So the app uses Google Meet under the hood; no changes needed in `main.py` (avoids merge conflicts with Person 3).

### 2. Google Cloud Speech-to-Text (primary STT) + Gemini fallback
- **`app/stt.py`**: **Google Cloud Speech-to-Text** is the primary STT (for the “use Google Cloud well” hackathon award). Gemini is used as fallback when Cloud STT is not configured or fails.
  - `transcribe_audio(session_id, audio_file_path)` – Cloud Speech-to-Text v2 (auto decoding, word time offsets); fallback Gemini.
  - `transcribe_audio_bytes(audio_data, mime_type)` – same: Cloud STT first, then Gemini.
  - `process_audio_upload(session_id, audio_data)` – used by `POST /api/audio/upload`; transcribes with Cloud STT (or Gemini) and adds chunks to the vector store. Upload limit 300MB. **Long audio (60–120 min):** audio is split into ~55s chunks (pydub + ffmpeg), each transcribed then merged.
  - Requires `GOOGLE_CLOUD_PROJECT` and Application Default Credentials (or `GOOGLE_APPLICATION_CREDENTIALS`) for Cloud STT. If unset, only Gemini is used.

### 3. ChromaDB and caching
- **`app/store.py`** (updated):
  - **Query cache**: In-memory cache for `query_chunks()` (TTL 5 min, max 200 entries). Cache key: `(session_id, query_text, top_k)`. Cache is cleared for a session when `delete_session()` is called.
  - **Indexing**: Metadata “speaker” truncated to 200 chars for ChromaDB limits; explicit `include` in `query`/`get` where needed.
  - No changes to public method signatures, so RAG/chatbot (Person 1) and main (Person 3) keep working.

### 4. Data persistence for notes/todos/events
- **`app/persistence.py`** (new): File-based persistence (JSON) for notes, todos, and calendar events.
  - `load_notes_store()` / `save_notes_store(notes_dict)`  
  - `load_todos_store()` / `save_todos_store(todos_dict)`  
  - `load_events_store()` / `save_events_store(events_dict)`  
  - Data dir: `CATCHUP_PERSIST_DIR` (default `./data`).  
  - **Usage**: Person 1’s `content_manager` can optionally call these at startup/shutdown or on each write to persist in-memory stores to disk. This branch does **not** modify `content_manager.py` to avoid merge conflicts.

### 5. Dependencies
- **`requirements.txt`**:
  - `google-cloud-speech` – **Google Cloud Speech-to-Text** (primary STT).
  - `google-api-python-client`, `google-auth` – optional, for Meet API (`fetch_meet_transcript_entries` / `ingest_meet_transcript_from_api`).

## Merge conflict avoidance

- **main.py**: Unchanged. Still imports `app.zoom` and `app.stt`; zoom delegates to meet, stt uses Cloud Speech-to-Text (primary) + Gemini fallback.
- **models.py**: Unchanged. `ZoomWebhookPayload` is still used for the webhook payload; Meet uses the same shape.
- **config.py**: Unchanged (Person 3 owns it). Cache/persistence use module-level/env defaults.
- **content_manager.py**: Unchanged (Person 1). Persistence is available in `app.persistence` when they want to plug it in.

## Env

- **Google Cloud Speech-to-Text (STT)**  
  - `GOOGLE_CLOUD_PROJECT` – your GCP project ID (required for Cloud STT; if unset, only Gemini fallback is used).  
  - `GOOGLE_APPLICATION_CREDENTIALS` – path to service account JSON (or use Application Default Credentials).
- **Optional: Meet API**  
  - `GOOGLE_MEET_API_ENABLED=true` – enable fetching transcripts from Meet REST API.  
- `CATCHUP_PERSIST_DIR` – directory for notes/todos/events JSON (default `./data`).

## Files touched (Person 2 only)

| File            | Action   |
|-----------------|----------|
| `app/meet.py`   | New      |
| `app/zoom.py`   | Modified (delegate to meet) |
| `app/stt.py`    | Google Cloud Speech-to-Text (primary) + Gemini fallback |
| `app/store.py`  | Modified (cache + small indexing tweaks) |
| `app/persistence.py` | New  |
| `requirements.txt` | Modified (optional Meet deps) |
| `backend/PERSON2_README.md` | New (this file) |
