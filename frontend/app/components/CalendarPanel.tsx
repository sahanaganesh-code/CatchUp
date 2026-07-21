"use client";

import { useState, useEffect } from "react";
import { Calendar, Trash2, Loader2, Edit2, Save, X, CalendarPlus } from "lucide-react";
import { api, CalendarEvent } from "../lib/api";
import EvidenceList from "./EvidenceList";

interface CalendarPanelProps {
  sessionId: string;
}

interface EditForm {
  title: string;
  description: string;
  date: string;
  time: string;
  duration_minutes: string;
}

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

function buildGoogleCalendarUrl(event: CalendarEvent): string | null {
  if (!event.date) return null;

  const [y, m, d] = event.date.split("-").map(Number);
  if (!y || !m || !d) return null;

  const params = new URLSearchParams();
  params.set("action", "TEMPLATE");
  params.set("text", event.title);
  params.set("details", event.description || "");

  if (event.time) {
    const [hh, mm] = event.time.split(":").map(Number);
    const start = new Date(y, m - 1, d, hh || 0, mm || 0);
    const duration = event.duration_minutes ?? 60;
    const end = new Date(start.getTime() + duration * 60000);
    const fmt = (dt: Date) =>
      `${dt.getFullYear()}${pad(dt.getMonth() + 1)}${pad(dt.getDate())}T${pad(dt.getHours())}${pad(dt.getMinutes())}00`;
    params.set("dates", `${fmt(start)}/${fmt(end)}`);
  } else {
    const start = new Date(y, m - 1, d);
    const end = new Date(start.getTime() + 24 * 60 * 60 * 1000);
    const fmtDay = (dt: Date) => `${dt.getFullYear()}${pad(dt.getMonth() + 1)}${pad(dt.getDate())}`;
    params.set("dates", `${fmtDay(start)}/${fmtDay(end)}`);
  }

  return `https://calendar.google.com/calendar/render?${params.toString()}`;
}

export default function CalendarPanel({ sessionId }: CalendarPanelProps) {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);
  const [editingEventId, setEditingEventId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<EditForm | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getEvents(sessionId).then(setEvents).catch((error) => {
      console.error("Error loading events:", error);
    });
  }, [sessionId]);

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

  const handleEditStart = (event: CalendarEvent) => {
    setEditingEventId(event.event_id);
    setEditForm({
      title: event.title,
      description: event.description,
      date: event.date || "",
      time: event.time || "",
      duration_minutes: event.duration_minutes ? String(event.duration_minutes) : "",
    });
  };

  const handleEditCancel = () => {
    setEditingEventId(null);
    setEditForm(null);
  };

  const handleEditSave = async (eventId: string) => {
    if (!editForm) return;
    setSaving(true);
    try {
      const updated = await api.updateEvent(eventId, {
        title: editForm.title,
        description: editForm.description,
        date: editForm.date || undefined,
        time: editForm.time || undefined,
        duration_minutes: editForm.duration_minutes ? parseInt(editForm.duration_minutes, 10) : undefined,
      });
      setEvents(events.map((e) => (e.event_id === eventId ? updated : e)));
      setEditingEventId(null);
      setEditForm(null);
    } catch (error) {
      console.error("Error updating event:", error);
      alert("Error updating event");
    } finally {
      setSaving(false);
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
          events.map((event) => {
            const isEditing = editingEventId === event.event_id;
            const gcalUrl = buildGoogleCalendarUrl(event);

            if (isEditing && editForm) {
              return (
                <div
                  key={event.event_id}
                  className="border border-purple-300 rounded-lg p-4 bg-purple-50"
                >
                  <input
                    type="text"
                    value={editForm.title}
                    onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                    placeholder="Event title..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-2 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                  <textarea
                    value={editForm.description}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    placeholder="Description..."
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-2 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    <input
                      type="date"
                      value={editForm.date}
                      onChange={(e) => setEditForm({ ...editForm, date: e.target.value })}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                    <input
                      type="time"
                      value={editForm.time}
                      onChange={(e) => setEditForm({ ...editForm, time: e.target.value })}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                    <input
                      type="number"
                      min={0}
                      value={editForm.duration_minutes}
                      onChange={(e) => setEditForm({ ...editForm, duration_minutes: e.target.value })}
                      placeholder="Duration (min)"
                      className="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleEditSave(event.event_id)}
                      disabled={saving || !editForm.title.trim()}
                      className="bg-purple-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-purple-700 disabled:bg-gray-300 flex items-center"
                    >
                      {saving ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Save className="w-4 h-4 mr-2" />
                          Save
                        </>
                      )}
                    </button>
                    <button
                      onClick={handleEditCancel}
                      className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-300"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            }

            return (
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

                  <div className="flex items-center gap-1 ml-2">
                    <button
                      onClick={() => handleEditStart(event)}
                      className="text-gray-400 hover:text-purple-600 p-1"
                      title="Edit event"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(event.event_id)}
                      className="text-gray-400 hover:text-red-600 p-1"
                      title="Delete event"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between mt-3">
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

                  {gcalUrl && (
                    <a
                      href={gcalUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center text-xs bg-white border border-purple-300 text-purple-700 px-3 py-1.5 rounded-lg font-medium hover:bg-purple-50"
                    >
                      <CalendarPlus className="w-3.5 h-3.5 mr-1.5" />
                      Add to Calendar
                    </a>
                  )}
                </div>

                {expandedEvent === event.event_id && (
                  <div className="mt-2">
                    <EvidenceList evidence={event.evidence} compact />
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
