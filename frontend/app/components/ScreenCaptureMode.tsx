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

const CHUNK_INTERVAL_MS = 10_000;
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

export default function ScreenCaptureMode({ onBack }: ScreenCaptureModeProps) {
  const [sessionId, setSessionId] = useState("");
  const [isCapturing, setIsCapturing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const displayStreamRef = useRef<MediaStream | null>(null);
  const chunkIndexRef = useRef(0);

  const isSupported =
    typeof window !== "undefined" &&
    !!navigator.mediaDevices?.getDisplayMedia &&
    typeof MediaRecorder !== "undefined";

  const handleStopCapture = () => {
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current = null;
    displayStreamRef.current?.getTracks().forEach((t) => t.stop());
    displayStreamRef.current = null;
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

    const newSessionId = `screenshare_${Date.now()}`;
    setSessionId(newSessionId);
    chunkIndexRef.current = 0;

    const recorder = new MediaRecorder(audioOnlyStream, { mimeType });

    recorder.ondataavailable = async (event: BlobEvent) => {
      if (event.data.size === 0) return;
      const offsetSeconds = chunkIndexRef.current * (CHUNK_INTERVAL_MS / 1000);
      chunkIndexRef.current += 1;
      try {
        await api.uploadAudioChunk(newSessionId, event.data, offsetSeconds, mimeType);
      } catch (err) {
        console.error("Error uploading audio chunk:", err);
      }
    };

    // If the user stops sharing via the browser's native "Stop sharing" bar.
    audioTracks[0].addEventListener("ended", handleStopCapture);

    recorder.start(CHUNK_INTERVAL_MS);
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
        ) : !isCapturing ? (
          <div className="bg-white rounded-xl shadow-lg p-8 max-w-2xl mx-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Share Your Screen</h2>
            <p className="text-gray-600 mb-6">
              Share a Zoom call, webinar, or video and get live transcription and evidence-based
              Q&amp;A - no setup needed, just click and share.
            </p>
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
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-3 animate-pulse" />
                <span className="text-green-800 font-medium">Capturing screen audio...</span>
              </div>
              <button
                onClick={handleStopCapture}
                className="bg-red-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-700"
              >
                Stop Sharing
              </button>
            </div>

            {/* Main Content */}
            <div className="space-y-6">
              <TranscriptViewer sessionId={sessionId} autoRefreshMs={8000} />

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
