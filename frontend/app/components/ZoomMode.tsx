"use client";

import { useState, useEffect } from "react";
import { ArrowLeft, Video, Send, FolderOpen, PlusCircle } from "lucide-react";
import { api, TranscriptChunk } from "../lib/api";
import RecapPanel from "./RecapPanel";
import QAPanel from "./QAPanel";
import TranscriptViewer from "./TranscriptViewer";
import TodoPanel from "./TodoPanel";
import CalendarPanel from "./CalendarPanel";

interface ZoomModeProps {
  onBack: () => void;
  initialSessionId?: string;
  sessions?: string[];
  onOpenSession?: (sessionId: string) => void;
}

function sessionDisplayName(sid: string): string {
  return sid.replace(/^inperson_/, "").replace(/^zoom_/, "") || sid;
}

export default function ZoomMode({ onBack, initialSessionId, sessions = [], onOpenSession }: ZoomModeProps) {
  const [sessionId, setSessionId] = useState("");
  const [meetingId, setMeetingId] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [transcriptInput, setTranscriptInput] = useState("");
  const [transcriptRefreshTrigger, setTranscriptRefreshTrigger] = useState(0);

  useEffect(() => {
    if (initialSessionId && initialSessionId.startsWith("zoom_")) {
      setSessionId(initialSessionId);
      setMeetingId(sessionDisplayName(initialSessionId));
      setIsConnected(true);
    }
  }, [initialSessionId]);

  const startNewSession = () => {
    setSessionId("");
    setMeetingId("");
    setIsConnected(false);
    setTranscriptRefreshTrigger((t) => t + 1);
  };

  const handleConnect = async () => {
    if (!meetingId.trim()) return;

    const newSessionId = `zoom_${meetingId}`;
    setSessionId(newSessionId);
    setIsConnected(true);
    // No sample transcript: only real Zoom/Meet transcript will be ingested.
  };

  const handleAddTranscript = async () => {
    if (!transcriptInput.trim() || !sessionId) return;

    const timestamp = new Date().toISOString().substr(11, 8);
    const chunk: TranscriptChunk = {
      timestamp,
      text: transcriptInput,
      speaker: "User",
    };

    await api.ingestTranscript(sessionId, "zoom", [chunk]);
    setTranscriptInput("");
    setTranscriptRefreshTrigger((t) => t + 1);
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
            <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mr-4">
              <Video className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Zoom Meeting Mode
              </h1>
              <p className="text-gray-600">RTMS transcript ingestion</p>
            </div>
          </div>
        </div>

        {/* Connection Panel */}
        {!isConnected ? (
          <div className="space-y-6 max-w-2xl mx-auto">
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Connect to a meeting
              </h2>
              <p className="text-gray-600 mb-6">
                Enter your Zoom meeting ID to start, or open a previous session below.
              </p>
              <div className="space-y-4">
                <input
                  type="text"
                  value={meetingId}
                  onChange={(e) => setMeetingId(e.target.value)}
                  placeholder="e.g. 123-456-7890"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  onClick={handleConnect}
                  disabled={!meetingId.trim()}
                  className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  Connect to Meeting
                </button>
              </div>
            </div>
            {sessions.filter((s) => s.startsWith("zoom_")).length > 0 && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
                  <FolderOpen className="w-5 h-5 text-blue-600" />
                  Open a previous session
                </h3>
                <ul className="space-y-2">
                  {sessions.filter((s) => s.startsWith("zoom_")).map((sid) => (
                    <li key={sid}>
                      <button
                        onClick={() => onOpenSession?.(sid)}
                        className="w-full text-left px-4 py-2 rounded-lg hover:bg-blue-50 font-medium text-gray-900"
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
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse" />
                  <span className="text-blue-800 font-medium">
                    Meeting: {meetingId || sessionDisplayName(sessionId)}
                  </span>
                  <button
                    onClick={startNewSession}
                    type="button"
                    className="flex items-center gap-1 text-sm text-blue-700 hover:text-blue-900 font-medium"
                  >
                    <PlusCircle className="w-4 h-4" />
                    New session
                  </button>
                </div>
                {sessions.filter((s) => s.startsWith("zoom_") && s !== sessionId).length > 0 && (
                  <div className="flex items-center gap-1 text-sm">
                    <FolderOpen className="w-4 h-4 text-blue-600" />
                    <select
                      className="bg-white border border-blue-300 rounded-lg px-2 py-1.5 text-blue-800 font-medium"
                      value=""
                      onChange={(e) => { const v = e.target.value; if (v) onOpenSession?.(v); e.target.value = ""; }}
                    >
                      <option value="">Switch session…</option>
                      {sessions.filter((s) => s.startsWith("zoom_") && s !== sessionId).map((sid) => (
                        <option key={sid} value={sid}>{sessionDisplayName(sid)}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            </div>

            {/* Add Transcript (Stub) */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                Add Transcript Chunk (Stub)
              </h3>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={transcriptInput}
                  onChange={(e) => setTranscriptInput(e.target.value)}
                  placeholder="Type transcript text..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  onKeyPress={(e) => {
                    if (e.key === "Enter") handleAddTranscript();
                  }}
                />
                <button
                  onClick={handleAddTranscript}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 flex items-center"
                >
                  <Send className="w-4 h-4 mr-2" />
                  Add
                </button>
              </div>
            </div>

            {/* Main Content */}
            <div className="space-y-6">
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
