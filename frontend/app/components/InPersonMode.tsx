"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { ArrowLeft, Mic, Upload, Send, Square, FolderOpen, PlusCircle } from "lucide-react";
import { api, getApiErrorMessage, TranscriptChunk } from "../lib/api";
import { WavRecorder } from "../lib/wavRecorder";
import RecapPanel from "./RecapPanel";
import QAPanel from "./QAPanel";
import TranscriptViewer from "./TranscriptViewer";
import TodoPanel from "./TodoPanel";
import CalendarPanel from "./CalendarPanel";

interface InPersonModeProps {
  onBack: () => void;
  initialSessionId?: string;
  sessions?: string[];
  onOpenSession?: (sessionId: string) => void;
}

function sessionDisplayName(sid: string): string {
  return sid.replace(/^inperson_/, "").replace(/^zoom_/, "") || sid;
}

export default function InPersonMode({ onBack, initialSessionId, sessions = [], onOpenSession }: InPersonModeProps) {
  const [sessionId, setSessionId] = useState("");
  const [lectureId, setLectureId] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [transcriptInput, setTranscriptInput] = useState("");
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [uploadMessage, setUploadMessage] = useState("");
  const [transcriptRefreshTrigger, setTranscriptRefreshTrigger] = useState(0);
  const [liveTranscribing, setLiveTranscribing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const wavRecorderRef = useRef<WavRecorder | null>(null);
  const recordingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const liveUploadIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastSentChunkIndexRef = useRef(0);

  useEffect(() => {
    if (initialSessionId && initialSessionId.startsWith("inperson_")) {
      setSessionId(initialSessionId);
      setLectureId(sessionDisplayName(initialSessionId));
    }
  }, [initialSessionId]);

  const handleStartSession = () => {
    if (!lectureId.trim()) return;

    const newSessionId = `inperson_${lectureId}`;
    setSessionId(newSessionId);
    setUploadStatus("idle");
    setUploadMessage("");
  };

  const startNewSession = () => {
    setSessionId("");
    setLectureId("");
    setUploadStatus("idle");
    setUploadMessage("");
    setTranscriptRefreshTrigger((t) => t + 1);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!sessionId) {
      setUploadStatus("error");
      setUploadMessage("Please start a session first: enter a Lecture ID and click Start Session.");
      return;
    }

    setUploadStatus("uploading");
    const isLongFile = file.size > 50 * 1024 * 1024 || file.name.match(/\.(mp4|mov|webm|mkv)$/i);
    setUploadMessage(isLongFile ? "Uploading and transcribing… Long videos can take 10–30 min, please wait." : "Uploading and transcribing…");
    try {
      const result = await api.uploadAudio(sessionId, file);
      if (result?.status === "error") {
        setUploadStatus("error");
        setUploadMessage(result?.detail || "Upload failed.");
        e.target.value = "";
        return;
      }
      setUploadStatus("success");
      setUploadMessage("File uploaded and transcribed successfully! Check the transcript below.");
      e.target.value = "";
    } catch (error: unknown) {
      console.error("Error uploading audio:", error);
      setUploadStatus("error");
      setUploadMessage(getApiErrorMessage(error, "Error uploading file."));
      e.target.value = "";
    }
  };

  const handleAddTranscript = async () => {
    if (!transcriptInput.trim() || !sessionId) return;

    const timestamp = new Date().toISOString().substr(11, 8);
    const chunk: TranscriptChunk = {
      timestamp,
      text: transcriptInput,
      speaker: "Speaker",
    };

    await api.ingestTranscript(sessionId, "in-person", [chunk]);
    setTranscriptInput("");
    setTranscriptRefreshTrigger((t) => t + 1);
  };

  const stopRecordingTimer = useCallback(() => {
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    setRecordingSeconds(0);
  }, []);

  const handleStartRecording = useCallback(async () => {
    if (!sessionId) {
      setUploadStatus("error");
      setUploadMessage("Start a session first (enter Lecture ID and click Start Session).");
      return;
    }
    const recorder = new WavRecorder();
    wavRecorderRef.current = recorder;
    try {
      await recorder.start({
        onError: (msg) => {
          setUploadStatus("error");
          setUploadMessage(msg || "Could not access microphone.");
        },
      });
      setIsRecording(true);
      setRecordingSeconds(0);
      setUploadStatus("idle");
      setUploadMessage("");
      lastSentChunkIndexRef.current = 0;
      recordingTimerRef.current = setInterval(() => {
        setRecordingSeconds((s) => s + 1);
      }, 1000);
      const LIVE_UPLOAD_INTERVAL_MS = 10_000;
      liveUploadIntervalRef.current = setInterval(async () => {
        const rec = wavRecorderRef.current;
        if (!rec) return;
        const count = rec.getChunkCount();
        const last = lastSentChunkIndexRef.current;
        if (count <= last) return;
        const blob = rec.buildWavFromChunkRange(last);
        if (!blob) return;
        setLiveTranscribing(true);
        try {
          const file = new File([blob], `live_${Date.now()}.wav`, { type: "audio/wav" });
          const result = await api.uploadAudio(sessionId, file);
          if (result?.status !== "error") {
            lastSentChunkIndexRef.current = count;
            setTranscriptRefreshTrigger((t) => t + 1);
          }
        } catch (e) {
          console.error("Live segment upload failed:", e);
        } finally {
          setLiveTranscribing(false);
        }
      }, LIVE_UPLOAD_INTERVAL_MS);
    } catch (err) {
      console.error("Failed to start recording:", err);
      setUploadStatus("error");
      setUploadMessage(
        "Could not access microphone. Allow microphone access and try again."
      );
      wavRecorderRef.current = null;
    }
  }, [sessionId]);

  const handleStopRecording = useCallback(async () => {
    if (liveUploadIntervalRef.current) {
      clearInterval(liveUploadIntervalRef.current);
      liveUploadIntervalRef.current = null;
    }
    setIsRecording(false);
    stopRecordingTimer();
    const recorder = wavRecorderRef.current;
    if (!recorder) {
      wavRecorderRef.current = null;
      return;
    }
    const count = recorder.getChunkCount();
    const last = lastSentChunkIndexRef.current;

    if (count > last) {
      const blob = recorder.buildWavFromChunkRange(last);
      recorder.stop();
      wavRecorderRef.current = null;
      if (blob && blob.size >= 44) {
        setUploadStatus("uploading");
        setUploadMessage("Transcribing final segment…");
        setLiveTranscribing(true);
        try {
          const file = new File([blob], `lecture_final_${Date.now()}.wav`, { type: "audio/wav" });
          const result = await api.uploadAudio(sessionId, file);
          if (result?.status === "error") {
            setUploadStatus("error");
            setUploadMessage(result?.detail || "Transcription failed.");
          } else {
            setUploadStatus("success");
            setUploadMessage("Recording transcribed. Check the transcript below.");
            setTranscriptRefreshTrigger((t) => t + 1);
          }
        } catch (error: unknown) {
          console.error("Error uploading final segment:", error);
          setUploadStatus("error");
          setUploadMessage(getApiErrorMessage(error, "Error transcribing recording."));
        } finally {
          setLiveTranscribing(false);
        }
      }
      return;
    }

    const blob = recorder.stop();
    wavRecorderRef.current = null;
    if (!blob || blob.size < 44) {
      setUploadStatus("error");
      setUploadMessage("No audio captured. Check that your microphone is working and allowed for this site, then try again.");
      return;
    }
    const file = new File([blob], `lecture_recording_${Date.now()}.wav`, { type: "audio/wav" });
    setUploadStatus("uploading");
    setUploadMessage("Transcribing your recording…");
    setLiveTranscribing(true);
    try {
      const result = await api.uploadAudio(sessionId, file);
      if (result?.status === "error") {
        setUploadStatus("error");
        setUploadMessage(result?.detail || "Transcription failed.");
      } else {
        setUploadStatus("success");
        setUploadMessage("Recording transcribed. Check the transcript below.");
        setTranscriptRefreshTrigger((t) => t + 1);
      }
    } catch (error: unknown) {
      console.error("Error uploading recording:", error);
      setUploadStatus("error");
      setUploadMessage(getApiErrorMessage(error, "Error transcribing recording."));
    } finally {
      setLiveTranscribing(false);
    }
  }, [sessionId, stopRecordingTimer]);

  const formatTime = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
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
            <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mr-4">
              <Mic className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                In-Person Lecture Mode
              </h1>
              <p className="text-gray-600">
                Record and transcribe live lectures
              </p>
            </div>
          </div>
        </div>

        {/* Setup Panel */}
        {!sessionId ? (
          <div className="space-y-6 max-w-2xl mx-auto">
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Start a new session
              </h2>
              <p className="text-gray-600 mb-6">
                Enter a lecture ID, then record or upload audio. You can reopen any session below later.
              </p>
              <div className="space-y-4">
                <input
                  type="text"
                  value={lectureId}
                  onChange={(e) => setLectureId(e.target.value)}
                  placeholder="e.g. CS101-Lecture5"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <button
                  onClick={handleStartSession}
                  disabled={!lectureId.trim()}
                  className="w-full bg-green-600 text-white py-3 rounded-lg font-medium hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  Start Session
                </button>
              </div>
            </div>
            {sessions.filter((s) => s.startsWith("inperson_")).length > 0 && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
                  <FolderOpen className="w-5 h-5 text-green-600" />
                  Open a previous session
                </h3>
                <ul className="space-y-2">
                  {sessions.filter((s) => s.startsWith("inperson_")).map((sid) => (
                    <li key={sid}>
                      <button
                        onClick={() => onOpenSession?.(sid)}
                        className="w-full text-left px-4 py-2 rounded-lg hover:bg-green-50 font-medium text-gray-900"
                      >
                        {sessionDisplayName(sid)}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {/* Status + session switcher */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3 flex-wrap">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                  <span className="text-green-800 font-medium">
                    Session: {lectureId || sessionDisplayName(sessionId)}
                  </span>
                  <button
                    onClick={startNewSession}
                    type="button"
                    className="flex items-center gap-1 text-sm text-green-700 hover:text-green-900 font-medium"
                  >
                    <PlusCircle className="w-4 h-4" />
                    New session
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  {sessions.filter((s) => s.startsWith("inperson_") && s !== sessionId).length > 0 && (
                    <div className="flex items-center gap-1 text-sm">
                      <FolderOpen className="w-4 h-4 text-green-600" />
                      <select
                        className="bg-white border border-green-300 rounded-lg px-2 py-1.5 text-green-800 font-medium"
                        value=""
                        onChange={(e) => { const v = e.target.value; if (v) onOpenSession?.(v); e.target.value = ""; }}
                      >
                        <option value="">Switch session…</option>
                        {sessions.filter((s) => s.startsWith("inperson_") && s !== sessionId).map((sid) => (
                          <option key={sid} value={sid}>{sessionDisplayName(sid)}</option>
                        ))}
                      </select>
                    </div>
                  )}
                  <button
                    onClick={() => { setUploadStatus("idle"); setUploadMessage(""); fileInputRef.current?.click(); }}
                    className="flex items-center text-green-700 hover:text-green-900 font-medium"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Upload
                  </button>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*,video/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </div>
            </div>

            {/* Upload status message - always visible when not idle */}
            {uploadStatus !== "idle" && (
              <div
                className={`rounded-lg p-4 ${
                  uploadStatus === "uploading"
                    ? "bg-blue-50 border border-blue-200 text-blue-800"
                    : uploadStatus === "success"
                    ? "bg-green-50 border border-green-200 text-green-800"
                    : "bg-red-50 border border-red-200 text-red-800"
                }`}
              >
                {uploadStatus === "uploading" && (
                  <span className="flex items-center">
                    <span className="inline-block w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-2" />
                    {uploadMessage}
                  </span>
                )}
                {(uploadStatus === "success" || uploadStatus === "error") && uploadMessage}
              </div>
            )}

            {/* Record lecturer */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-2">
                Record lecturer
              </h3>
              <p className="text-gray-600 text-sm mb-4">
                Use your device microphone to record the lecture. Speak for at least 2–3 seconds, then stop to transcribe.
              </p>
              <div className="flex items-center gap-4 flex-wrap">
                {!isRecording ? (
                  <button
                    onClick={handleStartRecording}
                    className="flex items-center px-6 py-3 rounded-lg font-medium bg-green-600 hover:bg-green-700 text-white"
                  >
                    <Mic className="w-5 h-5 mr-2" />
                    Start recording
                  </button>
                ) : (
                  <>
                    <button
                      onClick={handleStopRecording}
                      className="flex items-center px-6 py-3 rounded-lg font-medium bg-red-600 hover:bg-red-700 text-white"
                    >
                      <Square className="w-5 h-5 mr-2" />
                      Stop & transcribe
                    </button>
                    <div className="flex items-center gap-3 text-red-600 font-medium">
                      <span className="inline-block w-3 h-3 bg-red-600 rounded-full animate-pulse" />
                      Recording {formatTime(recordingSeconds)}
                      {liveTranscribing && (
                        <span className="text-sm text-blue-600 font-normal">Transcribing…</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 w-full mt-2">
                      Live: transcript updates every 10s. Generate recap or ask questions anytime to catch up.
                    </p>
                  </>
                )}
              </div>

              {/* Manual Transcript Input */}
              <div className="border-t pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Add Transcript Manually (for testing)
                </h4>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={transcriptInput}
                    onChange={(e) => setTranscriptInput(e.target.value)}
                    placeholder="Type transcript text..."
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    onKeyPress={(e) => {
                      if (e.key === "Enter") handleAddTranscript();
                    }}
                  />
                  <button
                    onClick={handleAddTranscript}
                    className="bg-green-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-green-700 flex items-center"
                  >
                    <Send className="w-4 h-4 mr-2" />
                    Add
                  </button>
                </div>
              </div>
            </div>

            {/* Main Content */}
            <div className="space-y-6">
              {isRecording && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-2 text-blue-800 text-sm">
                  Live — Transcript updates every ~10s while recording. Use &quot;Generate Recap&quot; or Q&A anytime to catch up.
                </div>
              )}
              {/* Top Row: Transcript */}
              <TranscriptViewer sessionId={sessionId} refreshTrigger={transcriptRefreshTrigger} />

              {/* Middle Row: Recap and Q&A */}
              <div className="grid lg:grid-cols-2 gap-6">
                <RecapPanel sessionId={sessionId} />
                <QAPanel sessionId={sessionId} />
              </div>

              {/* Bottom Row: Todos, Calendar */}
              <div className="grid lg:grid-cols-2 gap-6">
                <TodoPanel sessionId={sessionId} />
                <CalendarPanel sessionId={sessionId} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
