import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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
  action_type: "google_tasks" | "google_calendar" | "gmail_followup" | "google_slides";
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

export const api = {
  async ingestTranscript(
    sessionId: string,
    mode: "google_meet" | "in-person",
    chunks: TranscriptChunk[]
  ) {
    const response = await axios.post(`${API_URL}/api/ingest`, {
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
    const response = await axios.post(`${API_URL}/api/question`, {
      session_id: sessionId,
      question,
    });
    return response.data;
  },

  async getRecap(sessionId: string): Promise<RecapResponse> {
    const response = await axios.post(`${API_URL}/api/recap`, {
      session_id: sessionId,
    });
    return response.data;
  },

  async proposeActions(sessionId: string): Promise<ProposedAction[]> {
    const response = await axios.post(`${API_URL}/api/actions/propose`, {
      session_id: sessionId,
    });
    return response.data.actions;
  },

  async approveAction(actionId: string, approved: boolean) {
    const response = await axios.post(`${API_URL}/api/actions/approve`, {
      action_id: actionId,
      approved,
    });
    return response.data;
  },

  async uploadAudio(sessionId: string, audioFile: File) {
    const formData = new FormData();
    formData.append("audio", audioFile);

    const response = await axios.post(
      `${API_URL}/api/audio/upload?session_id=${sessionId}`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  async getTranscript(sessionId: string): Promise<{
    session_id: string;
    chunks: TranscriptChunk[];
    total_duration: string;
  }> {
    const response = await axios.get(`${API_URL}/api/transcript/${sessionId}`);
    return response.data;
  },

  async createNote(
    sessionId: string,
    title: string,
    content: string,
    date: string
  ): Promise<Note> {
    const response = await axios.post(`${API_URL}/api/notes`, {
      session_id: sessionId,
      title,
      content,
      date,
    });
    return response.data;
  },

  async getNotes(sessionId?: string): Promise<Note[]> {
    const params = sessionId ? { session_id: sessionId } : {};
    const response = await axios.get(`${API_URL}/api/notes`, { params });
    return response.data.notes;
  },

  async updateNote(
    noteId: string,
    title?: string,
    content?: string
  ): Promise<Note> {
    const response = await axios.put(`${API_URL}/api/notes/${noteId}`, {
      note_id: noteId,
      title,
      content,
    });
    return response.data;
  },

  async deleteNote(noteId: string) {
    const response = await axios.delete(`${API_URL}/api/notes/${noteId}`);
    return response.data;
  },

  async generateTodos(sessionId: string): Promise<TodoItem[]> {
    const response = await axios.post(`${API_URL}/api/todos/generate`, {
      session_id: sessionId,
    });
    return response.data.todos;
  },

  async getTodos(): Promise<TodoItem[]> {
    const response = await axios.get(`${API_URL}/api/todos`);
    return response.data.todos;
  },

  async completeTodo(todoId: string, completed: boolean): Promise<TodoItem> {
    const response = await axios.put(
      `${API_URL}/api/todos/${todoId}/complete?completed=${completed}`
    );
    return response.data;
  },

  async deleteTodo(todoId: string) {
    const response = await axios.delete(`${API_URL}/api/todos/${todoId}`);
    return response.data;
  },

  async generateEvents(sessionId: string): Promise<CalendarEvent[]> {
    const response = await axios.post(`${API_URL}/api/events/generate`, {
      session_id: sessionId,
    });
    return response.data.events;
  },

  async getEvents(): Promise<CalendarEvent[]> {
    const response = await axios.get(`${API_URL}/api/events`);
    return response.data.events;
  },

  async deleteEvent(eventId: string) {
    const response = await axios.delete(`${API_URL}/api/events/${eventId}`);
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
    const response = await axios.post(`${API_URL}/api/chatbot`, {
      question,
      context_types: contextTypes,
    });
    return response.data;
  },
};
