"""
Quick test to verify Gemini API works
"""
from google import genai
import os

# Set API key
api_key = "AIzaSyBWUL7NiLuySvvvO6vHmpOR9jnRhywrfgY"

print("Testing Gemini API...")
print(f"API Key: {api_key[:20]}...")

try:
    # Initialize client
    client = genai.Client(api_key=api_key)
    print("✓ Client initialized")
    
    # Try embedding with text-embedding-004
    print("\nTrying text-embedding-004...")
    result = client.models.embed_content(
        model="text-embedding-004",
        contents=["Hello world"]
    )
    print(f"✓ Success! Got {len(result.embeddings)} embedding(s)")
    print(f"  Embedding dimension: {len(result.embeddings[0].values)}")
    
except Exception as e:
    print(f"✗ Failed with text-embedding-004: {e}")
    
    # Try with models/text-embedding-004
    try:
        print("\nTrying models/text-embedding-004...")
        result = client.models.embed_content(
            model="models/text-embedding-004",
            contents=["Hello world"]
        )
        print(f"✓ Success! Got {len(result.embeddings)} embedding(s)")
        print(f"  Embedding dimension: {len(result.embeddings[0].values)}")
    except Exception as e2:
        print(f"✗ Failed with models/text-embedding-004: {e2}")

print("\n" + "="*60)
print("Now testing text generation...")

try:
    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents="Say hello in 5 words"
    )
    print(f"✓ Text generation works!")
    print(f"  Response: {response.text}")
except Exception as e:
    print(f"✗ Text generation failed: {e}")
