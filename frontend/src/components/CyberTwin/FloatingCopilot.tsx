import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { X, MessageCircle, Send, Trash2, Sparkles } from 'lucide-react';
import { useCyberStore } from '../../store/cyberStore';

const SUGGESTED_PROMPTS = [
  "Why is DB01 risky?",
  "Summarize incidents",
  "Generate executive report",
  "Containment suggestions",
  "What changed after latest upload?",
  "Which assets were added?",
  "Show suspicious assets",
  "Show MITRE coverage"
];

export function FloatingCopilot() {
  const { copilotOpen, toggleCopilot, chatHistory, sendHuntGPTQuery, huntgptLoading, clearChat } = useCyberStore();
  const [input, setInput] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, copilotOpen]);

  const handleSend = async (text: string = input) => {
    if (!text.trim()) return;
    await sendHuntGPTQuery(text);
    setInput("");
  };

  return (
    <>
      {/* Floating button */}
      <button
        onClick={toggleCopilot}
        className="fixed bottom-8 right-8 z-50 w-14 h-14 rounded-full bg-cyan-500 hover:bg-cyan-400 shadow-lg shadow-cyan-500/30 flex items-center justify-center transition-all hover:scale-105 active:scale-95"
      >
        {copilotOpen ? <X className="w-7 h-7 text-white" /> : <MessageCircle className="w-7 h-7 text-white" />}
        {!copilotOpen && <span className="absolute -top-1 -right-1 w-4 h-4 bg-pink-500 rounded-full animate-ping" />}
      </button>

      {/* Expanded copilot */}
      {copilotOpen && (
        <div className="fixed bottom-8 right-8 z-50 w-[420px] h-[650px] bg-slate-800 border border-slate-700 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
          {/* Header */}
          <div className="p-4 border-b border-slate-700 flex items-center justify-between bg-slate-800/90">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-full flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-slate-100 font-semibold">CyberTwin Copilot</h3>
                <p className="text-xs text-slate-400">AI SOC Assistant</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={clearChat}
                className="p-2 hover:bg-slate-700 rounded-full text-slate-400 hover:text-slate-100"
              >
                <Trash2 className="w-4 h-4" />
              </button>
              <button
                onClick={toggleCopilot}
                className="p-2 hover:bg-slate-700 rounded-full text-slate-400 hover:text-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Chat area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatHistory.length === 0 && (
              <div className="space-y-3">
                <p className="text-slate-400 text-sm">Ask about your assets, incidents, or security posture!</p>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTED_PROMPTS.map((prompt, i) => (
                    <button
                      key={i}
                      onClick={() => handleSend(prompt)}
                      className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs rounded-full transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {chatHistory.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] px-4 py-3 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-cyan-600 text-white rounded-tr-none'
                      : 'bg-slate-700 text-slate-100 rounded-tl-none'
                  }`}
                >
                  <ReactMarkdown className="text-sm whitespace-pre-wrap">
                    {msg.content}
                  </ReactMarkdown>
                  {msg.data && (msg.data.assets?.length > 0 || msg.data.recommendations?.length > 0) && (
                    <div className="mt-3 pt-3 border-t border-slate-600 text-xs space-y-1">
                      {msg.data.assets?.map((a: any, idx: number) => (
                        <div key={idx} className="flex items-center justify-between">
                          <span className="text-slate-300">{a.name}</span>
                          <span className="text-cyan-300">{a.risk_score?.toFixed(1)}</span>
                        </div>
                      ))}
                      {msg.data.recommendations?.map((r: string, idx: number) => (
                        <div key={idx} className="text-yellow-300">• {r}</div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {huntgptLoading && (
              <div className="flex justify-start">
                <div className="bg-slate-700 text-slate-100 px-4 py-3 rounded-2xl rounded-tl-none flex items-center gap-2">
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Input area */}
          <div className="p-4 border-t border-slate-700">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleSend(); }}
                placeholder="Ask CyberTwin Copilot..."
                className="flex-1 bg-slate-700 text-slate-100 placeholder-slate-400 px-4 py-2 rounded-xl border border-slate-600 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
              />
              <button
                onClick={() => handleSend()}
                disabled={huntgptLoading}
                className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-white transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
