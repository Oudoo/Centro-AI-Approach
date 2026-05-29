"use client";

/**
 * Aura (by Centro) — primary chat surface.
 * Wires the WebSocket hook to the message list, action cards, and composer.
 */
import { useEffect, useRef, useState } from "react";
import { Send, Wifi, WifiOff, Menu, UserCog } from "lucide-react";
import { useWebSocket } from "@/hooks/useWebSocket";
import { BRAND } from "@/lib/brand";
import { mintIdentity } from "@/lib/api";
import { ActionCard } from "@/components/action-card";
import { MessageBubble } from "@/components/message-bubble";
import { Logo } from "@/components/logo";

const SUGGESTIONS = [
  "How do I submit my resignation?",
  "Show me the holiday calendar",
  "Request a casual leave for tomorrow",
  "I want to request an annual leave",
  "Can I update my break timing?",
];

// A1 — demo identities so HR can show RBAC sandboxing live in one window.
const DEMO_IDENTITIES = [
  { label: "Global Agent", role: "agent", scope: "global" },
  { label: "Coastline Agent", role: "agent", scope: "coastline" },
  { label: "Coastline Manager", role: "manager", scope: "coastline" },
  { label: "Trueblue Agent", role: "agent", scope: "trueblue" },
  { label: "Trueblue Manager", role: "manager", scope: "trueblue" },
];

export function ChatInterface({
  sessionId,
  token: tokenProp,
  onMenuClick,
  onFirstMessage,
}: {
  sessionId: string;
  token?: string;
  onMenuClick?: () => void;
  onFirstMessage?: (text: string) => void;
}) {
  // When no token is supplied (main chat), let the user pick a demo identity.
  const usingDemoIdentity = !tokenProp;
  const [identityIdx, setIdentityIdx] = useState(0);
  const [identityToken, setIdentityToken] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (!usingDemoIdentity) return;
    let cancelled = false;
    const id = DEMO_IDENTITIES[identityIdx];
    mintIdentity(id.role, id.scope)
      .then((t) => !cancelled && setIdentityToken(t))
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [identityIdx, usingDemoIdentity]);

  const token = tokenProp ?? identityToken;
  const { messages, connState, sendQuery, respondToAction } = useWebSocket(
    sessionId,
    token
  );
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const submit = (text: string) => {
    const value = text.trim();
    if (!value) return;
    if (messages.length === 0 && onFirstMessage) {
      onFirstMessage(value);
    }
    sendQuery(value);
    setInput("");
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <header className="flex items-center gap-3 border-b border-centro-mist bg-white px-6 py-4">
        {onMenuClick && (
          <button 
            onClick={onMenuClick}
            className="mr-1 flex items-center justify-center rounded-lg p-1.5 text-centro-onyx/70 transition hover:bg-centro-mist"
          >
            <Menu size={20} />
          </button>
        )}
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-centro-prussian text-white shadow-card">
          <Logo className="h-6 w-6" />
        </div>
        <div>
          <h1 className="text-lg font-bold leading-tight text-centro-onyx">
            {BRAND.fullName}
          </h1>
          <p className="text-xs text-centro-onyx/60">{BRAND.tagline}</p>
        </div>
        {usingDemoIdentity && (
          <label className="ml-auto flex items-center gap-1.5 rounded-lg border border-centro-mist bg-centro-mist/30 px-2 py-1 text-xs text-centro-onyx/70">
            <UserCog size={14} className="text-centro-prussian" />
            <span className="hidden sm:inline">Acting as</span>
            <select
              value={identityIdx}
              onChange={(e) => setIdentityIdx(Number(e.target.value))}
              className="bg-transparent font-medium text-centro-onyx outline-none"
              title="Demo identity (drives RBAC sandboxing)"
            >
              {DEMO_IDENTITIES.map((id, i) => (
                <option key={id.label} value={i}>{id.label}</option>
              ))}
            </select>
          </label>
        )}
        <div
          className={`${usingDemoIdentity ? "" : "ml-auto"} flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
            connState === "open"
              ? "bg-emerald-50 text-emerald-700"
              : "bg-gray-100 text-gray-500"
          }`}
        >
          {connState === "open" ? <Wifi size={13} /> : <WifiOff size={13} />}
          {connState === "open" ? "Connected" : "Reconnecting…"}
        </div>
      </header>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-6 py-6">
        {messages.length === 0 && (
          <div className="mx-auto mt-10 max-w-lg text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-centro-prussian text-white shadow-card">
              <Logo className="h-8 w-8" />
            </div>
            <h2 className="text-xl font-bold text-centro-onyx">Hi, I'm Aura — your Co-Pilot by Centro. Let's make your day easier.</h2>
            <p className="mt-2 text-sm text-centro-onyx/60">
              Ask about HR, leave, schedules, or submit a request.
            </p>
            <div className="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => submit(s)}
                  className="rounded-xl border border-centro-mist bg-white px-4 py-3 text-left text-sm text-centro-onyx transition hover:border-centro-prussian/40 hover:shadow-card"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) =>
          m.card ? (
            <ActionCard
              key={m.id}
              card={m.card}
              resolved={m.cardResolved}
              onConfirm={(formData) => respondToAction(m.card!.action_id, true, formData)}
              onCancel={() => respondToAction(m.card!.action_id, false)}
            />
          ) : (
            <MessageBubble key={m.id} message={m} />
          )
        )}
      </div>

      {/* Composer */}
      <div className="border-t border-centro-mist bg-white px-6 py-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit(input);
          }}
          className="flex items-center gap-3"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Message Aura…"
            className="flex-1 rounded-xl border border-centro-mist bg-centro-mist/40 px-4 py-3 text-[15px] text-centro-onyx outline-none transition focus:border-centro-prussian focus:bg-white"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className="flex h-12 w-12 items-center justify-center rounded-xl bg-centro-prussian text-white transition hover:bg-centro-prussian-700 disabled:opacity-40"
          >
            <Send size={18} />
          </button>
        </form>
        <p className="mt-2 text-center text-[11px] text-centro-onyx/40">
          Aura can make mistakes. Mutating actions always require your confirmation.
        </p>
      </div>
    </div>
  );
}
