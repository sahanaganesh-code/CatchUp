"""
List available Gemini models
"""
from google import genai

api_key = "AIzaSyBWUL7NiLuySvvvO6vHmpOR9jnRhywrfgY"
client = genai.Client(api_key=api_key)

print("Listing all available models...\n")

try:
    models = client.models.list()
    
    print("EMBEDDING MODELS:")
    print("-" * 60)
    for model in models:
        if 'embed' in model.name.lower():
            print(f"  {model.name}")
            if hasattr(model, 'supported_generation_methods'):
                print(f"    Methods: {model.supported_generation_methods}")
    
    print("\nGENERATION MODELS:")
    print("-" * 60)
    for model in models:
        if 'gemini' in model.name.lower() and 'embed' not in model.name.lower():
            print(f"  {model.name}")
            if hasattr(model, 'supported_generation_methods'):
                print(f"    Methods: {model.supported_generation_methods}")
    
except Exception as e:
    print(f"Error listing models: {e}")
