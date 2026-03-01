"use client";

import { useState } from "react";
import { FileText, Loader2 } from "lucide-react";
import { api, getApiErrorMessage, RecapResponse } from "../lib/api";
import EvidenceList from "./EvidenceList";

interface RecapPanelProps {
  sessionId: string;
}

export default function RecapPanel({ sessionId }: RecapPanelProps) {
  const [recap, setRecap] = useState<RecapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleGenerateRecap = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const response = await api.getRecap(sessionId);
      setRecap(response);
    } catch (error: unknown) {
      console.error("Error generating recap:", error);
      const msg = getApiErrorMessage(error, "Error generating recap.");
      setErrorMessage(msg);
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <FileText className="w-5 h-5 text-blue-600 mr-2" />
          <h2 className="text-xl font-bold text-gray-900">CatchUp Recap</h2>
        </div>
        <button
          onClick={handleGenerateRecap}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 flex items-center"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            "Generate Recap"
          )}
        </button>
      </div>

      {recap ? (
        <div className="space-y-4">
          {recap.summary && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">
                Summary
              </h3>
              <p className="text-gray-800 whitespace-pre-line">{recap.summary}</p>
            </div>
          )}

          {recap.key_points.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">
                Key Points
              </h3>
              <ul className="space-y-2">
                {recap.key_points.map((point, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-blue-600 mr-2">•</span>
                    <span className="text-gray-800">{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {recap.evidence && recap.evidence.length > 0 && (
            <EvidenceList evidence={recap.evidence} />
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {errorMessage && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-800 text-sm">
              {errorMessage}
            </div>
          )}
          <p className="text-gray-500 text-center py-8">
            Click "Generate Recap" to get a summary of the meeting
          </p>
        </div>
      )}
    </div>
  );
}
