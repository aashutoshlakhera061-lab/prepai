"use client";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { api, getErrorMessage } from "@/lib/api";
import ErrorBanner from "@/components/ErrorBanner";

type Msg = { role: "user" | "assistant"; content: string };

export default function ChatPage() {
  const [documentId, setDocumentId] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    if (!input.trim()) return;
    if (!documentId) {
      setError("Enter a Document ID first — check the Upload page for its id.");
      return;
    }
    setError(null);
    const userMsg: Msg = { role: "user", content: input };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    try {
      const res = await api.post("/chat/", {
        document_id: Number(documentId),
        message: userMsg.content,
        history: nextMessages,
      });
      setMessages([...nextMessages, { role: "assistant", content: res.data.reply }]);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Study Assistant</h1>
      <input className="bg-gray-900 border border-gray-700 rounded px-3 py-2 mb-4 w-full max-w-xs"
        placeholder="Document ID" value={documentId} onChange={(e) => setDocumentId(e.target.value)} />

      <ErrorBanner message={error} />

      <div className="flex flex-col gap-3 mb-4 max-w-2xl">
        {messages.map((m, i) => (
          <div key={i} className={`rounded-lg p-3 ${m.role === "user" ? "bg-indigo-900 self-end" : "bg-gray-900"}`}>
            {m.role === "assistant" ? (
              <div className="prose prose-invert prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                  {m.content}
                </ReactMarkdown>
              </div>
            ) : (
              m.content
            )}
          </div>
        ))}
        {loading && <p className="text-gray-500">Thinking...</p>}
      </div>

      <div className="flex gap-2 max-w-2xl">
        <input className="bg-gray-900 border border-gray-700 rounded px-3 py-2 flex-1"
          placeholder="What should I study today?" value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()} />
        <button className="bg-indigo-600 rounded px-3 py-2 disabled:opacity-50" onClick={send} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}
