"use client";

import { useState, useRef } from "react";
import { ArrowLeft, Mic, Upload, Send } from "lucide-react";
import { api, TranscriptChunk } from "../lib/api";
import RecapPanel from "./RecapPanel";
import QAPanel from "./QAPanel";
import ActionsPanel from "./ActionsPanel";
import TranscriptViewer from "./TranscriptViewer";
import TodoPanel from "./TodoPanel";
import CalendarPanel from "./CalendarPanel";
import NotesPanel from "./NotesPanel";

interface InPersonModeProps {
  onBack: () => void;
}

export default function InPersonMode({ onBack }: InPersonModeProps) {
  const [sessionId, setSessionId] = useState("");
  const [lectureId, setLectureId] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [transcriptInput, setTranscriptInput] = useState("");
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [uploadMessage, setUploadMessage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleStartSession = () => {
    if (!lectureId.trim()) return;

    const newSessionId = `inperson_${lectureId}`;
    setSessionId(newSessionId);
    setUploadStatus("idle");
    setUploadMessage("");
    // No sample transcript: only your uploaded audio will fill the transcript.
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
    setUploadMessage("Uploading and transcribing…");
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
      const msg = error && typeof error === "object" && "response" in error
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : null;
      setUploadStatus("error");
      setUploadMessage(msg || "Error uploading file. Is the backend running on http://localhost:8000?");
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
          <div className="bg-white rounded-xl shadow-lg p-8 max-w-2xl mx-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Start Recording Session
            </h2>
            <p className="text-gray-600 mb-6">
              Enter a lecture ID to start your recording session. After you start, you can upload an audio or video file to transcribe it with Google Cloud Speech-to-Text.
            </p>
            <div className="space-y-4">
              <input
                type="text"
                value={lectureId}
                onChange={(e) => setLectureId(e.target.value)}
                placeholder="Enter Lecture ID (e.g., CS101-Lecture5)"
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
        ) : (
          <div className="space-y-6">
            {/* Status */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-3 h-3 bg-green-500 rounded-full mr-3 animate-pulse" />
                  <span className="text-green-800 font-medium">
                    Session: {lectureId}
                  </span>
                </div>
                <button
                  onClick={() => { setUploadStatus("idle"); setUploadMessage(""); fileInputRef.current?.click(); }}
                  className="flex items-center text-green-700 hover:text-green-900 font-medium"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Audio or Video
                </button>
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

            {/* Recording Controls (Stub) */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                Recording Controls (Stub)
              </h3>
              <div className="flex items-center gap-4 mb-4">
                <button
                  onClick={() => setIsRecording(!isRecording)}
                  className={`flex items-center px-6 py-3 rounded-lg font-medium ${
                    isRecording
                      ? "bg-red-600 hover:bg-red-700 text-white"
                      : "bg-green-600 hover:bg-green-700 text-white"
                  }`}
                >
                  <Mic className="w-5 h-5 mr-2" />
                  {isRecording ? "Stop Recording" : "Start Recording"}
                </button>
                {isRecording && (
                  <div className="flex items-center text-red-600">
                    <div className="w-3 h-3 bg-red-600 rounded-full mr-2 animate-pulse" />
                    Recording...
                  </div>
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
              {/* Top Row: Transcript */}
              <TranscriptViewer sessionId={sessionId} />

              {/* Middle Row: Recap and Q&A */}
              <div className="grid lg:grid-cols-2 gap-6">
                <RecapPanel sessionId={sessionId} />
                <QAPanel sessionId={sessionId} />
              </div>

              {/* Bottom Row: Todos, Calendar, Notes, Actions */}
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
