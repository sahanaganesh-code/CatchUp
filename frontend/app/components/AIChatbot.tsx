"use client";

import { useState } from "react";
import { Bot, Send, Loader2, X } from "lucide-react";
import { api, ChatbotResponse } from "../lib/api";
import EvidenceList from "./EvidenceList";

interface ChatMessage {
  type: "user" | "bot";
  content: string;
  response?: ChatbotResponse;
}

export default function AIChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      type: "user",
      content: input,
    };

    setMessages([...messages, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await api.chatbot(input);

      const botMessage: ChatMessage = {
        type: "bot",
        content: response.answer,
        response,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error("Error in chatbot:", error);
      const errorMessage: ChatMessage = {
        type: "bot",
        content: "Sorry, I encountered an error. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-[#2e6a4f] text-white p-4 rounded-full shadow-lg hover:bg-[#256055] hover:shadow-xl transition-all z-50"
      >
        <Bot className="w-6 h-6" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 h-[600px] bg-white rounded-2xl shadow-2xl flex flex-col z-50 border border-gray-200">
      {/* Header */}
      <div className="bg-[#2e6a4f] text-white p-4 rounded-t-2xl flex items-center justify-between">
        <div className="flex items-center">
          <Bot className="w-5 h-5 mr-2" />
          <h3 className="font-bold">AI Assistant</h3>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="hover:bg-white/20 rounded p-1"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <Bot className="w-12 h-12 mx-auto mb-3 text-gray-400" />
            <p className="text-sm">
              Ask me anything about your meetings, notes, todos, or calendar
              events!
            </p>
            <p className="text-xs mt-2 text-gray-400">
              All answers include evidence quotes
            </p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index}>
              {msg.type === "user" ? (
                <div className="flex justify-end">
                  <div className="bg-[#2e6a4f] text-white px-4 py-2 rounded-2xl rounded-tr-sm max-w-[80%]">
                    {msg.content}
                  </div>
                </div>
              ) : (
                <div className="flex justify-start">
                  <div className="bg-gray-100 text-gray-900 px-4 py-2 rounded-2xl rounded-tl-sm max-w-[85%]">
                    <p className="mb-2">{msg.content}</p>
                    {msg.response && msg.response.has_sufficient_evidence && (
                      <div className="mt-2">
                        <EvidenceList
                          evidence={msg.response.evidence}
                          compact
                        />
                        {msg.response.sources.length > 0 && (
                          <div className="mt-2 text-xs text-gray-500">
                            Sources: {msg.response.sources.join(", ")}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 px-4 py-2 rounded-2xl rounded-tl-sm">
              <Loader2 className="w-4 h-4 animate-spin text-gray-600" />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter" && !loading) handleSend();
            }}
            placeholder="Ask about meetings, notes, todos..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#2e6a4f] focus:border-transparent"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="bg-[#2e6a4f] text-white px-4 py-2 rounded-lg hover:bg-[#256055] disabled:bg-gray-300"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
