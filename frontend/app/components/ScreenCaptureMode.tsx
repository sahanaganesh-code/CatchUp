"use client";

import { useRef, useState } from "react";
import { ArrowLeft, ScreenShare } from "lucide-react";
import { api } from "../lib/api";
import RecapPanel from "./RecapPanel";
import QAPanel from "./QAPanel";
import ActionsPanel from "./ActionsPanel";
import TranscriptViewer from "./TranscriptViewer";
import TodoPanel from "./TodoPanel";
import CalendarPanel from "./CalendarPanel";
import NotesPanel from "./NotesPanel";

interface ScreenCaptureModeProps {
  onBack: () => void;
}

// MediaRecorder's native timeslice firing happens in the browser's media
// pipeline, not the JS event loop - unlike setInterval/setTimeout, it keeps
// firing reliably even when the tab is backgrounded (which happens the
// moment the user switches to actually look at whatever they're sharing).
// So chunks are built from small native-timeslice fragments accumulated in
// the browser, not from manually-scheduled requestData() calls.
const NATIVE_FRAGMENT_MS = 250;
const FRAGMENTS_PER_CHUNK = 20; // 20 x 250ms fragments = one 5s uploaded chunk
const CHUNK_INTERVAL_MS = NATIVE_FRAGMENT_MS * FRAGMENTS_PER_CHUNK;
const MIME_CANDIDATES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/ogg;codecs=opus",
  "audio/ogg",
];

function pickSupportedMimeType(): string {
  if (typeof MediaRecorder === "undefined") return "";
  return MIME_CANDIDATES.find((t) => MediaRecorder.isTypeSupported(t)) ?? "";
}

