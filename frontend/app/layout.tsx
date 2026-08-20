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
        <nav className="flex gap-6 px-6 py-4 border-b border-gray-800 items-center">
          <Link href="/" className="font-bold text-lg">PrepAI</Link>
          <Link href="/upload">Upload</Link>
          <Link href="/dashboard">Dashboard</Link>
          <Link href="/flashcards">Flashcards</Link>
          <Link href="/mocktest">Mock Test</Link>
          <Link href="/chat">Study Assistant</Link>
        </nav>
        <main className="max-w-5xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
