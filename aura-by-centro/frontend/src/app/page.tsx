"use client";

/**
 * Aura (by Centro) — Global chat dashboard.
 * In production the session_id + auth token come from the auth handler; here we
 * generate a stable per-browser session for local development.
 */
import { useMemo } from "react";
import { ChatInterface } from "@/components/chat-interface";

function useSession(): string {
  return useMemo(() => {
    if (typeof window === "undefined") return "ssr-session";
    const KEY = "aura.session_id";
    let id = window.localStorage.getItem(KEY);
    if (!id) {
      id = "sess-" + Math.random().toString(36).slice(2, 10);
      window.localStorage.setItem(KEY, id);
    }
    return id;
  }, []);
}

export default function Home() {
  const sessionId = useSession();

  return (
    <main className="mx-auto flex h-screen max-w-3xl flex-col p-3 sm:p-6">
      <div className="flex flex-1 overflow-hidden rounded-3xl border border-centro-mist bg-white shadow-card">
        <ChatInterface sessionId={sessionId} />
      </div>
    </main>
  );
}
