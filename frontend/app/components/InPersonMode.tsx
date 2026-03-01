"use client";

import { useState, useRef, useEffect } from "react";
import { ArrowLeft, Mic, Upload, Send, History } from "lucide-react";
import { api, TranscriptChunk } from "../lib/api";
import RecapPanel from "./RecapPanel";
import QAPanel from "./QAPanel";
import ActionsPanel from "./ActionsPanel";
import TranscriptViewer from "./TranscriptViewer";
import TodoPanel from "./TodoPanel";
import CalendarPanel from "./CalendarPanel";
import NotesPanel from "./NotesPanel";

const INPERSON_HISTORY_KEY = "catchup_inperson_history";
const MAX_HISTORY = 50;

type InPersonHistoryEntry = { title: string; date: string };

function formatHistoryDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { dateStyle: "medium" });
}

interface InPersonModeProps {
  onBack: () => void;
  userName?: string | null;
}

export default function InPersonMode({ onBack, userName }: InPersonModeProps) {
  const [sessionId, setSessionId] = useState("");
  const [lectureId, setLectureId] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [transcriptInput, setTranscriptInput] = useState("");
  const [activeTab, setActiveTab] = useState<"connect" | "history">("connect");
  const [lectureHistory, setLectureHistory] = useState<InPersonHistoryEntry[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(INPERSON_HISTORY_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as InPersonHistoryEntry[];
        setLectureHistory(Array.isArray(parsed) ? parsed : []);
      }
    } catch {
      setLectureHistory([]);
    }
  }, []);

  const saveToHistory = (entry: InPersonHistoryEntry) => {
    setLectureHistory((prev) => {
      const next = [entry, ...prev.filter((e) => e.title !== entry.title || e.date !== entry.date)].slice(0, MAX_HISTORY);
      try {
        localStorage.setItem(INPERSON_HISTORY_KEY, JSON.stringify(next));
      } catch {}
      return next;
    });
  };

  const handleStartSession = () => {
    if (!lectureId.trim()) return;

    saveToHistory({ title: lectureId.trim(), date: new Date().toISOString() });

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
    <div className="min-h-screen p-6 bg-[#f0e6d3] relative">
      <div
        role="img"
        aria-label="CatchUp logo"
        className="absolute top-6 right-6 w-20 h-20 bg-[#2e6a4f] shrink-0"
        style={{
          maskImage: "url(/logo.png)",
          maskSize: "contain",
          maskRepeat: "no-repeat",
          maskPosition: "center",
          WebkitMaskImage: "url(/logo.png)",
          WebkitMaskSize: "contain",
          WebkitMaskRepeat: "no-repeat",
          WebkitMaskPosition: "center",
        }}
      />
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
            <div className="flex items-center justify-center w-12 h-12 bg-[#2e6a4f] rounded-full mr-4">
              <Mic className="w-6 h-6 text-white" />
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
          <div className="bg-[#2e6a4f] rounded-xl shadow-lg p-8 max-w-2xl mx-auto">
            <div className="flex gap-2 mb-4">
              <button
                type="button"
                onClick={() => setActiveTab("connect")}
                className={`px-4 py-2 rounded-lg font-medium ${activeTab === "connect" ? "bg-[#256055] text-white" : "bg-white/20 text-green-100 hover:bg-white/30"}`}
              >
                Connect
              </button>
              <button
                type="button"
                onClick={() => setActiveTab("history")}
                className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 ${activeTab === "history" ? "bg-[#256055] text-white" : "bg-white/20 text-green-100 hover:bg-white/30"}`}
              >
                <History className="w-4 h-4" />
                History
              </button>
            </div>
            <h2 className="text-xl font-bold text-white mb-4">
              Connect to In-Person Lecture{userName ? `, ${userName}` : ""}
            </h2>
            {activeTab === "connect" ? (
              <>
            <p className="text-green-100 mb-6">
              Enter a lecture ID to start your recording session.
            </p>
            <div className="space-y-4">
              <input
                type="text"
                value={lectureId}
                onChange={(e) => setLectureId(e.target.value)}
                placeholder="Enter Lecture ID (e.g., CS101-Lecture5)"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
              <button
                onClick={handleStartSession}
                disabled={!lectureId.trim()}
                className="w-full bg-[#256055] text-white py-3 rounded-lg font-medium hover:bg-[#1e5249] disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                Start Session
              </button>
            </div>
              </>
            ) : (
              <div className="space-y-3">
                <p className="text-green-100 mb-4">Past lectures: title and date.</p>
                {lectureHistory.length === 0 ? (
                  <p className="text-green-200 text-sm">No lecture history yet. Start a session to see it here.</p>
                ) : (
                  <ul className="space-y-2 max-h-64 overflow-y-auto">
                    {lectureHistory.map((entry, i) => (
                      <li key={`${entry.title}-${entry.date}-${i}`} className="bg-white/10 rounded-lg px-4 py-3 flex justify-between items-center">
                        <span className="text-white font-medium">{entry.title}</span>
                        <span className="text-green-200 text-sm">{formatHistoryDate(entry.date)}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {/* Status */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              {userName && (
                <p className="text-green-800 text-sm mb-2">Connected as {userName}</p>
              )}
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
            <div className="bg-[#2e6a4f] rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-bold text-white mb-4">
                Recording Controls (Stub)
              </h3>
              <div className="flex items-center gap-4 mb-4">
                <button
                  onClick={() => setIsRecording(!isRecording)}
                  className={`flex items-center px-6 py-3 rounded-lg font-medium ${
                    isRecording
                      ? "bg-red-600 hover:bg-red-700 text-white"
                      : "bg-white text-[#2e6a4f] hover:bg-gray-100"
                  }`}
                >
                  <Mic className="w-5 h-5 mr-2" />
                  {isRecording ? "Stop Recording" : "Start Recording"}
                </button>
                {isRecording && (
                  <div className="flex items-center text-red-300">
                    <div className="w-3 h-3 bg-red-500 rounded-full mr-2 animate-pulse" />
                    Recording...
                  </div>
                )}
              </div>

              {/* Manual Transcript Input */}
              <div className="border-t border-green-600 pt-4">
                <h4 className="text-sm font-medium text-green-100 mb-2">
                  Add Transcript Manually (for testing)
                </h4>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={transcriptInput}
                    onChange={(e) => setTranscriptInput(e.target.value)}
                    placeholder="Type transcript text..."
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    onKeyPress={(e) => {
                      if (e.key === "Enter") handleAddTranscript();
                    }}
                  />
                  <button
                    onClick={handleAddTranscript}
                    className="bg-[#256055] text-white px-6 py-2 rounded-lg font-medium hover:bg-[#1e5249] flex items-center"
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
