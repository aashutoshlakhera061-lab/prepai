"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, register } from "@/lib/api";

export default function HomePage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      if (mode === "register") {
        await register(email, password, name);
      }
      await login(email, password);
      router.push("/upload");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Something went wrong");
    }
  }

  return (
    <div className="max-w-sm mx-auto mt-16">
      <h1 className="text-2xl font-bold mb-2">PrepAI</h1>
      <p className="text-gray-400 mb-6">
        Upload → Understand → Practice → Evaluate → Improve.
      </p>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        {mode === "register" && (
          <input className="bg-gray-900 border border-gray-700 rounded px-3 py-2"
            placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} />
        )}
        <input className="bg-gray-900 border border-gray-700 rounded px-3 py-2"
          placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
               <div className="relative">
          <input className="bg-gray-900 border border-gray-700 rounded px-3 py-2 w-full pr-16"
            placeholder="Password" type={showPassword ? "text" : "password"} value={password}
            onChange={(e) => setPassword(e.target.value)} required />
          <button type="button" onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-400 hover:text-gray-200">
            {showPassword ? "Hide" : "Show"}
          </button>
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <button className="bg-amber-500 text-black hover:bg-amber-400 rounded px-3 py-2 font-medium" type="submit">
          {mode === "login" ? "Log in" : "Create account"}
        </button>
      </form>
      <button className="text-sm text-gray-400 mt-3 underline"
        onClick={() => setMode(mode === "login" ? "register" : "login")}>
        {mode === "login" ? "Need an account? Register" : "Already have an account? Log in"}
      </button>
    </div>
  );
}
