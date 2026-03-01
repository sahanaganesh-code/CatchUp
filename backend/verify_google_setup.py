#!/usr/bin/env python3
"""
Quick check that Google setup is in place. Run from backend/: python3 verify_google_setup.py
"""
import os
import sys

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def check(name, ok, msg):
    status = "OK" if ok else "MISSING/FAIL"
    print(f"  [{status}] {name}: {msg}")
    return ok

def main():
    print("CatchUp – Google setup check\n")
    all_ok = True

    # 1. Env vars
    print("1. Environment variables")
    gemini = os.environ.get("GEMINI_API_KEY", "")
    all_ok &= check("GEMINI_API_KEY", bool(gemini.strip()), "set" if gemini else "not set")
    gcp = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    all_ok &= check("GOOGLE_CLOUD_PROJECT", bool(gcp.strip()), gcp or "not set (Cloud STT will use Gemini fallback)")
    creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if creds:
        # Resolve path: try as-is, then cwd-relative, then next to this script (backend/)
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        creds_paths = [creds, os.path.join(os.getcwd(), creds), os.path.join(backend_dir, creds.lstrip("./")) if not os.path.isabs(creds) else creds]
        creds_found = any(os.path.isfile(p) for p in creds_paths)
        all_ok &= check("GOOGLE_APPLICATION_CREDENTIALS", creds_found, creds if creds_found else f"file not found (tried {creds})")
    else:
        check("GOOGLE_APPLICATION_CREDENTIALS", False, "not set (use for Cloud STT)")

    # 2. Imports (app uses Google)
    print("\n2. App modules (Google integrations)")
    try:
        from app.zoom import process_zoom_webhook
        from app.meet import process_meet_webhook, get_meet_session_id
        from app.stt import transcribe_audio_bytes
        from app.store import vector_store
        check("app.zoom → app.meet", True, "webhook delegates to Google Meet")
        check("app.stt", True, "Cloud Speech-to-Text primary, Gemini fallback")
        check("app.store", True, "vector_store ready")
    except Exception as e:
        all_ok &= check("app imports", False, str(e))

    # 3. Optional: Cloud Speech client
    print("\n3. Google Cloud Speech-to-Text (optional)")
    if gcp.strip():
        # Resolve credentials path so it works when script is run from project root
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        creds_val = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
        if creds_val and not os.path.isabs(creds_val):
            for base in [os.getcwd(), backend_dir]:
                resolved = os.path.join(base, creds_val.lstrip("./"))
                if os.path.isfile(resolved):
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(resolved)
                    break
        try:
            from google.cloud.speech_v2 import SpeechClient
            client = SpeechClient()
            check("google.cloud.speech_v2", True, "SpeechClient OK")
        except Exception as e:
            all_ok &= check("google.cloud.speech_v2", False, str(e))
    else:
        print("  [skip] Set GOOGLE_CLOUD_PROJECT to use Cloud STT")

    print()
    if all_ok:
        print("All checks passed. Start server: python3 -m uvicorn app.main:app --reload --port 8000")
    else:
        print("Fix the items above, then run again. See backend/GOOGLE_VERIFY.md for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
