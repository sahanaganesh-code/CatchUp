# Service account vs you – what to use and what to grant

## Short answer

- **Backend runs as the service account** (the one in `gcp-key.json`). It does not run as “you.”
- **You** use your own Google account only to sign in to Cloud Console and **grant roles to that service account** (and to enable APIs).

So: **service account** = identity the app uses. **You** = human who sets up the project and gives the service account permission.

---

## 1. What is the service account?

It’s the identity in `gcp-key.json`:

- **Email:** `catchup-speech@niyati-cheesehacks.iam.gserviceaccount.com`  
  (or whatever `client_email` is in your `gcp-key.json`)
- **Used for:** Cloud Speech-to-Text and (if you use long audio) writing to the GCS bucket.

The backend uses this key via `GOOGLE_APPLICATION_CREDENTIALS`. No “you” (user account) is used at runtime.

---

## 2. What “you” need (your Google account)

- You must be able to sign in to [Google Cloud Console](https://console.cloud.google.com) for the project (e.g. `niyati-cheesehacks`).
- You need permission to **enable APIs** and **grant IAM roles** (e.g. Owner or Editor, or custom roles that allow `iam.roles.update` and `resourcemanager.projects.get` / using the Console).

If you created the project, you already have this.

---

## 3. Permissions to set (for the service account)

### A. Cloud Speech-to-Text

- **Enable the API** (you do this in the project):  
  [Enable Speech-to-Text API](https://console.cloud.google.com/apis/library/speech.googleapis.com) → select your project → Enable.
- **Who needs permission:** The **service account** must be allowed to call Speech-to-Text.  
  Usually the project’s default Compute/App Engine service account or a custom one is given “Speech-to-Text User” (or the API is enabled and the project allows it).  
  If you created a **custom** service account (like `catchup-speech@...`), grant it a role that includes `speech.*` (e.g. **Speech-to-Text User** or **Editor** for the project).

**How to grant (high level):**

1. Go to [IAM & Admin → IAM](https://console.cloud.google.com/iam-admin/iam).
2. Find the principal `catchup-speech@niyati-cheesehacks.iam.gserviceaccount.com` (or add it with **Grant access**).
3. Add role: **Speech-to-Text User** (or **Cloud Speech-to-Text User**).
4. Save.

### B. GCS bucket (only for long audio / lecture uploads)

If you use a bucket (e.g. `GOOGLE_CLOUD_STT_BUCKET=catchup-stt`), the **service account** must be able to write objects to that bucket.

**Steps:**

1. Open [Cloud Console → Storage](https://console.cloud.google.com/storage/browser).
2. Open your bucket (e.g. `catchup-stt`) → **Permissions** tab.
3. **Grant access** (or **Add principal**).
4. **New principal:** paste the **service account email** from `gcp-key.json`:  
   `catchup-speech@niyati-cheesehacks.iam.gserviceaccount.com`
5. **Role:** **Storage Object Creator** (under Cloud Storage).
6. Save.

Details: see **GCS_BUCKET_FIX.md**.

---

## 4. Quick checklist

| Task | Who | Where | What |
|------|-----|--------|------|
| Enable Speech-to-Text API | You | APIs & Services → Library | Enable for project |
| Let app call Speech-to-Text | Service account | IAM → IAM | Role: **Speech-to-Text User** for `catchup-speech@...` |
| Let app write to bucket | Service account | Bucket → Permissions | **Storage Object Creator** for `catchup-speech@...` |

---

## 5. Summary

- **Use the service account** for the app; it’s already in `gcp-key.json`.
- **You** only sign in to Console and **grant** the service account:
  - **Speech-to-Text User** (project-level IAM), and  
  - **Storage Object Creator** on the GCS bucket (if you use long audio).
- No need to run the backend “as you”; it runs as the service account.
