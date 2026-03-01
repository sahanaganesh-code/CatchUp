"use client";

import { useState, useEffect } from "react";
import { StickyNote, Plus, Trash2, Edit2, Save, X } from "lucide-react";
import { api, Note } from "../lib/api";

interface NotesPanelProps {
  sessionId: string;
}

export default function NotesPanel({ sessionId }: NotesPanelProps) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);

  const [newNoteTitle, setNewNoteTitle] = useState("");
  const [newNoteContent, setNewNoteContent] = useState("");
  const [newNoteDate, setNewNoteDate] = useState(
    new Date().toISOString().split("T")[0]
  );

  useEffect(() => {
    loadNotes();
  }, [sessionId]);

  const loadNotes = async () => {
    try {
      const allNotes = await api.getNotes(sessionId);
      setNotes(allNotes);
    } catch (error) {
      console.error("Error loading notes:", error);
    }
  };

  const handleCreateNote = async () => {
    if (!newNoteTitle.trim() || !newNoteContent.trim()) return;

    try {
      const note = await api.createNote(
        sessionId,
        newNoteTitle,
        newNoteContent,
        newNoteDate
      );
      setNotes([note, ...notes]);
      setNewNoteTitle("");
      setNewNoteContent("");
      setShowCreateForm(false);
    } catch (error) {
      console.error("Error creating note:", error);
      alert("Error creating note");
    }
  };

  const handleDelete = async (noteId: string) => {
    try {
      await api.deleteNote(noteId);
      setNotes(notes.filter((n) => n.note_id !== noteId));
    } catch (error) {
      console.error("Error deleting note:", error);
    }
  };

  return (
    <div className="bg-[#2e6a4f] rounded-xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <StickyNote className="w-5 h-5 text-green-200 mr-2" />
          <h2 className="text-xl font-bold text-white">Live Notes</h2>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-[#256055] text-white px-4 py-2 rounded-lg font-medium hover:bg-[#1e5249] flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          New Note
        </button>
      </div>

      {/* Create Note Form */}
      {showCreateForm && (
        <div className="mb-4 border border-green-600 rounded-lg p-4 bg-white">
          <input
            type="text"
            value={newNoteTitle}
            onChange={(e) => setNewNoteTitle(e.target.value)}
            placeholder="Note title..."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-2 bg-white focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
          <textarea
            value={newNoteContent}
            onChange={(e) => setNewNoteContent(e.target.value)}
            placeholder="Note content..."
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-2 bg-white focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={newNoteDate}
              onChange={(e) => setNewNoteDate(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
            <button
              onClick={handleCreateNote}
              className="bg-[#256055] text-white px-4 py-2 rounded-lg font-medium hover:bg-[#1e5249] flex items-center"
            >
              <Save className="w-4 h-4 mr-2" />
              Save Note
            </button>
            <button
              onClick={() => setShowCreateForm(false)}
              className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-300"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Notes List */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {notes.length === 0 ? (
          <p className="text-green-100 text-center py-8">
            No notes yet. Click "New Note" to create one.
          </p>
        ) : (
          notes.map((note) => (
            <div
              key={note.note_id}
              className="border border-green-600 rounded-lg p-4 bg-white"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{note.title}</h3>
                  <p className="text-xs text-gray-500 mt-1">
                    📅 {note.date}
                  </p>
                </div>
                <button
                  onClick={() => handleDelete(note.note_id)}
                  className="text-gray-400 hover:text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {note.content}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
