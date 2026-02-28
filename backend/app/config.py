from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # API Keys
    gemini_api_key: str
    
    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "catchup_transcripts_gemini"
    
    # Models
    gemini_model: str = "gemini-1.5-flash"
    gemini_embed_model: str = "models/gemini-embedding-001"
    
    # RAG Settings
    min_evidence_quotes: int = 2
    max_evidence_quotes: int = 5
    retrieval_top_k: int = 10
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
