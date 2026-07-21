"use client";

import { useState, useEffect } from "react";
import { ArrowLeft, History, Mic, ScreenShare } from "lucide-react";
import { api, Session } from "../lib/api";
import RecapPanel from "./RecapPanel";
import QAPanel from "./QAPanel";
import ActionsPanel from "./ActionsPanel";
import TranscriptViewer from "./TranscriptViewer";
import TodoPanel from "./TodoPanel";
import CalendarPanel from "./CalendarPanel";
import NotesPanel from "./NotesPanel";

interface SessionHistoryProps {
  onBack: () => void;
}

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function SessionHistory({ onBack }: SessionHistoryProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  useEffect(() => {
    api
      .getSessions()
      .then(setSessions)
      .catch((error) => console.error("Error loading sessions:", error))
      .finally(() => setLoading(false));
  }, []);

  const selectedSession = sessions.find((s) => s.id === selectedSessionId);

  if (selectedSessionId && selectedSession) {
    return (
      <div className="min-h-screen p-6">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <button
              onClick={() => setSelectedSessionId(null)}
              className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to History
            </button>
            <div className="flex items-center">
              <div className="flex items-center justify-center w-12 h-12 bg-indigo-100 rounded-full mr-4">
                {selectedSession.mode === "screen-share" ? (
                  <ScreenShare className="w-6 h-6 text-indigo-600" />
                ) : (
                  <Mic className="w-6 h-6 text-indigo-600" />
                )}
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">{selectedSession.display_name}</h1>
                <p className="text-gray-600">{formatDate(selectedSession.created_at)}</p>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <TranscriptViewer sessionId={selectedSession.id} />

            <div className="grid lg:grid-cols-2 gap-6">
              <RecapPanel sessionId={selectedSession.id} />
              <QAPanel sessionId={selectedSession.id} />
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
              <div className="space-y-6">
                <TodoPanel sessionId={selectedSession.id} />
                <CalendarPanel sessionId={selectedSession.id} />
              </div>
              <div className="space-y-6">
                <NotesPanel sessionId={selectedSession.id} />
                <ActionsPanel sessionId={selectedSession.id} />
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <button
            onClick={onBack}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Back
          </button>
          <div className="flex items-center">
            <div className="flex items-center justify-center w-12 h-12 bg-indigo-100 rounded-full mr-4">
              <History className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Session History</h1>
              <p className="text-gray-600">Revisit any past session's transcript, recap, and Q&amp;A</p>
            </div>
          </div>
        </div>

        {loading ? (
          <p className="text-gray-500 text-center py-12">Loading sessions...</p>
        ) : sessions.length === 0 ? (
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <p className="text-gray-500">No sessions yet. Start one from the home page.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => setSelectedSessionId(session.id)}
                className="w-full bg-white rounded-xl shadow-lg p-5 hover:shadow-xl transition-shadow border-2 border-transparent hover:border-indigo-500 text-left flex items-center"
              >
                <div className="flex items-center justify-center w-10 h-10 bg-indigo-100 rounded-full mr-4 flex-shrink-0">
                  {session.mode === "screen-share" ? (
                    <ScreenShare className="w-5 h-5 text-indigo-600" />
                  ) : (
                    <Mic className="w-5 h-5 text-indigo-600" />
                  )}
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{session.display_name}</h3>
                  <p className="text-sm text-gray-500">
                    {session.mode === "screen-share" ? "Screen Share" : "In-Person"} &middot;{" "}
                    {formatDate(session.created_at)}
                  </p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