function slugify(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export default function ScreenCaptureMode({ onBack }: ScreenCaptureModeProps) {
  const [sessionId, setSessionId] = useState("");
  const [sessionName, setSessionName] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [isCapturing, setIsCapturing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const displayStreamRef = useRef<MediaStream | null>(null);
  const chunkIndexRef = useRef(0);
  const headerBlobRef = useRef<Blob | null>(null);
  const pendingFragmentsRef = useRef<Blob[]>([]);

  const isSupported =
    typeof window !== "undefined" &&
    !!navigator.mediaDevices?.getDisplayMedia &&
    typeof MediaRecorder !== "undefined";

  const handleStopCapture = () => {
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current = null;
    displayStreamRef.current?.getTracks().forEach((t) => t.stop());
    displayStreamRef.current = null;
    headerBlobRef.current = null;
    pendingFragmentsRef.current = [];
    setIsCapturing(false);
  };

  const handleStartCapture = async () => {
    setError(null);

    let displayStream: MediaStream;
    try {
      displayStream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
        audio: true,
      });
    } catch {
      setError("Screen share was cancelled or denied.");
      return;
    }

    const audioTracks = displayStream.getAudioTracks();
    if (audioTracks.length === 0) {
      displayStream.getTracks().forEach((t) => t.stop());
      setError(
        'No audio was captured. When sharing, choose "Chrome Tab" (most reliable on Mac) ' +
          'or "Entire Screen", and make sure "Share audio" / "Share tab audio" is checked.'
      );
      return;
    }

    const mimeType = pickSupportedMimeType();
    if (!mimeType) {
      displayStream.getTracks().forEach((t) => t.stop());
      setError("This browser doesn't support recording audio. Try Chrome.");
      return;
    }

    // We only need the audio - stop the video track immediately.
    displayStream.getVideoTracks().forEach((t) => t.stop());
    const audioOnlyStream = new MediaStream(audioTracks);
    displayStreamRef.current = displayStream;

    const slug = slugify(sessionName);
    const newSessionId = slug ? `screenshare_${slug}_${Date.now()}` : `screenshare_${Date.now()}`;
    setSessionId(newSessionId);
    setDisplayName(sessionName.trim() || "Untitled session");
    chunkIndexRef.current = 0;
    headerBlobRef.current = null;
    pendingFragmentsRef.current = [];

    // A single continuous recorder for the whole session, using MediaRecorder's
    // own native timeslice firing (see the NATIVE_FRAGMENT_MS comment above)
    // rather than manually-scheduled requestData() calls, which stall for
    // long stretches whenever the tab is backgrounded.
    //
    // MediaRecorder only produces one complete, valid standalone audio file
    // in its FIRST fragment - every fragment after that is a raw continuation
    // with no header of its own, not independently decodable. So the first
    // 1s fragment is kept as a "header" and prepended to every later chunk's
    // upload (tried stripping it down to zero real audio via binary Cluster
    // slicing - that broke parsing entirely, a trailing fragment needs a
    // preceding Cluster to attach to - so a short real fragment it is).
    const recorder = new MediaRecorder(audioOnlyStream, { mimeType });

    recorder.ondataavailable = async (event: BlobEvent) => {
      if (event.data.size === 0) return;

      if (!headerBlobRef.current) {
        headerBlobRef.current = event.data;
        return;
      }

      pendingFragmentsRef.current.push(event.data);
      if (pendingFragmentsRef.current.length < FRAGMENTS_PER_CHUNK) return;

      const offsetSeconds = chunkIndexRef.current * (CHUNK_INTERVAL_MS / 1000);
      chunkIndexRef.current += 1;

      const fragments = pendingFragmentsRef.current;
      pendingFragmentsRef.current = [];

      const uploadBlob = new Blob([headerBlobRef.current, ...fragments], { type: mimeType });
      try {
        await api.uploadAudioChunk(newSessionId, uploadBlob, offsetSeconds, mimeType);
      } catch (err) {
        console.error("Error uploading audio chunk:", err);
      }
    };

    // If the user stops sharing via the browser's native "Stop sharing" bar.
    audioTracks[0].addEventListener("ended", handleStopCapture);

    recorder.start(NATIVE_FRAGMENT_MS);
    mediaRecorderRef.current = recorder;
    setIsCapturing(true);
  };

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={onBack}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back
          </button>
          <div className="flex items-center">
            <div className="flex items-center justify-center w-12 h-12 bg-amber-100 rounded-full mr-4">
              <ScreenShare className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Screen Share Mode</h1>
              <p className="text-gray-600">Live transcription of anything on your screen</p>
            </div>
          </div>
        </div>

        {!isSupported ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 max-w-2xl mx-auto text-center">
            <p className="text-yellow-800 font-medium">
              This browser doesn't support screen-audio capture. Please try Chrome or Edge on
              desktop.
            </p>
          </div>
        ) : !sessionId ? (
          <div className="bg-white rounded-xl shadow-lg p-8 max-w-2xl mx-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Share Your Screen</h2>
            <p className="text-gray-600 mb-6">
              Share a Zoom call, webinar, or video and get live transcription and evidence-based
              Q&amp;A - no setup needed, just click and share.
            </p>
            <input
              type="text"
              value={sessionName}
              onChange={(e) => setSessionName(e.target.value)}
              placeholder="Session name (optional, e.g. Wednesday Standup)"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg mb-4 focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            />
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}
            <button
              onClick={handleStartCapture}
              className="w-full bg-amber-600 text-white py-3 rounded-lg font-medium hover:bg-amber-700 flex items-center justify-center"
            >
              <ScreenShare className="w-5 h-5 mr-2" />
              Share Screen
            </button>
            <p className="text-xs text-gray-500 mt-3 text-center">
              Tip: On Mac, sharing a "Chrome Tab" captures audio more reliably than "Entire
              Screen."
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Status */}
            {isCapturing ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-3 animate-pulse" />
                  <span className="text-green-800 font-medium">
                    Capturing: {displayName}
                  </span>
                </div>
                <button
                  onClick={handleStopCapture}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-700"
                >
                  Stop Sharing
                </button>
              </div>
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-gray-400 rounded-full mr-3" />
                  <span className="text-gray-700 font-medium">
                    Session ended: {displayName}
                  </span>
                </div>
                <button
                  onClick={() => {
                    setSessionId("");
                    setSessionName("");
                    setError(null);
                  }}
                  className="bg-amber-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-amber-700"
                >
                  Start New Session
                </button>
              </div>
            )}

            {/* Main Content - stays visible after stopping so the session isn't lost */}
            <div className="space-y-6">
              <TranscriptViewer sessionId={sessionId} autoRefreshMs={isCapturing ? 4000 : undefined} />

              <div className="grid lg:grid-cols-2 gap-6">
                <RecapPanel sessionId={sessionId} />
                <QAPanel sessionId={sessionId} />
              </div>

              <div className="grid lg:grid-cols-2 gap-6">
                <div className="space-y-6">
                  <TodoPanel sessionId={sessionId} />
                  <CalendarPanel sessionId={sessionId} />
                </div>
                <div className="space-y-6">
                  <NotesPanel sessionId={sessionId} />
                  <ActionsPanel sessionId={sessionId} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
