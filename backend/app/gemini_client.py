"""
Gemini API client wrapper for embeddings and text generation.
Uses google.generativeai package with REST transport to avoid gRPC issues.
Optimized for Google Workspace integration and Google Meet transcripts.
"""
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from app.config import settings
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Set environment variable to use REST instead of gRPC
os.environ['GOOGLE_API_USE_CLIENT_CERTIFICATE'] = 'false'

# Configure Gemini with API key
genai.configure(api_key=settings.gemini_api_key, transport='rest')

# Safety settings optimized for professional meeting content
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# Generation config optimized for meeting analysis
GENERATION_CONFIG = {
    "temperature": 0.3,  # Lower temperature for more factual, consistent outputs
    "top_p": 0.8,
    "top_k": 40,
    "max_output_tokens": 2048,
}


def embed_texts(texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """
    Embed texts using Gemini embedding model.
    Optimized for Google Meet transcript chunks and meeting content.
    
    Args:
        texts: List of text strings to embed
        task_type: Either "RETRIEVAL_DOCUMENT" for stored chunks or "RETRIEVAL_QUERY" for queries
    
    Returns:
        List of embedding vectors (list of floats)
    """
    try:
        logger.info(f"Embedding {len(texts)} texts with task_type={task_type}")
        
        # Use google.generativeai.embed_content with optimized settings
        result = genai.embed_content(
            model=settings.gemini_embed_model,
            content=texts,
            task_type=task_type,
            title="Meeting Transcript Analysis" if task_type == "RETRIEVAL_DOCUMENT" else None
        )
        
        # result['embedding'] contains the embeddings
        embeddings = result['embedding']
        logger.info(f"Successfully generated {len(embeddings)} embeddings")
        return embeddings
    
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise


def generate_text(
    prompt: str, 
    model: str = None,
    temperature: Optional[float] = None,
    system_instruction: Optional[str] = None
) -> str:
    """
    Generate text using Gemini model with Google-optimized settings.
    
    Args:
        prompt: The prompt text
        model: Model name (defaults to settings.gemini_model)
        temperature: Override default temperature (0.3)
        system_instruction: Optional system instruction for better context
    
    Returns:
        Generated text string
    """
    if model is None:
        model = settings.gemini_model
    
    try:
        logger.info(f"Generating text with model={model}")
        
        # Prepare generation config
        gen_config = GENERATION_CONFIG.copy()
        if temperature is not None:
            gen_config["temperature"] = temperature
        
        # Use google.generativeai.GenerativeModel with optimized settings
        gen_model = genai.GenerativeModel(
            model,
            generation_config=gen_config,
            safety_settings=SAFETY_SETTINGS,
            system_instruction=system_instruction
        )
        
        response = gen_model.generate_content(prompt)
        
        text = response.text
        logger.info(f"Successfully generated {len(text)} characters")
        return text
    
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        raise


def generate_structured_output(
    prompt: str,
    response_schema: Optional[Dict[str, Any]] = None,
    model: str = None
) -> str:
    """
    Generate structured output (JSON) using Gemini with schema validation.
    Useful for extracting todos, events, and structured meeting data.
    
    Args:
        prompt: The prompt text
        response_schema: Optional JSON schema for structured output
        model: Model name (defaults to settings.gemini_model)
    
    Returns:
        Generated structured text
    """
    if model is None:
        model = settings.gemini_model
    
    try:
        logger.info(f"Generating structured output with model={model}")
        
        gen_config = GENERATION_CONFIG.copy()
        gen_config["temperature"] = 0.1  # Very low temperature for structured output
        
        if response_schema:
            gen_config["response_mime_type"] = "application/json"
            gen_config["response_schema"] = response_schema
        
        gen_model = genai.GenerativeModel(
            model,
            generation_config=gen_config,
            safety_settings=SAFETY_SETTINGS,
            system_instruction="You are a precise meeting analysis assistant. Always output valid JSON."
        )
        
        response = gen_model.generate_content(prompt)
        text = response.text
        logger.info(f"Successfully generated structured output: {len(text)} characters")
        return text
    
    except Exception as e:
        logger.error(f"Error generating structured output: {e}")
        raise
