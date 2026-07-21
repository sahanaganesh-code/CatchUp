"use client";

import { useState } from "react";
import { MessageCircle, Send, Loader2 } from "lucide-react";
import { api, QuestionResponse } from "../lib/api";
import EvidenceList from "./EvidenceList";
import MarkdownAnswer from "./MarkdownAnswer";

interface QAPanelProps {
  sessionId: string;
}

interface QAItem {
  question: string;
  response: QuestionResponse;
}

export default function QAPanel({ sessionId }: QAPanelProps) {
  const [question, setQuestion] = useState("");
  const [qaHistory, setQaHistory] = useState<QAItem[]>([]);
  const [loading, setLoading] = useState(false);

  const handleAskQuestion = async () => {
    if (!question.trim()) return;

    setLoading(true);
    const currentQuestion = question;
    setQuestion("");

    try {
      const response = await api.askQuestion(sessionId, currentQuestion);
      setQaHistory([...qaHistory, { question: currentQuestion, response }]);
    } catch (error) {
      console.error("Error asking question:", error);
      alert("Error asking question");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center mb-4">
        <MessageCircle className="w-5 h-5 text-green-600 mr-2" />
        <h2 className="text-xl font-bold text-gray-900">Grounded Q&A</h2>
      </div>

      {/* Question Input */}
      <div className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about the meeting..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            onKeyPress={(e) => {
              if (e.key === "Enter" && !loading) handleAskQuestion();
            }}
            disabled={loading}
          />
          <button
            onClick={handleAskQuestion}
            disabled={loading || !question.trim()}
            className="bg-green-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-green-700 disabled:bg-gray-300 flex items-center"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          All answers include 2-5 evidence quotes with timestamps
        </p>
      </div>

      {/* Q&A History */}
      <div className="space-y-6 max-h-96 overflow-y-auto">
        {qaHistory.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            Ask a question to get started
          </p>
        ) : (
          qaHistory.map((item, index) => (
            <div key={index} className="border-b pb-4 last:border-b-0">
              <div className="mb-3">
                <p className="font-semibold text-gray-900 mb-2">
                  Q: {item.question}
                </p>
                <MarkdownAnswer>{item.response.answer}</MarkdownAnswer>
              </div>

              {item.response.has_sufficient_evidence ? (
                <EvidenceList evidence={item.response.evidence} />
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-sm text-yellow-800">
                    ⚠️ Insufficient evidence in transcript
                  </p>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
