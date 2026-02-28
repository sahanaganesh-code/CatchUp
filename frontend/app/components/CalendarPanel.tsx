"use client";

import { useState } from "react";
import { Calendar, Trash2, Loader2, Clock } from "lucide-react";
import { api, CalendarEvent } from "../lib/api";
import EvidenceList from "./EvidenceList";

interface CalendarPanelProps {
  sessionId: string;
}

export default function CalendarPanel({ sessionId }: CalendarPanelProps) {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);

  const handleGenerateEvents = async () => {
    setLoading(true);
    try {
      const generatedEvents = await api.generateEvents(sessionId);
      setEvents(generatedEvents);
    } catch (error) {
      console.error("Error generating events:", error);
      alert("Error generating calendar events");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (eventId: string) => {
    try {
      await api.deleteEvent(eventId);
      setEvents(events.filter((e) => e.event_id !== eventId));
    } catch (error) {
      console.error("Error deleting event:", error);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">Calendar Events</h2>
        <button
          onClick={handleGenerateEvents}
          disabled={loading}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-purple-700 disabled:bg-gray-300 flex items-center"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Extracting...
            </>
          ) : (
            "Extract Events"
          )}
        </button>
      </div>

      <div className="space-y-3">
        {events.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            Click "Extract Events" to find calendar events mentioned in the meeting
          </p>
        ) : (
          events.map((event) => (
            <div
              key={event.event_id}
              className="border border-purple-200 rounded-lg p-4 hover:border-purple-300"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Calendar className="w-4 h-4 text-purple-600" />
                    <h3 className="font-semibold text-gray-900">
                      {event.title}
                    </h3>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">
                    {event.description}
                  </p>

                  <div className="flex flex-wrap gap-2 text-xs">
                    {event.date && (
                      <span className="bg-purple-50 text-purple-700 px-2 py-1 rounded">
                        📅 {event.date}
                      </span>
                    )}
                    {event.time && (
                      <span className="bg-purple-50 text-purple-700 px-2 py-1 rounded">
                        🕐 {event.time}
                      </span>
                    )}
                    {event.duration_minutes && (
                      <span className="bg-purple-50 text-purple-700 px-2 py-1 rounded">
                        ⏱️ {event.duration_minutes} min
                      </span>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => handleDelete(event.event_id)}
                  className="text-gray-400 hover:text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Evidence */}
              <div className="mt-3">
                <button
                  onClick={() =>
                    setExpandedEvent(
                      expandedEvent === event.event_id ? null : event.event_id
                    )
                  }
                  className="text-xs text-purple-600 hover:text-purple-700 font-medium"
                >
                  {expandedEvent === event.event_id
                    ? "Hide Evidence"
                    : `Show Evidence (${event.evidence.length})`}
                </button>

                {expandedEvent === event.event_id && (
                  <div className="mt-2">
                    <EvidenceList evidence={event.evidence} compact />
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
