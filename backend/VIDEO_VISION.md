# Video visual content (slides / on-screen text)

When you upload a **video**, CatchUp uses both:

1. **Audio** → transcribed to text (Speech-to-Text).
2. **Visual** → frames are sampled from the video and **OCR** (Tesseract) is run to read text from slides and on-screen content.

Those visual chunks are stored in the same session with speaker `"Slide"` and text prefixed with `[On-screen]`. Recap and Q&A then use **transcript + visual text**, so key points and answers can include things that were only shown on screen (e.g. bullet points on a slide that were never said aloud).

## Requirements

- **ffmpeg** – for extracting audio and video frames (see main docs).
- **Tesseract OCR** – for reading text from frames.
  - **macOS:** `brew install tesseract` (after installing Homebrew).
  - **Ubuntu/Debian:** `sudo apt install tesseract-ocr`.
  - **Windows:** install from https://github.com/UB-Mannheim/tesseract/wiki.
- **Python:** `pip install Pillow pytesseract` (already in `requirements.txt`).

If Tesseract is not installed, video upload still works: you get transcription only, and no visual chunks are added (no error).

## Flow

1. User uploads a video.
2. Backend extracts audio → transcribes → adds transcript chunks.
3. Backend extracts one frame every 5 seconds (up to 120 frames) → runs OCR on each → dedupes → adds chunks with `[On-screen] ...` and speaker `Slide`.
4. Recap and Q&A use all chunks (spoken + slide), so the LLM can use both.
