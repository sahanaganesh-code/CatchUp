from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration. Google-first: Gemini, Meet, Calendar, Gmail, Drive, Tasks, Docs, Slides."""

    # --- Google AI (Gemini) ---
    gemini_api_key: str

    # --- API Authentication (optional) ---
    api_key: Optional[str] = None

    # --- Rate limiting ---
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

    # --- Google Meet (live captions / transcript ingestion) ---
    google_meet_webhook_secret: Optional[str] = None  # Verify Meet webhook payloads

    # --- Google OAuth2 (for Calendar, Gmail, Drive, Tasks, Docs, Slides) ---
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_credentials_path: Optional[str] = None  # Service account or OAuth token path

    # --- Google Calendar ---
    google_calendar_enabled: bool = True

    # --- Gmail ---
    gmail_enabled: bool = True

    # --- Google Drive (store transcripts, recordings) ---
    google_drive_folder_id: Optional[str] = None

    # --- Google Tasks ---
    google_tasks_list_id: Optional[str] = None  # Default task list

    # --- Google Docs (notes) ---
    google_docs_enabled: bool = True

    # --- Google Slides (action: create slides) ---
    google_slides_enabled: bool = True

    # --- ChromaDB (vector store; can later sync to Drive) ---
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "catchup_transcripts_gemini"

    # --- Gemini models ---
    gemini_model: str = "gemini-1.5-flash"
    gemini_embed_model: str = "models/gemini-embedding-001"

    # --- RAG ---
    min_evidence_quotes: int = 2
    max_evidence_quotes: int = 5
    retrieval_top_k: int = 10

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
