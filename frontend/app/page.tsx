"use client";

import { useState } from "react";
import { Video, Mic } from "lucide-react";
import ZoomMode from "./components/ZoomMode";
import InPersonMode from "./components/InPersonMode";
import AIChatbot from "./components/AIChatbot";

export default function Home() {
  const [mode, setMode] = useState<"zoom" | "in-person" | null>(null);

  if (mode === "zoom") {
    return <ZoomMode onBack={() => setMode(null)} />;
  }

  if (mode === "in-person") {
    return <InPersonMode onBack={() => setMode(null)} />;
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
          {/* Zoom Mode */}
          <button
            onClick={() => setMode("zoom")}
            className="bg-white rounded-2xl shadow-lg p-8 hover:shadow-xl transition-shadow border-2 border-transparent hover:border-blue-500 text-left"
          >
            <div className="flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-6">
              <Video className="w-8 h-8 text-blue-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-3">
              Zoom Meeting Mode
            </h2>
            <p className="text-gray-600 mb-4">
              Real-time captions and transcripts for remote work, online classes, 
              and telehealth appointments. Perfect for hearing accessibility.
            </p>
            <div className="flex items-center text-sm text-blue-600 font-medium">
              Get Started →
            </div>
          </button>

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
