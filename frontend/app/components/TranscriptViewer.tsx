"use client";

import { useState, useEffect } from "react";
import { FileText, Download, Loader2 } from "lucide-react";
import { api, TranscriptChunk } from "../lib/api";

interface TranscriptViewerProps {
  sessionId: string;
}

export default function TranscriptViewer({ sessionId }: TranscriptViewerProps) {
  const [transcript, setTranscript] = useState<TranscriptChunk[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalDuration, setTotalDuration] = useState("00:00:00");

  const loadTranscript = async () => {
    setLoading(true);
    try {
      const response = await api.getTranscript(sessionId);
      setTranscript(response.chunks);
      setTotalDuration(response.total_duration);
    } catch (error) {
      console.error("Error loading transcript:", error);
      alert("Error loading transcript");
    } finally {
      setLoading(false);
    }
  };

  const exportTranscript = () => {
    const text = transcript
      .map((chunk) => `[${chunk.timestamp}] ${chunk.speaker || "Speaker"}: ${chunk.text}`)
      .join("\n\n");

    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `transcript_${sessionId}_${new Date().toISOString().split("T")[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-[#2e6a4f] rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <FileText className="w-5 h-5 text-green-200 mr-2" />
          <h2 className="text-xl font-bold text-white">Full Transcript</h2>
        </div>
        <div className="flex gap-2">
          {transcript.length > 0 && (
            <button
              onClick={exportTranscript}
              className="flex items-center text-green-200 hover:text-white font-medium"
            >
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
          )}
          <button
            onClick={loadTranscript}
            disabled={loading}
            className="bg-[#256055] text-white px-4 py-2 rounded-lg font-medium hover:bg-[#1e5249] disabled:bg-gray-500 flex items-center"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Loading...
              </>
            ) : (
              "Load Transcript"
            )}
          </button>
        </div>
      </div>

      {transcript.length > 0 && (
        <div className="mb-3 text-sm text-green-100">
          Duration: {totalDuration} • {transcript.length} segments
        </div>
      )}

      <div className="max-h-96 overflow-y-auto space-y-3 bg-white rounded-lg p-4">
        {transcript.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            Click "Load Transcript" to view the full meeting transcript
          </p>
        ) : (
          transcript.map((chunk, index) => (
            <div key={index} className="border-l-4 border-[#2e6a4f] pl-4 py-2">
              <div className="flex items-start gap-3">
                <span className="font-mono text-xs text-[#2e6a4f] font-semibold whitespace-nowrap">
                  [{chunk.timestamp}]
                </span>
                <div className="flex-1">
                  {chunk.speaker && (
                    <span className="font-semibold text-gray-900">
                      {chunk.speaker}:{" "}
                    </span>
                  )}
                  <span className="text-gray-700">{chunk.text}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
