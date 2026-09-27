import "./globals.css";
import "katex/dist/katex.min.css";
import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "PrepAI",
  description: "Adaptive AI interview preparation",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav className="border-b border-gray-800 px-6 py-4">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-8">
              <Link href="/dashboard" className="font-bold text-lg">PrepAI</Link>
              <div className="flex gap-6 text-sm text-gray-300">
                <Link href="/dashboard" className="hover:text-white">Dashboard</Link>
                <Link href="/upload" className="hover:text-white">Materials</Link>
                <Link href="/mocktest" className="hover:text-white">Mock Tests</Link>
                <Link href="/flashcards" className="hover:text-white">Flashcards</Link>
                <Link href="/chat" className="hover:text-white">Study Assistant</Link>
              </div>
            </div>
            <Link
              href="/upload"
              className="bg-amber-500 hover:bg-amber-400 text-black font-semibold text-sm rounded-lg px-4 py-2 transition-colors"
            >
              Upload material
            </Link>
          </div>
        </nav>
        <main className="max-w-6xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
