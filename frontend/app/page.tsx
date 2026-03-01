"use client";

import { useState, useEffect } from "react";
import { ArrowRight, AlertCircle, FolderOpen, Loader2, Trash2 } from "lucide-react";
import InPersonMode from "./components/InPersonMode";
import { checkBackendHealth, api } from "./lib/api";

function sessionDisplayName(sessionId: string): string {
  return sessionId.replace(/^inperson_/, "") || sessionId;
}

export default function Home() {
  const [mode, setMode] = useState<"in-person" | null>(null);
  const [initialSessionId, setInitialSessionId] = useState<string | null>(null);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [sessions, setSessions] = useState<string[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  useEffect(() => {
    checkBackendHealth().then(({ ok }) => setBackendOk(ok));
    const t = setInterval(() => checkBackendHealth().then(({ ok }) => setBackendOk(ok)), 10000);
    return () => clearInterval(t);
  }, []);

  const loadSessions = () => {
    if (!backendOk) return;
    setSessionsLoading(true);
    api.listSessions().then((r) => { setSessions(r.session_ids || []); setSessionsLoading(false); }).catch(() => setSessionsLoading(false));
  };

  useEffect(() => {
    if (!backendOk) return;
    loadSessions();
  }, [backendOk]);

  const inPersonSessions = sessions.filter((s) => s.startsWith("inperson_"));

  const openSession = (sessionId: string) => {
    setInitialSessionId(sessionId);
    setMode("in-person");
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this session? Transcript, recap, and Q&A for it will be removed.")) return;
    try {
      await api.deleteSession(sessionId);
      if (initialSessionId === sessionId) {
        setInitialSessionId(null);
        setMode(null);
      }
      loadSessions();
    } catch (err) {
      console.error(err);
      alert("Failed to delete session.");
    }
  };

  const goBack = () => {
    setMode(null);
    setInitialSessionId(null);
  };

  if (mode === "in-person") {
    return <InPersonMode onBack={goBack} initialSessionId={initialSessionId ?? undefined} sessions={inPersonSessions} onOpenSession={openSession} onDeleteSession={handleDeleteSession} onRefreshSessions={loadSessions} />;
  }

  return (
    <>
      {backendOk === false && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 max-w-xl w-full mx-4 bg-amber-50 border border-amber-300 text-amber-900 rounded-lg px-4 py-3 shadow flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <div className="text-sm">
            <strong>Backend not connected.</strong> Upload and recap will fail. Start the backend:{" "}
            <code className="bg-amber-100 px-1 rounded text-xs">cd backend && python -m uvicorn app.main:app --reload --port 8000</code>
          </div>
        </div>
      )}
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="max-w-4xl w-full">
        <div className="text-center mb-12">
          <h1 className="text-8xl font-bold text-gray-900 mb-4">CatchUp</h1>
          <p className="text-xl text-gray-600 mb-2">
            Get back on track when you zone out
          </p>
          <p className="text-sm text-gray-500 max-w-2xl mx-auto">
            Zone out for five minutes? Ten? Doesn&apos;t matter. Ask a question, generate a recap, and get back into the conversation like you never left.
          </p>
        </div>

        <div className="flex justify-center">
          <button
            onClick={() => setMode("in-person")}
            className="bg-white rounded-2xl shadow-lg p-8 hover:shadow-xl transition-shadow border-2 border-transparent hover:border-green-500 text-left max-w-md w-full flex items-center justify-center gap-2 text-xl font-bold text-green-600"
          >
            Get Started
            <ArrowRight className="w-6 h-6" />
          </button>
        </div>

        {/* Your sessions — quick access for ADHD-friendly flow */}
        <div className="mt-12 w-full max-w-2xl mx-auto">
          <h2 className="text-lg font-bold text-gray-900 mb-3 flex items-center gap-2">
            <FolderOpen className="w-5 h-5 text-indigo-600" />
            Your sessions
          </h2>
          <p className="text-sm text-gray-600 mb-3">
            Open any session to view transcript, recap, and Q&A.
          </p>
          {sessionsLoading ? (
            <div className="flex items-center gap-2 text-gray-500 text-sm py-4">
              <Loader2 className="w-4 h-4 animate-spin" />
              Loading sessions…
            </div>
          ) : inPersonSessions.length === 0 ? (
            <p className="text-sm text-gray-500 py-4 bg-gray-50 rounded-xl px-4">
              No sessions yet. Click Get Started, then record or upload to see your sessions here.
            </p>
          ) : (
            <ul className="space-y-2 bg-white rounded-xl border border-gray-200 divide-y divide-gray-100 overflow-hidden">
              {inPersonSessions.map((sid) => (
                <li key={sid}>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => openSession(sid)}
                      className="flex-1 text-left px-4 py-3 hover:bg-indigo-50 flex items-center justify-between gap-2 transition-colors"
                    >
                      <span className="font-medium text-gray-900 truncate">{sessionDisplayName(sid)}</span>
                      <span className="text-xs text-gray-500 shrink-0">In-person</span>
                    </button>
                    <button
                      type="button"
                      onClick={(e) => handleDeleteSession(sid, e)}
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors shrink-0"
                      title="Delete session"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="mt-12 text-center">
          <div className="inline-block bg-blue-50 border border-blue-200 rounded-lg px-6 py-3">
            <p className="text-sm text-blue-900 font-medium mb-1">
              ♿ Built for Accessibility
            </p>
            <p className="text-xs text-blue-700">
              Evidence-based answers • Real-time captions • Cognitive support • Stress reduction
            </p>
          </div>
        </div>
      </div>
      </div>
    </>
  );
}
