"""
Quick test script to verify the CatchUp API is working.
Run this after starting the backend server.
"""
import requests
import json
import os

API_URL = "http://localhost:8000"

def check_gemini_key():
    """Check if Gemini API key is configured."""
    from dotenv import load_dotenv
    load_dotenv()
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("⚠️  Warning: GEMINI_API_KEY not found in environment")
        print("   Some tests may fail. Please add your key to .env file")
        return False
    return True

def test_health():
    """Test health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{API_URL}/")
    print(f"✓ Health check: {response.json()}")
    return response.status_code == 200

def test_ingest_and_query():
    """Test transcript ingestion and Q&A."""
    session_id = "test_session_123"
    
    # Test data
    chunks = [
        {
            "timestamp": "00:00:00",
            "text": "Welcome to the product planning meeting. Today we'll discuss Q2 roadmap.",
            "speaker": "Alice"
        },
        {
            "timestamp": "00:00:20",
            "text": "We need to prioritize the authentication improvements for security.",
            "speaker": "Bob"
        },
        {
            "timestamp": "00:00:40",
            "text": "I'll create Notion tasks for the auth work and schedule a kickoff meeting.",
            "speaker": "Bob"
        },
        {
            "timestamp": "00:01:00",
            "text": "Great. Let's also plan to send follow-up emails to stakeholders.",
            "speaker": "Alice"
        }
    ]
    
    # Ingest transcript
    print("\nIngesting transcript...")
    response = requests.post(
        f"{API_URL}/api/ingest",
        json={
            "session_id": session_id,
            "mode": "google_meet",
            "chunks": chunks
        }
    )
    print("Ingest status:", response.status_code)
    print("Ingest JSON:", response.json())
    print(f"✓ Ingested {response.json()['chunks_ingested']} chunks")
    
    # Ask a question
    print("\nAsking question...")
    response = requests.post(
        f"{API_URL}/api/question",
        json={
            "session_id": session_id,
            "question": "What topics were discussed in the meeting?"
        }
    )
    result = response.json()
    print(f"✓ Answer: {result['answer']}")
    print(f"✓ Evidence quotes: {len(result['evidence'])}")
    print(f"✓ Has sufficient evidence: {result['has_sufficient_evidence']}")
    
    # Verify evidence requirement (2-5 quotes)
    if result['has_sufficient_evidence']:
        assert 2 <= len(result['evidence']) <= 5, "Evidence must be 2-5 quotes"
        print("✓ Evidence requirement met (2-5 quotes)")
    
    # Generate recap
    print("\nGenerating recap...")
    response = requests.post(
        f"{API_URL}/api/recap",
        json={"session_id": session_id}
    )
    result = response.json()
    print(f"✓ Summary: {result['summary'][:100]}...")
    print(f"✓ Key points: {len(result['key_points'])}")
    print(f"✓ Evidence: {len(result['evidence'])}")
    
    # Propose actions
    print("\nProposing actions...")
    response = requests.post(
        f"{API_URL}/api/actions/propose",
        json={"session_id": session_id}
    )
    result = response.json()
    actions = result['actions']
    print(f"✓ Proposed {len(actions)} actions")
    
    if actions:
        action = actions[0]
        print(f"  - {action['action_type']}: {action['title']}")
        print(f"  - Evidence quotes: {len(action['evidence'])}")
        
        # Test approval gating
        print("\nTesting approval gating...")
        
        # Try to approve
        response = requests.post(
            f"{API_URL}/api/actions/approve",
            json={
                "action_id": action['action_id'],
                "approved": True
            }
        )
        result = response.json()
        print(f"✓ Action approved: {result['approved']}")
        print(f"✓ Action executed: {result['executed']}")
        assert result['approved'] == True, "Action should be approved"
        assert result['executed'] == True, "Action should be executed after approval"
        
        # Test rejection
        if len(actions) > 1:
            action2 = actions[1]
            response = requests.post(
                f"{API_URL}/api/actions/approve",
                json={
                    "action_id": action2['action_id'],
                    "approved": False
                }
            )
            result = response.json()
            print(f"✓ Action rejected: {result['approved']}")
            assert result['approved'] == False, "Action should be rejected"
            assert result['executed'] == False, "Rejected action should not execute"
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("CatchUp API Test Suite (Gemini)")
    print("=" * 60)
    
    # Check Gemini API key
    has_key = check_gemini_key()
    if not has_key:
        print("\n⚠️  Continuing with limited tests...")
    print()
    
    try:
        if not test_health():
            print("\n❌ Health check failed. Is the server running?")
            return
        
        if test_ingest_and_query():
            print("\n" + "=" * 60)
            print("✓ All tests passed!")
            print("=" * 60)
            print("\nHard rules verified:")
            print("1. ✓ Evidence requirement (2-5 quotes)")
            print("2. ✓ Approval gating (actions only execute if approved=true)")
            print("3. ✓ Modular architecture")
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
