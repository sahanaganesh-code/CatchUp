"use client";

import { useState } from "react";
import { ArrowLeft, Video, Send } from "lucide-react";
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
}

export default function MeetMode({ onBack }: MeetModeProps) {
  const [sessionId, setSessionId] = useState("");
  const [meetingId, setMeetingId] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [transcriptInput, setTranscriptInput] = useState("");

  const handleConnect = async () => {
    if (!meetingId.trim()) return;

    const newSessionId = `meet_${meetingId}`;
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
    <div className="min-h-screen p-6">
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
              <p className="text-gray-600">Live captions & transcript (Meet, Gemini)</p>
            </div>
          </div>
        </div>

        {!isConnected ? (
          <div className="bg-white rounded-xl shadow-lg p-8 max-w-2xl mx-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Connect to Google Meet
            </h2>
            <p className="text-gray-600 mb-6">
              Enter your Meet meeting code or link ID to start receiving
              real-time transcripts (live captions or recording).
            </p>
            <div className="space-y-4">
              <input
                type="text"
                value={meetingId}
                onChange={(e) => setMeetingId(e.target.value)}
                placeholder="Enter Meet code or meeting ID"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
              <button
                onClick={handleConnect}
                disabled={!meetingId.trim()}
                className="w-full bg-red-600 text-white py-3 rounded-lg font-medium hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                Connect to Meet
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="w-3 h-3 bg-green-500 rounded-full mr-3 animate-pulse" />
                <span className="text-green-800 font-medium">
                  Connected to Meet {meetingId}
                </span>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                Add transcript chunk (stub)
              </h3>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={transcriptInput}
                  onChange={(e) => setTranscriptInput(e.target.value)}
                  placeholder="Type transcript text..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  onKeyPress={(e) => {
                    if (e.key === "Enter") handleAddTranscript();
                  }}
                />
                <button
                  onClick={handleAddTranscript}
                  className="bg-red-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-red-700 flex items-center"
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
