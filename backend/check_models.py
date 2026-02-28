"""
Check available Gemini models using REST API
"""
import google.generativeai as genai
import os

# Use REST transport
os.environ['GOOGLE_API_USE_CLIENT_CERTIFICATE'] = 'false'
genai.configure(api_key="AIzaSyBWUL7NiLuySvvvO6vHmpOR9jnRhywrfgY", transport='rest')

print("Listing available models...\n")

try:
    models = genai.list_models()
    
    print("=" * 70)
    print("EMBEDDING MODELS:")
    print("=" * 70)
    for model in models:
        if 'embed' in model.name.lower():
            print(f"\n✓ {model.name}")
            print(f"  Display Name: {model.display_name}")
            print(f"  Supported Methods: {model.supported_generation_methods}")
    
    print("\n" + "=" * 70)
    print("TEXT GENERATION MODELS:")
    print("=" * 70)
    for model in models:
        if 'gemini' in model.name.lower() and 'embed' not in model.name.lower():
            print(f"\n✓ {model.name}")
            print(f"  Display Name: {model.display_name}")
            print(f"  Supported Methods: {model.supported_generation_methods}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
