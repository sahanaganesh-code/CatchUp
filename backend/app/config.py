from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

# Always load .env from backend/ so it works no matter where uvicorn is run from
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # API Keys (optional if embeddings_use_local=True and recap/QA are local)
    gemini_api_key: Optional[str] = None
    # Optional: use OpenAI for recap (paraphrased bullets, avoids Gemini rate limits)
    openai_api_key: Optional[str] = None
    
    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "catchup_transcripts_gemini"
    
    # Use gemini-2.0-flash (gemini-1.5-flash returns 404 on v1beta)
    gemini_model: str = "gemini-2.0-flash"
    # Optional fallback when primary hits quota (e.g. gemini-2.0-flash-lite)
    gemini_model_fallback: Optional[str] = None
    gemini_embed_model: str = "models/gemini-embedding-001"
    
    # RAG Settings
    min_evidence_quotes: int = 2
    max_evidence_quotes: int = 5
    retrieval_top_k: int = 10
    # Recap: when True use local summarizer only (no API). When False try OpenAI then Gemini.
    recap_use_local: bool = True
    openai_recap_model: str = "gpt-4o-mini"
    # Q&A: when True use local answer from retrieved chunks (no API). When False use Gemini.
    qa_use_local: bool = True
    # Embeddings: when True do not call Gemini for ingest or retrieval (use keyword-only retrieval). Avoids quota.
    embeddings_use_local: bool = True
    # Local LLM (Ollama): no API keys, no rate limits. Run: ollama serve && ollama run llama3.2
    use_local_llm: bool = True
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Google Cloud (Speech-to-Text, optional Meet API) – read from env
    google_cloud_project: Optional[str] = None
    google_application_credentials: Optional[str] = None
    # For long audio (>60s): upload to this GCS bucket, then use batch_recognize (no ffmpeg needed)
    google_cloud_stt_bucket: Optional[str] = None
    
    class Config:
        env_file = str(_ENV_FILE) if _ENV_FILE.exists() else ".env"
        case_sensitive = False
        extra = "ignore"  # allow other env vars (e.g. CATCHUP_*) without errors


settings = Settings()
