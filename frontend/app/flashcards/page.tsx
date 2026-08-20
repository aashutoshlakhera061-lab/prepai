"use client";
import { useState } from "react";
import { api, getErrorMessage } from "@/lib/api";
import ErrorBanner from "@/components/ErrorBanner";

type Card = { id: number; question: string; answer: string; difficulty: string; retention: number };

export default function FlashcardsPage() {
  const [documentId, setDocumentId] = useState("");
  const [cards, setCards] = useState<Card[]>([]);
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function generate() {
    if (!documentId) {
      setError("Enter a Document ID first — check the Upload page for its id.");
      return;
    }
    setError(null);
    setBusy(true);
    setStatus("Generating flashcards... this can take up to 30 seconds.");
    try {
      await api.post("/flashcards/generate", { document_id: Number(documentId), count: 15 });
      setStatus("Done. Loading due cards...");
      await loadDue();
    } catch (err) {
      setError(getErrorMessage(err));
      setStatus("");
    } finally {
      setBusy(false);
    }
  }

  async function loadDue() {
    if (!documentId) {
      setError("Enter a Document ID first.");
      return;
    }
    setError(null);
    try {
      const res = await api.get("/flashcards/due", { params: { document_id: Number(documentId) } });
      setCards(res.data);
      setIndex(0);
      setRevealed(false);
      setStatus("");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  async function review(gotItRight: boolean) {
    const card = cards[index];
    try {
      await api.post("/flashcards/review", { flashcard_id: card.id, got_it_right: gotItRight });
      setRevealed(false);
      setIndex((i) => i + 1);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  const current = cards[index];

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Flashcards</h1>
      <div className="flex gap-2 mb-4 max-w-md">
        <input className="bg-gray-900 border border-gray-700 rounded px-3 py-2 flex-1"
          placeholder="Document ID (see Upload page)" value={documentId} onChange={(e) => setDocumentId(e.target.value)} />
        <button className="bg-indigo-600 rounded px-3 py-2 disabled:opacity-50" onClick={generate} disabled={busy}>
          {busy ? "Working..." : "Generate"}
        </button>
        <button className="bg-gray-700 rounded px-3 py-2" onClick={loadDue}>Load due</button>
      </div>

      <ErrorBanner message={error} />
      {status && <p className="text-gray-400 mb-4">{status}</p>}

      {current ? (
        <div className="border border-gray-800 rounded-lg p-6 max-w-lg">
          <p className="text-xs text-gray-500 mb-2">
            Card {index + 1} of {cards.length} · {current.difficulty} · retention {(current.retention * 100).toFixed(0)}%
          </p>
          <p className="text-lg mb-4">{current.question}</p>
          {revealed ? (
            <>
              <p className="text-green-400 mb-4">{current.answer}</p>
              <div className="flex gap-3">
                <button className="bg-red-700 rounded px-3 py-2" onClick={() => review(false)}>Got it wrong</button>
                <button className="bg-green-700 rounded px-3 py-2" onClick={() => review(true)}>Got it right</button>
              </div>
            </>
          ) : (
            <button className="bg-indigo-600 rounded px-3 py-2" onClick={() => setRevealed(true)}>Reveal answer</button>
          )}
        </div>
      ) : (
        !error && <p className="text-gray-500">No cards loaded. Generate or load due cards for a document.</p>
      )}
    </div>
  );
}
