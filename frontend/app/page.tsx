"use client";

import { useState, useEffect } from "react";
import { Video, Mic } from "lucide-react";
import MeetMode from "./components/MeetMode";
import InPersonMode from "./components/InPersonMode";
import AIChatbot from "./components/AIChatbot";

// TEMPORARY TEST ONLY: sessionStorage keys for login/name flow. Remove when done testing.
const TEST_USER_KEY = "catchup_test_user";
const TEST_NAME_KEY = "catchup_test_name";

export default function Home() {
  const [mode, setMode] = useState<"google_meet" | "in-person" | null>(null);

  // TEMPORARY: auth step and stored name for welcome message
  const [authStep, setAuthStep] = useState<"login" | "home">("login");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [savedName, setSavedName] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedName = sessionStorage.getItem(TEST_NAME_KEY);
    if (storedName) {
      setSavedName(storedName);
      setAuthStep("home");
    }
  }, []);

  const capitalizeName = (s: string) =>
    s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    const raw = name.trim();
    if (!raw) return;
    const capitalizedName = capitalizeName(raw);
    sessionStorage.setItem(TEST_USER_KEY, capitalizedName);
    sessionStorage.setItem(TEST_NAME_KEY, capitalizedName);
    setSavedName(capitalizedName);
    setAuthStep("home");
  };

  const handleLogout = () => {
    sessionStorage.removeItem(TEST_USER_KEY);
    sessionStorage.removeItem(TEST_NAME_KEY);
    if (typeof window !== "undefined") {
      localStorage.removeItem("catchup_meet_history");
      localStorage.removeItem("catchup_inperson_history");
    }
    setSavedName(null);
    setName("");
    setPassword("");
    setAuthStep("login");
  };

  if (mode === "google_meet") {
    return <MeetMode onBack={() => setMode(null)} userName={savedName} />;
  }

  if (mode === "in-person") {
    return <InPersonMode onBack={() => setMode(null)} userName={savedName} />;
  }

  // TEMPORARY: Login screen
  if (authStep === "login") {
    return (
      <div className="min-h-screen w-full flex flex-col items-center justify-center p-4 bg-[#f0e6d3]">
        {/* Logo above sign-in box - same green as sign-in box (#2e6a4f) via mask */}
        <div
          role="img"
          aria-label="CatchUp logo"
          className="w-32 h-32 mb-6 bg-[#2e6a4f]"
          style={{
            maskImage: "url(/logo.png)",
            maskSize: "contain",
            maskRepeat: "no-repeat",
            maskPosition: "center",
            WebkitMaskImage: "url(/logo.png)",
            WebkitMaskSize: "contain",
            WebkitMaskRepeat: "no-repeat",
            WebkitMaskPosition: "center",
          }}
        />
        <div className="bg-[#2e6a4f] rounded-xl shadow-lg p-8 max-w-md w-full">
          <h1 className="text-2xl font-bold text-white mb-2 font-['Trebuchet_MS']">CatchUp</h1>
          <p className="text-green-100 mb-6">Sign in to continue (test only)</p>
          <form onSubmit={handleLogin} className="space-y-4">
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Name"
              className="w-full px-4 py-3 rounded-lg bg-white border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-transparent"
              required
            />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              className="w-full px-4 py-3 rounded-lg bg-white border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
            <button
              type="submit"
              className="w-full bg-[#256055] text-white py-3 rounded-lg font-medium hover:bg-[#1e5249]"
            >
              Continue
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <>
      <AIChatbot />
      <div className="min-h-screen w-full flex items-center justify-center p-4 bg-[#f0e6d3] relative">
        {savedName && (
          <button
            type="button"
            onClick={handleLogout}
            className="absolute top-4 right-4 text-sm text-gray-600 hover:text-gray-900 underline"
          >
            Log out (test only)
          </button>
        )}
        <div className="max-w-4xl w-full">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-4 mb-4">
            <h1 className="text-5xl font-bold text-gray-900 font-['Trebuchet_MS']">CatchUp</h1>
            <div
              role="img"
              aria-label="CatchUp logo"
              className="w-14 h-14 shrink-0 bg-[#2e6a4f]"
              style={{
                maskImage: "url(/logo.png)",
                maskSize: "contain",
                maskRepeat: "no-repeat",
                maskPosition: "center",
                WebkitMaskImage: "url(/logo.png)",
                WebkitMaskSize: "contain",
                WebkitMaskRepeat: "no-repeat",
                WebkitMaskPosition: "center",
              }}
            />
          </div>
          <p className={`text-xl mb-2 ${savedName ? "text-gray-900 font-medium" : "text-gray-600"}`}>
            {savedName ? `Welcome to CatchUp, ${savedName}` : "Accessible Meeting Assistant for Everyone"}
          </p>
          <div className="inline-block bg-transparent border-2 border-[#2e6a4f] rounded-lg px-4 py-3 max-w-2xl mx-auto">
            <p className="text-sm text-gray-600">
              Empowering all students, including those with disabilities, ADHD, hearing impairments, and cognitive challenges, through real-time transcription and evidence-based Q&A.
            </p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Google Meet Mode */}
          <button
            type="button"
            onClick={() => setMode("google_meet")}
            className="bg-[#2e6a4f] rounded-2xl p-8 transition-shadow hover:bg-[#256055] hover:shadow-lg text-left cursor-pointer"
          >
            <div className="flex items-center justify-center w-16 h-16 bg-[#256055] rounded-full mb-6">
              <Video className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-3">
              Google Meet Mode
            </h2>
            <p className="text-green-100 mb-4">
              Live captions and transcripts from Google Meet. Integrates with 
              Google Calendar, Tasks, Gmail, and Slides. 
            </p>
            <div className="flex items-center text-sm text-green-200 font-medium">
              Get Started →
            </div>
          </button>

          {/* In-Person Mode */}
          <button
            type="button"
            onClick={() => setMode("in-person")}
            className="bg-[#2e6a4f] rounded-2xl p-8 transition-shadow hover:bg-[#256055] hover:shadow-lg text-left cursor-pointer"
          >
            <div className="flex items-center justify-center w-16 h-16 bg-[#256055] rounded-full mb-6">
              <Mic className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-3">
              In-Person Lecture Mode
            </h2>
            <p className="text-green-100 mb-4">
              Record and transcribe classes, therapy sessions, or support groups. Focus on 
              participating instead of note-taking. 
            </p>
            <div className="flex items-center text-sm text-green-200 font-medium">
              Get Started →
            </div>
          </button>
        </div>

        <div className="mt-12 text-center">
          <p className="text-sm text-gray-700 font-medium mb-1">
            Built for Accessibility
          </p>
          <p className="text-xs text-gray-600">
            Evidence-based answers • Real-time captions • Stress reduction
          </p>
        </div>
      </div>
      </div>
    </>
  );
}
