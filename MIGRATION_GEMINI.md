# Migration Guide: OpenAI to Gemini

This document explains the changes made to switch from OpenAI to Google Gemini.

## What Changed

### 1. Dependencies
- **Removed**: `openai==1.12.0`
- **Added**: `google-genai==0.2.2`

### 2. API Keys
- **Old**: `OPENAI_API_KEY`
- **New**: `GEMINI_API_KEY`

Get your Gemini API key here: https://aistudio.google.com/app/apikey

### 3. Configuration Variables
In `backend/.env`:
- `OPENAI_API_KEY` → `GEMINI_API_KEY`
- `EMBEDDING_MODEL` → `GEMINI_EMBED_MODEL` (default: `text-embedding-004`)
- `LLM_MODEL` → `GEMINI_MODEL` (default: `gemini-2.0-flash-exp`)

### 4. ChromaDB Collection
The collection name changed from `catchup_transcripts` to `catchup_transcripts_gemini` to avoid mixing OpenAI and Gemini embedding spaces.

**Important**: If you have existing data with OpenAI embeddings, it will not be accessible with the new collection name. This is intentional to prevent compatibility issues.

## Migration Steps

### For New Installations
1. Install dependencies: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env`
3. Add your `GEMINI_API_KEY`
4. Start the server

### For Existing Installations

#### Option 1: Fresh Start (Recommended)
1. Update dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Update your `.env` file:
   ```bash
   # Remove
   OPENAI_API_KEY=...
   EMBEDDING_MODEL=text-embedding-3-small
   LLM_MODEL=gpt-4-turbo-preview
   
   # Add
   GEMINI_API_KEY=your-key-here
   GEMINI_MODEL=gemini-2.0-flash-exp
   GEMINI_EMBED_MODEL=text-embedding-004
   ```

3. Delete old ChromaDB data (optional):
   ```bash
   rm -rf chroma_db/
   ```

4. Restart the server

#### Option 2: Keep Old Data
If you want to keep your old OpenAI-embedded data:

1. Change the collection name in `app/config.py`:
   ```python
   chroma_collection_name: str = "catchup_transcripts"  # Keep old name
   ```

2. **Warning**: This will cause embedding space mismatch. Queries may not work correctly because OpenAI and Gemini embeddings are not compatible.

## Technical Details

### Embedding Changes
- **OpenAI**: Used `text-embedding-3-small` (1536 dimensions)
- **Gemini**: Uses `text-embedding-004` (768 dimensions)

These are different embedding spaces and cannot be mixed.

### Task Types
Gemini embeddings support task types for better retrieval:
- `RETRIEVAL_DOCUMENT`: Used when storing transcript chunks
- `RETRIEVAL_QUERY`: Used when querying for relevant chunks

This optimization improves retrieval accuracy.

### API Differences

**OpenAI (Old)**:
```python
from openai import OpenAI
client = OpenAI(api_key=settings.openai_api_key)

# Embeddings
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=texts
)

# Text generation
response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[...]
)
```

**Gemini (New)**:
```python
from google import genai
from google.genai import types
client = genai.Client()  # Reads GEMINI_API_KEY from env

# Embeddings
result = client.models.embed_content(
    model="text-embedding-004",
    contents=texts,
    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
)

# Text generation
response = client.models.generate_content(
    model="gemini-2.0-flash-exp",
    contents=prompt
)
```

## Testing

After migration, run the test suite:
```bash
cd backend
python test_api.py
```

All tests should pass with the new Gemini backend.

## Troubleshooting

### "GEMINI_API_KEY not found"
- Make sure you've updated your `.env` file
- Restart the backend server after changing `.env`

### "Embedding dimension mismatch"
- Delete the old `chroma_db/` directory
- The new collection will be created automatically

### "No results from queries"
- Ensure you're using the new collection name
- Re-ingest your transcript data with Gemini embeddings

### "API rate limit exceeded"
- Gemini has different rate limits than OpenAI
- Check your quota at https://aistudio.google.com/

## Benefits of Gemini

1. **Cost**: Gemini is generally more cost-effective
2. **Speed**: Gemini 2.0 Flash is optimized for low latency
3. **Task-specific embeddings**: Better retrieval with task types
4. **Multimodal**: Future support for images/video (not used yet)

## Rollback

If you need to rollback to OpenAI:

1. Checkout the previous version of the code
2. Restore your old `.env` with `OPENAI_API_KEY`
3. Restore old `chroma_db/` backup if you have one
4. Run `pip install -r requirements.txt`

## Questions?

Check the updated documentation:
- `README.md` - Updated setup instructions
- `QUICKSTART.md` - Updated quick start guide
- `ARCHITECTURE.md` - Updated architecture diagrams
