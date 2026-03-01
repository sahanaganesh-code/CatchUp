import axios from "axios";

/** Turn API errors (including network/fetch failures) into a user-friendly string. */
export function getApiErrorMessage(error: unknown, fallback: string): string {
  const err = error as {
    message?: string;
    code?: string;
    response?: { status?: number; data?: { detail?: string; error?: string } };
  };
  if (!err?.response && (err?.code === "ERR_NETWORK" || /fetch|network|failed/i.test(String(err?.message))))
    return "Couldn't reach the backend. Make sure the backend is running (e.g. port 8000).";
  const data = err?.response?.data;
  if (data?.detail && typeof data.detail === "string") return data.detail;
  if (data?.error && typeof data.error === "string") return data.error;
  if (err?.response?.status === 503) return "Backend unreachable. Is the backend server running?";
  return fallback;
}

// In browser: same-origin proxy /api/backend -> no CORS. On server: call backend directly.
const isBrowser = typeof window !== "undefined";
const API_BASE = isBrowser ? "" : (process.env.BACKEND_URL || "http://127.0.0.1:8000");
const API_PREFIX = isBrowser ? "/api/backend" : "/api";

export interface TranscriptChunk {
  timestamp: string;
  text: string;
  speaker?: string;
}

export interface Evidence {
  timestamp: string;
  quote: string;
  speaker?: string;
}

export interface QuestionResponse {
  answer: string;
  evidence: Evidence[];
  has_sufficient_evidence: boolean;
}

export interface RecapResponse {
  summary: string;
  key_points: string[];
  evidence: Evidence[];
}

export interface ProposedAction {
  action_id: string;
  action_type: "notion_task" | "calendar_event" | "email_followup" | "slides";
  title: string;
  description: string;
  evidence: Evidence[];
  metadata: Record<string, any>;
  approved: boolean;
  executed: boolean;
  created_at: string;
}

export interface Note {
  note_id: string;
  session_id: string;
  title: string;
  content: string;
  date: string;
  created_at: string;
  updated_at: string;
}

export interface TodoItem {
  todo_id: string;
  title: string;
  description: string;
  priority: "low" | "medium" | "high";
  due_date?: string;
  evidence: Evidence[];
  completed: boolean;
  created_at: string;
}

export interface CalendarEvent {
  event_id: string;
  title: string;
  description: string;
  date?: string;
  time?: string;
  duration_minutes?: number;
  evidence: Evidence[];
  created_at: string;
}

export interface ChatbotResponse {
  answer: string;
  evidence: Evidence[];
  sources: string[];
  has_sufficient_evidence: boolean;
}

/** Check if the backend is reachable (for "Backend: connected" banner). */
export async function checkBackendHealth(): Promise<{ ok: boolean; message?: string }> {
  try {
    const base = typeof window !== "undefined" ? "" : process.env.BACKEND_URL || "http://127.0.0.1:8000";
    const url = typeof window !== "undefined" ? "/api/backend/health" : `${base}/`;
    const res = await fetch(url, { cache: "no-store", signal: AbortSignal.timeout(3000) });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok && (data.ok === true || data.status === "healthy"), message: data.message };
  } catch {
    return { ok: false, message: "Backend not reachable" };
  }
}

