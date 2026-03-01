# Local LLM (Ollama) — Your own LLM for Recap & Q&A

No API keys. No rate limits. Recap and Q&A run on a **real LLM** on your machine.

## 1. Install Ollama

- **macOS / Linux:** https://ollama.com — download and install.
- **Windows:** same from the website.

## 2. Start Ollama and pull a model

In a terminal:

```bash
# Start the server (often starts automatically after install)
ollama serve

# In another terminal: pull a small, fast model (one-time)
ollama run llama3.2
```

`llama3.2` is a good default (~2B params). You can also use `phi`, `gemma2:2b`, or `mistral`:

```bash
ollama run phi
# or
ollama run gemma2:2b
```

Set the same name in `.env` as `OLLAMA_MODEL=phi` (or whatever you ran).

## 3. Backend config

In `backend/.env`:

```env
USE_LOCAL_LLM=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
RECAP_USE_LOCAL=true
QA_USE_LOCAL=true
```

Restart the backend. On startup you should see:

- `Local LLM (Ollama): on`
- `Recap: local (Ollama)`
- `Q&A: local (Ollama)`

## 4. What uses the LLM

- **Recap:** The local LLM gets the full transcript and returns short bullet-point key points (paraphrased, no quotes).
- **Q&A:** The local LLM gets the question + retrieved evidence and returns an answer grounded in that evidence (still 2–5 quotes with timestamps).

If Ollama is not running or the model isn’t available, the app falls back to extractive recap and keyword-based answer synthesis.

## 5. Summary

| Step              | Command / config                          |
|-------------------|--------------------------------------------|
| Install           | Download from https://ollama.com           |
| Run server        | `ollama serve`                             |
| Pull model        | `ollama run llama3.2`                      |
| Backend .env      | `USE_LOCAL_LLM=true`, `OLLAMA_MODEL=llama3.2` |
| Restart backend   | So it connects to Ollama                   |

You now have **your own LLM** powering summary and Q&A with no external APIs.
