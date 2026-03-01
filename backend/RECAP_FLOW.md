# How recap works

Recap turns the **full meeting transcript** into **short, paraphrased bullet-point notes** (like lecture jots). No quotes from the transcript.

## Provider order (no Google Cloud changes)

1. **OpenAI** — If `OPENAI_API_KEY` is set in `.env`, recap uses OpenAI (e.g. `gpt-4o-mini`) for paraphrased, short bullets. Avoids Gemini rate limits.
2. **Local** — If `RECAP_USE_LOCAL=true`, recap uses the in-app extractive summarizer (no paraphrase; transcript excerpts).
3. **Gemini** — Otherwise we use Google Gemini. Same short-bullet prompt; can hit rate limits.

**For the hackathon:** Set `OPENAI_API_KEY=sk-...` in backend `.env`, run `pip install openai`, restart backend. Recap will use OpenAI and return short, paraphrased bullets.

## What recap is

Recap = **bullet list of key points** in the model’s own words. It must:

- Paraphrase, synthesize, and abstract ideas
- Group related concepts
- **Not** return direct quotes, copy sentences from the transcript, output transcript excerpts, or include timestamps

The result looks like clean lecture/meeting notes — no JSON, no rigid schema, just a structured bullet list.

## Step by step

1. **Transcript is stored**  
   When you ingest a meeting (e.g. upload audio → speech-to-text, or Zoom/Meet webhook), we save the transcript as chunks in the vector store (ChromaDB) for that session.

2. **You click “Generate Recap”**  
   The frontend calls `POST /api/recap` with your `session_id`.

3. **Backend loads the full transcript**  
   We load **all** chunks for that session and concatenate them into one transcript string.

4. **We call Gemini with system + user content**  
   - **System message:** Defines the assistant as a meeting-intelligence helper; instructs it to rewrite in its own words, not quote, not copy, not include timestamps or speaker labels; group related ideas; focus on themes, decisions, action items, insights.  
   - **User message:** “Here is the full meeting transcript. Generate a concise but comprehensive bulleted summary of all key points discussed.” plus the full transcript.

5. **We return the result**  
   We parse Gemini’s bullet list into `summary` (full text) and `key_points` (list of bullets). We do **not** attach evidence quotes; recap is notes only.

## If Gemini fails (429, 403, network, etc.)

- On **429 (rate limit)** we return **503** and the client can retry.
- On other errors we return **200** with a short message in `summary` explaining that recap could not be generated and the user should try again or check API key/quota. No transcript excerpts or quotes are ever returned.

## 503 and rate limiting

- Recap uses the same Gemini client as elsewhere: on 429 we retry up to 2 times, then try fallback model if configured, then raise `GeminiQuotaExceeded` → API returns **503**.
- Other errors (403, 404, 500) are logged; we return 200 with an error message in the recap body (no crash).
