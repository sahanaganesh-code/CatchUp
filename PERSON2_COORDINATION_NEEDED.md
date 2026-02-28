# Coordination Needed with Person 2 (Data Engineer)

## ⚠️ Important: Zoom → Google Meet Migration

Person 1 (AI Expert) has completed the migration from Zoom to Google Meet in all AI files.

### Changes Made by Person 1:
- ✅ `models.py`: Renamed `ZoomWebhookPayload` → `GoogleMeetWebhookPayload`
- ✅ `models.py`: Changed `mode: "zoom"` → `mode: "google-meet"`
- ✅ All AI files updated with Google Meet context

### Action Required by Person 2:

#### 1. Update `zoom.py` (Your File)
**File:** `backend/app/zoom.py`

**Required Changes:**
```python
# Line 6: Change this import
from app.models import TranscriptChunk, ZoomWebhookPayload
# TO:
from app.models import TranscriptChunk, GoogleMeetWebhookPayload
```

**Recommended:** Rename the entire file from `zoom.py` to `google_meet.py` and update all functions:
- `process_zoom_webhook()` → `process_google_meet_webhook()`
- `simulate_zoom_transcript()` → `simulate_google_meet_transcript()`

#### 2. Update `main.py` Import (Coordinate with Person 3)
**File:** `backend/app/main.py` (Person 3's file)

**Line 27** currently has:
```python
from app.zoom import process_zoom_webhook, simulate_zoom_transcript
```

After you rename `zoom.py` to `google_meet.py`, Person 3 will need to update this to:
```python
from app.google_meet import process_google_meet_webhook, simulate_google_meet_transcript
```

### Current Server Status:
❌ **Server won't start** until `zoom.py` is updated because it's trying to import `ZoomWebhookPayload` which no longer exists.

### Quick Fix to Get Server Running:
If you want to test immediately, temporarily update line 6 in `zoom.py`:
```bash
cd /Users/sahanaganesh/catchup/backend/app
# Quick fix:
sed -i '' 's/ZoomWebhookPayload/GoogleMeetWebhookPayload/g' zoom.py
```

Then the server will start and you can test the Google Meet changes!

---

## Summary
- **Person 1** ✅ Done: All AI files migrated to Google Meet
- **Person 2** ⏳ TODO: Update `zoom.py` imports and rename to `google_meet.py`
- **Person 3** ⏳ TODO: Update `main.py` imports after Person 2 renames file

**Priority:** High - Server won't start until this is fixed!
