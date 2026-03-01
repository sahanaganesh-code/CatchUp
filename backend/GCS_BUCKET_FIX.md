# Fix 403: Let your service account write to the bucket

Your error:

```text
catchup-speech@niyati-cheesehacks.iam.gserviceaccount.com does not have storage.objects.create access
```

So the service account in `gcp-key.json` must be allowed to **create objects** in your GCS bucket. Do this once.

---

## Steps (about 2 minutes)

### 1. Open your bucket

1. Go to: **https://console.cloud.google.com/storage/browser**
2. Select project **niyati-cheesehacks** (top bar).
3. Click the bucket name **catchup-stt** (the one in your `.env` as `GOOGLE_CLOUD_STT_BUCKET=catchup-stt`).

### 2. Open Permissions

1. In the bucket page, open the **Permissions** tab.
2. Click **Grant access** (or **Add principal**).

### 3. Add the service account

1. In **New principals**, paste exactly:
   ```text
   catchup-speech@niyati-cheesehacks.iam.gserviceaccount.com
   ```
2. In **Role**, choose **Storage Object Creator**  
   (or **Cloud Storage** → **Storage Object Creator**).
3. Click **Save**.

### 4. Retry the upload

Restart the backend (if you want), then upload your long audio again. The 403 should be gone and long files will be transcribed via Cloud Speech-to-Text (no Gemini needed for transcription).

---

## If you don’t see the bucket

- Create it: **Cloud Console** → **Storage** → **Create bucket** → name it `catchup-stt` (or another name).
- In `backend/.env` set:  
  `GOOGLE_CLOUD_STT_BUCKET=catchup-stt`  
  (or the name you chose).
- Then do steps 2–3 above on that bucket so `catchup-speech@niyati-cheesehacks.iam.gserviceaccount.com` has **Storage Object Creator**.

---

## Summary

| What | Value |
|------|--------|
| Service account (from gcp-key.json) | `catchup-speech@niyati-cheesehacks.iam.gserviceaccount.com` |
| Bucket name (in .env) | `catchup-stt` |
| Role to add | **Storage Object Creator** |

After this, long videos use **only** Google Cloud Speech-to-Text (upload → GCS → batch recognize). The Gemini 429 in your error is from the **fallback** when GCS failed; once GCS works, that fallback is not used for transcription.
