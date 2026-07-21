"use client";

import ReactMarkdown from "react-markdown";

interface MarkdownAnswerProps {
  children: string;
  className?: string;
}

/** Renders Gemini's markdown-formatted answers (bold, bullet lists, paragraphs) properly instead of as raw asterisks/text. */
export default function MarkdownAnswer({ children, className = "" }: MarkdownAnswerProps) {
  return (
    <div className={`text-gray-800 space-y-2 ${className}`}>
      <ReactMarkdown
        components={{
          p: ({ children }) => <p className="leading-relaxed">{children}</p>,
          ul: ({ children }) => <ul className="list-disc pl-5 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-5 space-y-1">{children}</ol>,
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
          code: ({ children }) => (
            <code className="bg-gray-100 text-gray-800 px-1 py-0.5 rounded text-xs font-mono">{children}</code>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
