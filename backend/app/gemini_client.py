"""
Gemini API client wrapper for embeddings and text generation.
Uses google.generativeai package with REST transport to avoid gRPC issues.
"""
import google.generativeai as genai
from app.config import settings
import logging
import os

logger = logging.getLogger(__name__)

# Set environment variable to use REST instead of gRPC
os.environ['GOOGLE_API_USE_CLIENT_CERTIFICATE'] = 'false'

# Configure Gemini with API key
genai.configure(api_key=settings.gemini_api_key, transport='rest')


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """
    Embed texts using Gemini embedding model.
    
    Args:
        texts: List of text strings to embed
        task_type: Either "RETRIEVAL_DOCUMENT" for stored chunks or "RETRIEVAL_QUERY" for queries
    
    Returns:
        List of embedding vectors (list of floats)
    """
    try:
        logger.info(f"Embedding {len(texts)} texts with task_type={task_type}")
        
        # Use google.generativeai.embed_content
        result = genai.embed_content(
            model=settings.gemini_embed_model,
            content=texts,
            task_type=task_type
        )
        
        # result['embedding'] contains the embeddings
        embeddings = result['embedding']
        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings
    
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise


def generate_text(prompt: str, model: str = None) -> str:
    """
    Generate text using Gemini model.
    
    Args:
        prompt: The prompt text
        model: Model name (defaults to settings.gemini_model)
    
    Returns:
        Generated text string
    """
    if model is None:
        model = settings.gemini_model
    
    try:
        logger.info(f"Generating text with model={model}")
        
        # Use google.generativeai.GenerativeModel
        gen_model = genai.GenerativeModel(model)
        response = gen_model.generate_content(prompt)
        
        text = response.text
        logger.info(f"Successfully generated {len(text)} characters")
        return text
    
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        raise
