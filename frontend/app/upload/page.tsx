"use client";
import { useEffect, useState } from "react";
import { api, getErrorMessage } from "@/lib/api";
import ErrorBanner from "@/components/ErrorBanner";

type Doc = { id: number; filename: string; subject: string; created_at: string };

export default function UploadPage() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [subject, setSubject] = useState("General");
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  async function loadDocs() {
    try {
      const res = await api.get("/documents/");
      setDocs(res.data);
      setLoadError(null);
    } catch (err) {
      setLoadError(getErrorMessage(err));
    }
  }

  useEffect(() => { loadDocs(); }, []);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return;
    setError(null);
    setStatus("Uploading & processing PDF...");
    const form = new FormData();
    form.append("file", file);
    form.append("subject", subject);
    try {
      await api.post("/documents/upload", form, { headers: { "Content-Type": "multipart/form-data" } });
      setStatus("Done.");
      setFile(null);
      loadDocs();
    } catch (err) {
      setError(getErrorMessage(err));
      setStatus("");
    }
  }

  return (
    <div>
      <h1 className="text-xl font-bold mb-4">Upload study material</h1>
      <form onSubmit={handleUpload} className="flex flex-col gap-3 max-w-md mb-8">
        <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <input className="bg-gray-900 border border-gray-700 rounded px-3 py-2"
          placeholder="Subject (e.g. Java, DBMS)" value={subject} onChange={(e) => setSubject(e.target.value)} />
        <button className="bg-amber-500 text-black hover:bg-amber-400 rounded px-3 py-2 font-medium" type="submit" disabled={!file}>
          Upload PDF
        </button>
        <ErrorBanner message={error} />
        {status && <p className="text-sm text-gray-400">{status}</p>}
      </form>

      <h2 className="text-lg font-semibold mb-2">Your documents</h2>
      <ErrorBanner message={loadError} />
      <ul className="flex flex-col gap-2">
        {docs.map((d) => (
          <li key={d.id} className="border border-gray-800 rounded px-3 py-2 flex justify-between">
            <span>{d.filename} <span className="text-gray-500">({d.subject})</span></span>
            <span className="text-gray-500 text-xs">id: {d.id}</span>
          </li>
        ))}
        {docs.length === 0 && !loadError && <p className="text-gray-500">No documents yet.</p>}
      </ul>
    </div>
  );
}
