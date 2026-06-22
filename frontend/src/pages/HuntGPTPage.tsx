import React, { useEffect, useRef, useState } from 'react';
import { useCyberStore } from '../store/cyberStore';
import { Send, Trash2, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const SUGGESTED_PROMPTS = [
  "Why is DB01 risky?",
  "Summarize incidents",
  "Containment suggestions",
  "Generate executive report"
];

export default function HuntGPTPage() {
  const { chatHistory, huntgptLoading, sendHuntGPTQuery, clearChat, fetchAllData } = useCyberStore();
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, huntgptLoading]);

  // Fetch initial data
  useEffect(() => {
    fetchAllData();
  }, []);

  const handleSend = () => {
    if (!input.trim()) return;
    sendHuntGPTQuery(input);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") handleSend();
  };

  return (
    <div className="flex h-[calc(100vh-88px)]">
      {/* Sidebar: Suggested prompts */}
      <div className="w-64 bg-card border-r border-border p-4">
        <h3 className="text-lg font-semibold mb-4">Suggested Prompts</h3>
        <div className="space-y-2">
          {SUGGESTED_PROMPTS.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => {
              setInput(prompt);
              sendHuntGPTQuery(prompt);
            }}
            className="w-full text-left px-3 py-2 rounded-md bg-bg border border-border hover:bg-accent/10 transition"
            >
              {prompt}
            </button>
          ))}
        </div>
        <button
          onClick={clearChat}
          className="mt-4 w-full flex items-center gap-2 justify-center px-3 py-2 rounded-md text-textSecondary hover:text-red-400 hover:bg-red-900/20 transition"
        >
          <Trash2 size={16} />
          Clear Chat
        </button>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col bg-bg">
        {/* Messages container */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {chatHistory.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-textSecondary">
              <p className="text-lg">Ask HuntGPT about your security data</p>
            </div>
          )}
          {chatHistory.map((msg, idx) => (
            <div
              key={idx}
              className={`max-w-3xl mx-auto p-4 rounded-lg ${
                msg.role === "user"
                  ? "bg-accent/20 text-accent ml-auto"
                  : "bg-card text-textPrimary"
              }`}
            >
              {msg.role === "assistant" ? (
                <div className="prose prose-invert">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                  {msg.data && (
                    <div className="mt-4 pt-4 border-t border-border">
                      {/* Optional: Display mitre, assets, incidents, recommendations here if needed
                      For now keep simple */}
                    </div>
                  )}
                </div>
              ) : (
                <p>{msg.content}</p>
              )}
            </div>
          ))}
          {huntgptLoading && (
            <div className="flex items-center justify-center gap-2 text-textSecondary">
              <Loader2 className="animate-spin" />
              <span>Analyzing...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="border-t border-border p-4">
          <div className="max-w-4xl mx-auto flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask HuntGPT..."
              className="flex-1 px-4 py-3 rounded-md bg-card border border-border focus:outline-none"
            />
            <button
              onClick={handleSend}
              disabled={huntgptLoading}
              className="flex items-center gap-2 px-4 py-3 bg-accent rounded-md hover:bg-cyan-600 transition"
            >
              <Send size={20} />
            </button>

          </div>
        </div>
      </div>
    </div>
  );
}