export const api = {
  async ingestTranscript(
    sessionId: string,
    mode: "zoom" | "in-person",
    chunks: TranscriptChunk[]
  ) {
    const response = await axios.post(`${API_BASE}${API_PREFIX}/ingest`, {
      session_id: sessionId,
      mode,
      chunks,
    });
    return response.data;
  },

  async askQuestion(
    sessionId: string,
    question: string
  ): Promise<QuestionResponse> {
    const response = await axios.post(`${API_BASE}${API_PREFIX}/question`, {
      session_id: sessionId,
      question,
    });
    return response.data;
  },

  async getRecap(sessionId: string): Promise<RecapResponse> {
    const response = await axios.post(`${API_BASE}${API_PREFIX}/recap`, {
      session_id: sessionId,
    });
    return response.data;
  },

  async proposeActions(sessionId: string): Promise<ProposedAction[]> {
    const response = await axios.post(`${API_BASE}${API_PREFIX}/actions/propose`, {
      session_id: sessionId,
    });
    return response.data.actions;
  },

  async approveAction(actionId: string, approved: boolean) {
    const response = await axios.post(`${API_BASE}${API_PREFIX}/actions/approve`, {
      action_id: actionId,
      approved,
    });
    return response.data;
  },

  async uploadAudio(sessionId: string, audioFile: File) {
    const formData = new FormData();
    formData.append("audio", audioFile);

    const url = `${API_BASE}${API_PREFIX}/audio/upload?session_id=${encodeURIComponent(sessionId)}`;
    const response = await axios.post(url, formData, {
      maxContentLength: Infinity,
      maxBodyLength: Infinity,
      timeout: 1800000, // 30 min: upload + ffmpeg + transcription for long lectures
    });
    return response.data;
  },

  async getTranscript(sessionId: string): Promise<{
    session_id: string;
    chunks: TranscriptChunk[];
    total_duration: string;
  }> {
    const response = await axios.get(`${API_BASE}${API_PREFIX}/transcript/${sessionId}`);
    return response.data;
  },

  async listSessions(): Promise<{ session_ids: string[] }> {
    const response = await axios.get(`${API_BASE}${API_PREFIX}/sessions`);
    return response.data;
  },

  async createNote(
    sessionId: string,
    title: string,
    content: string,
    date: string
  ): Promise<Note> {
    const response = await axios.post(`${API_BASE}${API_PREFIX}/notes`, {
      session_id: sessionId,
      title,
      content,
      date,
    });
    return response.data;
  },

  async getNotes(sessionId?: string): Promise<Note[]> {
    const params = sessionId ? { session_id: sessionId } : {};
    const response = await axios.get(`${API_BASE}${API_PREFIX}/notes`, { params });
    return response.data.notes;
  },

  async updateNote(
    noteId: string,
    title?: string,
    content?: string
  ): Promise<Note> {
    const response = await axios.put(`${API_BASE}${API_PREFIX}/notes/${noteId}`, {
      note_id: noteId,
      title,
      content,
    });
    return response.data;
  },

  async deleteNote(noteId: string) {
    const response = await axios.delete(`${API_BASE}${API_PREFIX}/notes/${noteId}`);
    return response.data;
  },

  async generateTodos(sessionId: string): Promise<TodoItem[]> {
    const response = await axios.post(`${API_BASE}${API_PREFIX}/todos/generate`, {
      session_id: sessionId,
    });
    return response.data.todos;
  },

  async getTodos(): Promise<TodoItem[]> {
    const response = await axios.get(`${API_BASE}${API_PREFIX}/todos`);
    return response.data.todos;
  },

  async completeTodo(todoId: string, completed: boolean): Promise<TodoItem> {
    const response = await axios.put(
      `${API_BASE}${API_PREFIX}/todos/${todoId}/complete?completed=${completed}`
    );
    return response.data;
  },

  async deleteTodo(todoId: string) {
    const response = await axios.delete(`${API_BASE}${API_PREFIX}/todos/${todoId}`);
    return response.data;
  },

  async generateEvents(sessionId: string): Promise<CalendarEvent[]> {
    const response = await axios.post(`${API_BASE}${API_PREFIX}/events/generate`, {
      session_id: sessionId,
    });
    return response.data.events;
  },

  async getEvents(): Promise<CalendarEvent[]> {
    const response = await axios.get(`${API_BASE}${API_PREFIX}/events`);
    return response.data.events;
  },

  async deleteEvent(eventId: string) {
    const response = await axios.delete(`${API_BASE}${API_PREFIX}/events/${eventId}`);
    return response.data;
  },

  async chatbot(
    question: string,
    contextTypes: ("transcripts" | "notes" | "todos" | "events")[] = [
      "transcripts",
      "notes",
      "todos",
      "events",
    ]
  ): Promise<ChatbotResponse> {
    const response = await axios.post(`${API_BASE}${API_PREFIX}/chatbot`, {
      question,
      context_types: contextTypes,
    });
    return response.data;
  },
};
