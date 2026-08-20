import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_URL });

// Attaches the JWT (stored in localStorage after login) to every request.
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("prepai_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function login(email: string, password: string) {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  const res = await api.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  localStorage.setItem("prepai_token", res.data.access_token);
  return res.data;
}

export async function register(email: string, password: string, name: string) {
  const res = await api.post("/auth/register", { email, password, name });
  return res.data;
}

/**
 * Turns any Axios/API failure into a clean, user-readable string.
 * Use this in every catch block instead of letting errors surface as
 * "Unhandled Runtime Error" overlays or silent failures.
 */
export function getErrorMessage(err: unknown): string {
  if (typeof err === "object" && err !== null) {
    const anyErr = err as any;
    if (anyErr.code === "ERR_NETWORK" || anyErr.message === "Network Error") {
      return "Can't reach the server. Make sure the backend is running (uvicorn app.main:app --reload) and try again.";
    }
    const detail = anyErr?.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
    if (anyErr?.response?.status) return `Request failed (status ${anyErr.response.status}). Please try again.`;
  }
  return "Something went wrong. Please try again.";
}
