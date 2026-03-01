"use client";

import { useState, useEffect } from "react";
import { ArrowLeft, Video, Send, History } from "lucide-react";
import { api, TranscriptChunk } from "../lib/api";
import RecapPanel from "./RecapPanel";
import QAPanel from "./QAPanel";
import ActionsPanel from "./ActionsPanel";
import TranscriptViewer from "./TranscriptViewer";
import TodoPanel from "./TodoPanel";
import CalendarPanel from "./CalendarPanel";
import NotesPanel from "./NotesPanel";

interface MeetModeProps {
  onBack: () => void;
  userName?: string | null;
}

const MEET_HISTORY_KEY = "catchup_meet_history";
const MAX_HISTORY = 50;

type MeetHistoryEntry = { meetingId: string; date: string };

function formatHistoryDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { dateStyle: "medium" });
}

export default function MeetMode({ onBack, userName }: MeetModeProps) {
  const [sessionId, setSessionId] = useState("");
  const [meetingId, setMeetingId] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [transcriptInput, setTranscriptInput] = useState("");
  const [activeTab, setActiveTab] = useState<"connect" | "history">("connect");
  const [meetHistory, setMeetHistory] = useState<MeetHistoryEntry[]>([]);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(MEET_HISTORY_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as MeetHistoryEntry[];
        setMeetHistory(Array.isArray(parsed) ? parsed : []);
      }
    } catch {
      setMeetHistory([]);
    }
  }, []);

  const saveToHistory = (entry: MeetHistoryEntry) => {
    setMeetHistory((prev) => {
      const next = [entry, ...prev.filter((e) => e.meetingId !== entry.meetingId || e.date !== entry.date)].slice(0, MAX_HISTORY);
      try {
        localStorage.setItem(MEET_HISTORY_KEY, JSON.stringify(next));
      } catch {}
      return next;
    });
  };

  const handleConnect = async () => {
    const trimmed = meetingId.trim();
    if (!trimmed) return;

    saveToHistory({ meetingId: trimmed, date: new Date().toISOString() });

    const newSessionId = `meet_${trimmed}`;
    setSessionId(newSessionId);
    setIsConnected(true);

    const mockChunks: TranscriptChunk[] = [
      {
        timestamp: "00:00:00",
        text: "Welcome everyone to today's product planning meeting.",
        speaker: "Alice",
      },
      {
        timestamp: "00:00:15",
        text: "Today we'll discuss the Q2 roadmap and prioritize features for the next release.",
        speaker: "Alice",
      },
      {
        timestamp: "00:00:35",
        text: "I think we should focus on the user authentication improvements first.",
        speaker: "Bob",
      },
      {
        timestamp: "00:01:00",
        text: "Good point. We've had several security audit recommendations that we need to address.",
        speaker: "Alice",
      },
      {
        timestamp: "00:01:20",
        text: "I can take ownership of the authentication work. I'll add it to Google Tasks and create a Calendar kickoff.",
        speaker: "Bob",
      },
    ];

    await api.ingestTranscript(newSessionId, "google_meet", mockChunks);
  };

  const handleAddTranscript = async () => {
    if (!transcriptInput.trim() || !sessionId) return;

    const timestamp = new Date().toISOString().substr(11, 8);
    const chunk: TranscriptChunk = {
      timestamp,
      text: transcriptInput,
      speaker: "User",
    };

    await api.ingestTranscript(sessionId, "google_meet", [chunk]);
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
        <div className="mb-6">
          <button
            onClick={onBack}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back
          </button>
          <div className="flex items-center">
            <div className="flex items-center justify-center w-12 h-12 bg-red-100 rounded-full mr-4">
              <Video className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Google Meet Mode
              </h1>
              <p className="text-gray-600">Live captions & transcript (meeting, Gemini)</p>
            </div>
          </div>
        </div>

        {!isConnected ? (
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
              Connect to Google Meet{userName ? `, ${userName}` : ""}
            </h2>
            {activeTab === "connect" ? (
              <>
            <p className="text-green-100 mb-6">
              Enter your meeting ID to start receiving
              real-time transcripts (live captions or recording).
            </p>
            <div className="space-y-4">
              <input
                type="text"
                value={meetingId}
                onChange={(e) => setMeetingId(e.target.value)}
                placeholder="Enter meeting ID"
                className="w-full px-4 py-3 border border-green-600 bg-white text-gray-900 placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-green-300 focus:border-transparent"
              />
              <button
                onClick={handleConnect}
                disabled={!meetingId.trim()}
                className="w-full bg-[#256055] text-white py-3 rounded-lg font-medium hover:bg-[#1e5249] disabled:bg-gray-500 disabled:cursor-not-allowed"
              >
                Connect to Meet
              </button>
            </div>
              </>
            ) : (
              <div className="space-y-3">
                <p className="text-green-100 mb-4">Past meetings and their dates.</p>
                {meetHistory.length === 0 ? (
                  <p className="text-green-200 text-sm">No meeting history yet. Connect to a meeting to see it here.</p>
                ) : (
                  <ul className="space-y-2 max-h-64 overflow-y-auto">
                    {meetHistory.map((entry, i) => (
                      <li key={`${entry.meetingId}-${entry.date}-${i}`} className="bg-white/10 rounded-lg px-4 py-3 flex justify-between items-center">
                        <span className="text-white font-medium">{entry.meetingId}</span>
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
            <div className="bg-[#2e6a4f] border border-[#256055] rounded-lg p-4">
              {userName && (
                <p className="text-green-100 text-sm mb-2">Connected as {userName}</p>
              )}
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-300 rounded-full mr-3 animate-pulse" />
                <span className="text-white font-medium">
                  Connected to meeting
                </span>
              </div>
            </div>

            {/* Meeting view + CatchUp side by side: meeting at top, tools below */}
            <div className="bg-[#2e6a4f] rounded-xl shadow-lg overflow-hidden">
              <h3 className="text-lg font-bold text-white p-4 pb-2">Google Meet</h3>
              <div className="relative bg-black rounded-b-xl" style={{ height: "min(50vh, 400px)" }}>
                <iframe
                  title="Google Meet"
                  src={`https://meet.google.com/${meetingId.trim()}`}
                  className="w-full h-full border-0"
                  allow="camera; microphone; fullscreen; display-capture"
                  referrerPolicy="no-referrer-when-downgrade"
                />
              </div>
              <div className="p-4 pt-2 flex items-center justify-between flex-wrap gap-2">
                <p className="text-green-100 text-sm">
                  If the meeting doesn&apos;t load above, open it in a new tab to join.
                </p>
                <button
                  type="button"
                  onClick={() => window.open(`https://meet.google.com/${meetingId.trim()}`, "_blank", "noopener,noreferrer")}
                  className="bg-white text-[#2e6a4f] px-4 py-2 rounded-lg font-medium hover:bg-gray-100"
                >
                  Open meeting in new tab
                </button>
              </div>
            </div>

            <div className="bg-[#2e6a4f] rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-bold text-white mb-4">
                Add transcript chunk (stub)
              </h3>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={transcriptInput}
                  onChange={(e) => setTranscriptInput(e.target.value)}
                  placeholder="Type transcript text..."
                  className="flex-1 px-4 py-2 border border-green-600 bg-white text-gray-900 placeholder-gray-400 rounded-lg focus:ring-2 focus:ring-green-300 focus:border-transparent"
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

            <div className="space-y-6">
              <TranscriptViewer sessionId={sessionId} />
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
