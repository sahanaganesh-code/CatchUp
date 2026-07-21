from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # API Keys
    gemini_api_key: str
    
    # Google Workspace (optional for future integration)
    google_calendar_enabled: bool = False

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "catchup_transcripts_gemini"
    
    # Models - Using Google's Gemini for everything
    gemini_model: str = "gemini-flash-lite-latest"  # Fast, efficient for meeting analysis
    gemini_embed_model: str = "models/gemini-embedding-001"  # Optimized embeddings
    
    # RAG Settings
    min_evidence_quotes: int = 2
    max_evidence_quotes: int = 5
    retrieval_top_k: int = 10
    chunk_size: int = 500  # Optimal for meeting transcripts
    chunk_overlap: int = 50
    
    # AI Generation Settings
    default_temperature: float = 0.3  # Lower for factual meeting analysis
    max_output_tokens: int = 2048
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Comma-separated list of allowed frontend origins for CORS
    cors_origins: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
