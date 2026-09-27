"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, getErrorMessage } from "@/lib/api";
import ErrorBanner from "@/components/ErrorBanner";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";
import { Flame, Target, TrendingUp, FileText, ArrowUpRight } from "lucide-react";

type RecentDocument = { id: number; filename: string; subject: string; created_at: string };
type RecentAttempt = { id: number; subject: string; score_pct: number; created_at: string };

type Dashboard = {
  interview_readiness: number;
  topic_scores: Record<string, number>;
  materials_count: number;
  mock_tests_taken: number;
  flashcards_total: number;
  flashcards_reviewed: number;
  top_priority_topic: string | null;
  accuracy_trend: number[];
  recent_documents: RecentDocument[];
  recent_attempts: RecentAttempt[];
};

export default function DashboardPage() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/dashboard/")
      .then((res) => setData(res.data))
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  const topicData = Object.entries(data.topic_scores).map(([topic, score]) => ({ topic, score }));
  const trendData = data.accuracy_trend.map((v, i) => ({ attempt: i + 1, score: v }));

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-1">Study overview</h1>
          <p className="text-gray-400">Everything you need for your next interview, test or exam.</p>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <StatCard
          icon={<Flame size={16} className="text-amber-400" />}
          label="MATERIALS"
          value={data.materials_count}
          caption="PDFs and notes in your library"
        />
        <StatCard
          icon={<Target size={16} className="text-amber-400" />}
          label="ACCURACY"
          value={data.mock_tests_taken > 0 ? `${data.interview_readiness}%` : "—"}
          caption={data.mock_tests_taken > 0 ? "Overall readiness" : "Take a mock test"}
        />
        <StatCard
          icon={<TrendingUp size={16} className="text-amber-400" />}
          label="MOCK TESTS"
          value={data.mock_tests_taken}
          caption="Attempts completed"
        />
        <StatCard
          icon={<FileText size={16} className="text-amber-400" />}
          label="FLASHCARDS"
          value={data.flashcards_total}
          caption="Cards across decks"
        />
      </div>

      {/* Recent materials */}
      <div className="bg-gray-950 border border-gray-800 rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Recent materials</h2>
          <Link href="/upload" className="text-amber-400 hover:text-amber-300 text-sm font-medium">
            Manage
          </Link>
        </div>
        {data.recent_documents.length === 0 ? (
          <div className="border border-dashed border-gray-700 rounded-lg py-8 text-center text-gray-500">
            No study material yet — upload a PDF to get started.
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {data.recent_documents.map((doc) => (
              <div key={doc.id} className="flex justify-between items-center border border-gray-800 rounded-lg px-4 py-3">
                <span>{doc.filename} <span className="text-gray-500 text-sm">({doc.subject})</span></span>
                <span className="text-gray-500 text-xs">id: {doc.id}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Jump back in */}
      <div className="bg-gray-950 border border-gray-800 rounded-xl p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4">Jump back in</h2>
        <div className="flex flex-col gap-3">
          <QuickAction href="/mocktest" label="Generate a mock test" />
          <QuickAction href="/flashcards" label="Review flashcards" />
          <QuickAction href="/chat" label="Ask the study assistant" />
        </div>
      </div>

      {/* Recent attempts */}
      <div className="bg-gray-950 border border-gray-800 rounded-xl p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Recent attempts</h2>
        {data.recent_attempts.length === 0 ? (
          <p className="text-gray-500">Your mock test history will appear here.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {data.recent_attempts.map((a) => (
              <div key={a.id} className="flex justify-between items-center border border-gray-800 rounded-lg px-4 py-3">
                <span>{a.subject}</span>
                <span className="text-amber-400 font-medium">{a.score_pct}%</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Charts */}
      {topicData.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-2">Topic scores</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={topicData}>
              <XAxis dataKey="topic" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip />
              <Bar dataKey="score" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {trendData.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-2">Accuracy trend</h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={trendData}>
              <XAxis dataKey="attempt" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip />
              <Line type="monotone" dataKey="score" stroke="#f59e0b" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function StatCard({
  icon, label, value, caption,
}: { icon: React.ReactNode; label: string; value: string | number; caption: string }) {
  return (
    <div className="bg-gray-950 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center gap-2 text-gray-400 text-xs font-semibold tracking-wide mb-3">
        {icon}
        {label}
      </div>
      <p className="text-3xl font-bold mb-1">{value}</p>
      <p className="text-gray-500 text-sm">{caption}</p>
    </div>
  );
}

function QuickAction({ href, label }: { href: string; label: string }) {
  return (
    <Link
      href={href}
      className="flex items-center justify-between bg-gray-900 hover:bg-gray-800 border border-gray-800 rounded-lg px-4 py-3 transition-colors"
    >
      <span className="font-medium">{label}</span>
      <ArrowUpRight size={18} className="text-amber-400" />
    </Link>
  );
}
