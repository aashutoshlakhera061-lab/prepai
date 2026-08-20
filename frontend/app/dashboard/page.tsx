"use client";
import { useEffect, useState } from "react";
import { api, getErrorMessage } from "@/lib/api";
import ErrorBanner from "@/components/ErrorBanner";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";

type Dashboard = {
  interview_readiness: number;
  topic_scores: Record<string, number>;
  mock_tests_taken: number;
  flashcards_reviewed: number;
  top_priority_topic: string | null;
  accuracy_trend: number[];
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
      <h1 className="text-xl font-bold mb-6">Your Dashboard</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Stat label="Interview Readiness" value={`${data.interview_readiness}%`} />
        <Stat label="Mock Tests Taken" value={data.mock_tests_taken} />
        <Stat label="Flashcards Reviewed" value={data.flashcards_reviewed} />
        <Stat label="Priority Topic" value={data.top_priority_topic || "—"} highlight />
      </div>

      {topicData.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-2">Topic scores</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={topicData}>
              <XAxis dataKey="topic" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip />
              <Bar dataKey="score" fill="#6366f1" />
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
              <Line type="monotone" dataKey="score" stroke="#22c55e" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {data.mock_tests_taken === 0 && (
        <p className="text-gray-500 mt-6">Take a mock test to start seeing your progress here.</p>
      )}
    </div>
  );
}

function Stat({ label, value, highlight }: { label: string; value: string | number; highlight?: boolean }) {
  return (
    <div className={`border rounded-lg p-4 ${highlight ? "border-red-500" : "border-gray-800"}`}>
      <p className="text-gray-500 text-xs uppercase">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
