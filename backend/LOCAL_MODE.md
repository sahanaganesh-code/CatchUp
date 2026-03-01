# Local mode — Summary & Q&A without API (no rate limits)

CatchUp can run **Recap** and **Q&A** with **no external LLM/API calls**, so you never hit rate limits on free tiers.

## What runs locally

| Feature | Local behavior | Project rule |
|--------|----------------|--------------|
| **Recap** | Key points extracted from transcript (scoring + dedup). No summary block; bullets only, ≤25 words each, complete thoughts. | Evidence-style recap; key points only. |
| **Q&A** | Keyword retrieval over stored chunks + short synthesis from top quote. Always returns **2–5 evidence quotes with timestamps**. | Every answer grounded in transcript; 2–5 quotes. |

## Config (default: local)

In `backend/.env`:

```env
# Recap: true = local only (no API). false = try OpenAI then Gemini.
RECAP_USE_LOCAL=true

# Q&A: true = local retrieval + local answer (no API). false = Gemini.
QA_USE_LOCAL=true
```

With both `true` (default), **Recap** and **Q&A** use **zero** Gemini/OpenAI calls after transcript is in the store.

## Ingest (transcript storage)

Ingesting transcript (e.g. after upload or Zoom webhook) still uses **Gemini embeddings** once per session so ChromaDB can do semantic search. If you later set `QA_USE_LOCAL=true`, Q&A uses **keyword search** over the same stored text, so no extra API calls at answer time. For fully zero-API ingest you’d need a separate local embedding path (e.g. sentence-transformers); current setup keeps ingest on Gemini.

## When to use API again

Set `RECAP_USE_LOCAL=false` and/or `QA_USE_LOCAL=false` when you have quota and want:

- **Recap:** Paraphrased, AI-written bullets (OpenAI or Gemini).
- **Q&A:** Full natural-language answers from Gemini instead of the short local synthesis.

Restart the backend after changing `.env`.

## Aligns with PROJECT_SUMMARY.md

- **Evidence-based answers:** Local Q&A still returns 2–5 evidence quotes with timestamps.
- **Recap:** Key points only (no summary block in local mode); bullets are complete thoughts, ≤25 words.
- **No speculation:** Local Q&A answer is built only from retrieved chunks; “Insufficient evidence” when &lt; 2 quotes.
