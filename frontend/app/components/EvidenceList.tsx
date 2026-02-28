"use client";

import { Clock } from "lucide-react";
import { Evidence } from "../lib/api";

interface EvidenceListProps {
  evidence: Evidence[];
  compact?: boolean;
}

export default function EvidenceList({
  evidence,
  compact = false,
}: EvidenceListProps) {
  if (evidence.length === 0) {
    return null;
  }

  return (
    <div
      className={`${
        compact ? "bg-gray-50" : "bg-blue-50 border border-blue-200"
      } rounded-lg p-3`}
    >
      <h4
        className={`text-xs font-semibold ${
          compact ? "text-gray-700" : "text-blue-900"
        } mb-2 flex items-center`}
      >
        <Clock className="w-3 h-3 mr-1" />
        Evidence ({evidence.length} quotes)
      </h4>
      <div className="space-y-2">
        {evidence.map((ev, index) => (
          <div
            key={index}
            className={`${
              compact ? "bg-white" : "bg-white"
            } rounded p-2 text-xs`}
          >
            <div className="flex items-start gap-2">
              <span
                className={`font-mono ${
                  compact ? "text-gray-600" : "text-blue-600"
                } font-semibold whitespace-nowrap`}
              >
                [{ev.timestamp}]
              </span>
              <div className="flex-1">
                {ev.speaker && (
                  <span className="font-semibold text-gray-700">
                    {ev.speaker}:{" "}
                  </span>
                )}
                <span className="text-gray-700">"{ev.quote}"</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
