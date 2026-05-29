"use client";

/**
 * Aura (by Centro) — Global chat dashboard with Recent Conversations.
 */
import { useEffect, useState } from "react";
import { ChatInterface } from "@/components/chat-interface";
import { Plus, MessageSquare, Pin, Edit2, Trash2, MoreHorizontal } from "lucide-react";

type SessionMeta = { id: string; title: string; timestamp: number; isPinned?: boolean };

export default function Home() {
  const [sessions, setSessions] = useState<SessionMeta[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);

  useEffect(() => {
    const handleGlobalClick = () => setMenuOpenId(null);
    if (menuOpenId) {
      window.addEventListener("click", handleGlobalClick);
    }
    return () => window.removeEventListener("click", handleGlobalClick);
  }, [menuOpenId]);

  const startNewSession = (updateState = true) => {
    const id = "sess-" + Math.random().toString(36).slice(2, 10);
    const newSession = { id, title: "New Conversation", timestamp: Date.now() };
    if (updateState) {
      setSessions((prev) => [newSession, ...prev]);
      setCurrentSessionId(id);
      if (window.innerWidth < 768) setSidebarOpen(false);
    }
    return newSession;
  };

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = window.localStorage.getItem("aura.sessions");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          const lastId = window.localStorage.getItem("aura.last_session_id");
          if (parsed && parsed.length > 0) {
            setSessions(parsed);
            if (lastId && parsed.some((s: SessionMeta) => s.id === lastId)) {
              setCurrentSessionId(lastId);
            } else {
              setCurrentSessionId(parsed[0].id);
            }
          } else {
            const newS = startNewSession(false);
            setSessions([newS]);
            setCurrentSessionId(newS.id);
          }
        } catch (e) {
          const newS = startNewSession(false);
          setSessions([newS]);
          setCurrentSessionId(newS.id);
        }
      } else {
        const newS = startNewSession(false);
        setSessions([newS]);
        setCurrentSessionId(newS.id);
      }
      setIsLoaded(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (isLoaded && typeof window !== "undefined") {
      window.localStorage.setItem("aura.sessions", JSON.stringify(sessions));
      if (currentSessionId) {
        window.localStorage.setItem("aura.last_session_id", currentSessionId);
      }
    }
  }, [sessions, currentSessionId, isLoaded]);

  if (!isLoaded || !currentSessionId) {
    return <div className="h-screen bg-gray-50/50" />;
  }

  const handleFirstMessage = async (id: string, text: string) => {
    try {
      const res = await fetch("http://localhost:8000/title", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (res.ok) {
        const data = await res.json();
        setSessions((prev) =>
          prev.map((s) => (s.id === id ? { ...s, title: data.title } : s))
        );
      }
    } catch (e) {
      console.error(e);
    }
  };

  const togglePin = (id: string) => {
    setSessions((prev) =>
      prev.map((s) => (s.id === id ? { ...s, isPinned: !s.isPinned } : s))
    );
  };

  const renameSession = (id: string, newTitle: string) => {
    setSessions((prev) =>
      prev.map((s) => (s.id === id ? { ...s, title: newTitle || "Untitled" } : s))
    );
  };

  const deleteSession = (id: string) => {
    setSessions((prev) => {
      const next = prev.filter((s) => s.id !== id);
      if (next.length === 0) {
        const newS = startNewSession(false);
        next.push(newS);
        setCurrentSessionId(newS.id);
      } else if (currentSessionId === id) {
        setCurrentSessionId(next[0].id);
      }
      return next;
    });
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(`aura.chat.${id}`);
    }
  };

  const sortedSessions = [...sessions].sort((a, b) => {
    if (a.isPinned && !b.isPinned) return -1;
    if (!a.isPinned && b.isPinned) return 1;
    return b.timestamp - a.timestamp;
  });

  const sidebarContent = (
    <>
      <div className="border-b border-centro-mist p-4">
        <button
          onClick={() => startNewSession()}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-centro-prussian px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-centro-prussian-700"
        >
          <Plus size={16} /> New Chat
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        <p className="mb-2 px-1 text-xs font-semibold uppercase tracking-wider text-centro-onyx/50">
          Recent
        </p>
        {sortedSessions.map((s) => (
          <div key={s.id} className="group relative flex items-center">
            <button
              onClick={() => {
                setCurrentSessionId(s.id);
                if (window.innerWidth < 768) setSidebarOpen(false);
              }}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition ${
                currentSessionId === s.id
                  ? "bg-centro-mist/60 font-medium text-centro-onyx"
                  : "text-centro-onyx/70 hover:bg-centro-mist/40"
              }`}
            >
              {s.isPinned ? (
                <Pin size={16} className="shrink-0 text-emerald-600" />
              ) : (
                <MessageSquare size={16} className="shrink-0 opacity-60" />
              )}
              {editingId === s.id ? (
                <input
                  autoFocus
                  defaultValue={s.title}
                  onBlur={(e) => {
                    renameSession(s.id, e.target.value);
                    setEditingId(null);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      renameSession(s.id, e.currentTarget.value);
                      setEditingId(null);
                    }
                  }}
                  className="w-full bg-transparent outline-none"
                />
              ) : (
                <span className="truncate">{s.title}</span>
              )}
            </button>
            <div className={`absolute right-2 ${menuOpenId === s.id ? "block" : "hidden group-hover:block"}`}>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setMenuOpenId(menuOpenId === s.id ? null : s.id);
                }}
                className="rounded p-1 text-centro-onyx/50 transition-colors hover:bg-black/5 hover:text-centro-onyx"
              >
                <MoreHorizontal size={16} />
              </button>
              
              {menuOpenId === s.id && (
                <div className="absolute right-0 top-full z-50 mt-1 w-32 overflow-hidden rounded-lg border border-centro-mist bg-white py-1 shadow-lg">
                  <button
                    onClick={(e) => { e.stopPropagation(); setEditingId(s.id); setMenuOpenId(null); }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-centro-onyx transition-colors hover:bg-centro-mist/50"
                  >
                    <Edit2 size={14} /> Rename
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); togglePin(s.id); setMenuOpenId(null); }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-centro-onyx transition-colors hover:bg-centro-mist/50"
                  >
                    <Pin size={14} className={s.isPinned ? "fill-emerald-600 text-emerald-600" : ""} /> {s.isPinned ? "Unpin" : "Pin"}
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteSession(s.id); setMenuOpenId(null); }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 transition-colors hover:bg-red-50"
                  >
                    <Trash2 size={14} /> Delete
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </>
  );

  return (
    <main className="mx-auto flex h-screen max-w-5xl flex-col p-3 sm:p-6">
      <div className="relative flex flex-1 overflow-hidden rounded-3xl border border-centro-mist bg-white shadow-card">
        {/* Desktop Sidebar (Collapsible) */}
        <div
          className={`hidden shrink-0 border-r border-centro-mist bg-gray-50 transition-all duration-300 ease-in-out md:block ${
            sidebarOpen ? "w-64" : "w-0 border-r-0"
          } overflow-hidden`}
        >
          <div className="flex h-full w-64 flex-col">{sidebarContent}</div>
        </div>

        {/* Mobile Sidebar (Absolute Overlay) */}
        <div
          className={`absolute inset-y-0 left-0 z-20 w-64 transform border-r border-centro-mist bg-gray-50 transition-transform duration-300 ease-in-out md:hidden ${
            sidebarOpen ? "translate-x-0 shadow-xl" : "-translate-x-full"
          }`}
        >
          <div className="flex h-full w-full flex-col">{sidebarContent}</div>
        </div>

        {/* Overlay for mobile when sidebar is open */}
        {sidebarOpen && (
          <div
            className="absolute inset-0 z-10 bg-black/10 transition-opacity md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Chat Area */}
        <div className="flex flex-1 flex-col overflow-hidden bg-white">
          <ChatInterface
            sessionId={currentSessionId}
            onMenuClick={() => setSidebarOpen((prev) => !prev)}
            onFirstMessage={(text) => handleFirstMessage(currentSessionId, text)}
          />
        </div>
      </div>
    </main>
  );
}
