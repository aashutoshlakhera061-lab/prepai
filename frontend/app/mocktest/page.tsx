"use client";
import { useState } from "react";
import { api, getErrorMessage } from "@/lib/api";
import ErrorBanner from "@/components/ErrorBanner";

type Question = { question: string; options: string[]; correct_index: number; topic: string; source?: string };
type Test = { id: number; subject: string; difficulty: string; questions: Question[] };
type Result = { score_pct: number; topic_breakdown: Record<string, number>; mistakes_logged: number };

export default function MockTestPage() {
  const [documentId, setDocumentId] = useState("");
  const [difficulty, setDifficulty] = useState("medium");
  const [numQuestions, setNumQuestions] = useState(10);
  const [test, setTest] = useState<Test | null>(null);
  const [answers, setAnswers] = useState<number[]>([]);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    if (!documentId) {
      setError("Enter a Document ID first — check the Upload page for its id.");
      return;
    }
    setError(null);
    setLoading(true);
    setResult(null);
    try {
      const res = await api.post("/mocktest/generate", {
        document_id: Number(documentId), difficulty, num_questions: numQuestions,
      });
      setTest(res.data);
      setAnswers(new Array(res.data.questions.length).fill(-1));
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function selectAnswer(qIndex: number, optIndex: number) {
    const next = [...answers];
    next[qIndex] = optIndex;
    setAnswers(next);
  }

  async function submit() {
    if (!test) return;
    setError(null);
    try {
      const res = await api.post("/mocktest/submit", { mock_test_id: test.id, answers });
      setResult(res.data);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Mock Test</h1>
      <ErrorBanner message={error} />

      {!test && (
        <div className="flex flex-col gap-3 max-w-md">
          <input className="bg-gray-900 border border-gray-700 rounded px-3 py-2"
            placeholder="Document ID" value={documentId} onChange={(e) => setDocumentId(e.target.value)} />
          <select className="bg-gray-900 border border-gray-700 rounded px-3 py-2"
            value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
          <input type="number" className="bg-gray-900 border border-gray-700 rounded px-3 py-2"
            value={numQuestions} onChange={(e) => setNumQuestions(Number(e.target.value))} />
          <button className="bg-amber-500 text-black rounded px-3 py-2 disabled:opacity-50" onClick={generate} disabled={loading}>
            {loading ? "Generating..." : "Generate mock test"}
          </button>
        </div>
      )}

      {test && !result && (
        <div className="flex flex-col gap-6 mt-6">
          {test.questions.map((q, qi) => (
            <div key={qi} className="border border-gray-800 rounded-lg p-4">
              <p className="font-medium mb-2">{qi + 1}. {q.question} <span className="text-xs text-gray-500">({q.topic})</span></p>
              <div className="flex flex-col gap-1">
                {q.options.map((opt, oi) => (
                  <label key={oi} className="flex items-center gap-2 cursor-pointer">
                    <input type="radio" name={`q${qi}`} checked={answers[qi] === oi} onChange={() => selectAnswer(qi, oi)} />
                    {opt}
                  </label>
                ))}
              </div>
            </div>
          ))}
          <button className="bg-green-700 rounded px-3 py-2 w-fit" onClick={submit}>Submit test</button>
        </div>
      )}

      {result && (
        <div className="mt-6 border border-gray-800 rounded-lg p-6 max-w-md">
          <h2 className="text-lg font-bold mb-2">Score: {result.score_pct}%</h2>
          <p className="text-gray-400 mb-3">{result.mistakes_logged} mistake(s) logged to your Mistake Book.</p>
          {Object.entries(result.topic_breakdown).map(([topic, pct]) => (
            <p key={topic}>{topic}: {pct}%</p>
          ))}
        </div>
      )}
    </div>
  );
}
