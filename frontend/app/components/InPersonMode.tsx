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
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleStartSession = () => {
    if (!lectureId.trim()) return;

    const newSessionId = `inperson_${lectureId}`;
    setSessionId(newSessionId);

    // Simulate initial transcript
    const mockChunks: TranscriptChunk[] = [
      {
        timestamp: "00:00:00",
        text: "Good morning class. Today we'll be covering advanced algorithms and data structures.",
        speaker: "Professor",
      },
      {
        timestamp: "00:00:20",
        text: "Let's start with binary search trees and their time complexity analysis.",
        speaker: "Professor",
      },
      {
        timestamp: "00:00:45",
        text: "Remember that balanced trees like AVL and Red-Black trees maintain O(log n) operations.",
        speaker: "Professor",
      },
      {
        timestamp: "00:01:10",
        text: "For your homework, I want you to implement a self-balancing tree and submit it by next week.",
        speaker: "Professor",
      },
    ];

    api.ingestTranscript(newSessionId, "in-person", mockChunks);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !sessionId) return;

    try {
      await api.uploadAudio(sessionId, file);
      alert("Audio uploaded successfully! (Stub - would transcribe in production)");
    } catch (error) {
      console.error("Error uploading audio:", error);
      alert("Error uploading audio");
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
              Enter a lecture ID to start your recording session.
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
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center text-green-700 hover:text-green-900 font-medium"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Audio
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="audio/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </div>
            </div>

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
