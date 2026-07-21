"use client";

import { useState } from "react";
import { Mic, ScreenShare, History } from "lucide-react";
import InPersonMode from "./components/InPersonMode";
import ScreenCaptureMode from "./components/ScreenCaptureMode";
import SessionHistory from "./components/SessionHistory";
import AIChatbot from "./components/AIChatbot";

export default function Home() {
  const [mode, setMode] = useState<"in-person" | "screen-share" | "history" | null>(null);

  if (mode === "in-person") {
    return <InPersonMode onBack={() => setMode(null)} />;
  }

  if (mode === "screen-share") {
    return <ScreenCaptureMode onBack={() => setMode(null)} />;
  }

  if (mode === "history") {
    return <SessionHistory onBack={() => setMode(null)} />;
  }

  return (
    <>
      <AIChatbot />
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="max-w-4xl w-full">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">CatchUp</h1>
          <p className="text-xl text-gray-600 mb-2">
            Accessible Meeting Assistant for Everyone
          </p>
          <p className="text-sm text-gray-500 max-w-2xl mx-auto">
            Empowering students with disabilities, ADHD, hearing impairments, and cognitive challenges through real-time transcription and evidence-based Q&A
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* In-Person Mode */}
          <button
            onClick={() => setMode("in-person")}
            className="bg-white rounded-2xl shadow-lg p-8 hover:shadow-xl transition-shadow border-2 border-transparent hover:border-green-500 text-left"
          >
            <div className="flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-6">
              <Mic className="w-8 h-8 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-3">
              In-Person Lecture Mode
            </h2>
            <p className="text-gray-600 mb-4">
              Record classes, therapy sessions, or support groups. Focus on
              participating instead of note-taking. Ideal for ADHD and learning disabilities.
            </p>
            <div className="flex items-center text-sm text-green-600 font-medium">
              Get Started →
            </div>
          </button>

          {/* Screen Share Mode */}
          <button
            onClick={() => setMode("screen-share")}
            className="bg-white rounded-2xl shadow-lg p-8 hover:shadow-xl transition-shadow border-2 border-transparent hover:border-amber-500 text-left"
          >
            <div className="flex items-center justify-center w-16 h-16 bg-amber-100 rounded-full mb-6">
              <ScreenShare className="w-8 h-8 text-amber-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-3">
              Screen Share Mode
            </h2>
            <p className="text-gray-600 mb-4">
              Share your screen during a Zoom call, webinar, or video and get live
              transcription and evidence-based Q&A. No platform integration needed.
            </p>
            <div className="flex items-center text-sm text-amber-600 font-medium">
              Get Started →
            </div>
          </button>
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={() => setMode("history")}
            className="inline-flex items-center text-sm text-indigo-600 hover:text-indigo-800 font-medium"
          >
            <History className="w-4 h-4 mr-1.5" />
            View Past Sessions
          </button>
        </div>

        <div className="mt-8 text-center">
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
