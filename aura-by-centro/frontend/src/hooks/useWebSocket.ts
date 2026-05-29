"use client";

/**
 * Aura (by Centro) — useWebSocket
 *
 * Owns the live connection to the FastAPI backbone, parses the typed
 * SocketMessage contract, and projects it into a ChatMessage[] the UI renders:
 *   - "streaming"   -> append tokens to the active assistant bubble
 *   - "completed"   -> finalize the bubble
 *   - "action_card" -> attach a dual-confirmation card to a new bubble
 *   - "error"       -> surface an enterprise fallback notice (socket stays open)
 */
import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatMessage, SocketMessage } from "@/lib/types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";

function uid(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export type ConnState = "connecting" | "open" | "closed";

export function useWebSocket(sessionId: string, token?: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [connState, setConnState] = useState<ConnState>("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const activeAssistantId = useRef<string | null>(null);

  const connect = useCallback(() => {
    const params = new URLSearchParams({ session_id: sessionId });
    if (token) params.set("token", token);
    const ws = new WebSocket(`${WS_URL}?${params.toString()}`);
    wsRef.current = ws;
    setConnState("connecting");

    ws.onopen = () => setConnState("open");
    ws.onclose = () => {
      setConnState("closed");
      // Auto-reconnect with a short backoff so the session survives blips.
      setTimeout(() => connect(), 1500);
    };
    ws.onmessage = (event) => {
      let msg: SocketMessage;
      try {
        msg = JSON.parse(event.data) as SocketMessage;
      } catch {
        return;
      }
      handleMessage(msg);
    };
  }, [sessionId, token]);

  const handleMessage = useCallback((msg: SocketMessage) => {
    setMessages((prev) => {
      const next = [...prev];

      if (msg.status === "streaming") {
        const text = msg.payload.text ?? "";
        if (activeAssistantId.current) {
          const idx = next.findIndex((m) => m.id === activeAssistantId.current);
          if (idx >= 0) next[idx] = { ...next[idx], text: next[idx].text + text };
        } else {
          const id = uid();
          activeAssistantId.current = id;
          next.push({ id, role: "assistant", text, streaming: true });
        }
        return next;
      }

      if (msg.status === "completed") {
        if (activeAssistantId.current) {
          const idx = next.findIndex((m) => m.id === activeAssistantId.current);
          if (idx >= 0) next[idx] = { ...next[idx], streaming: false };
        }
        activeAssistantId.current = null;
        return next;
      }

      if (msg.status === "action_card" && msg.payload.card_data) {
        activeAssistantId.current = null;
        next.push({
          id: uid(),
          role: "assistant",
          text: "",
          card: msg.payload.card_data,
        });
        return next;
      }

      if (msg.status === "error") {
        activeAssistantId.current = null;
        next.push({
          id: uid(),
          role: "system",
          text: msg.payload.text ?? "An error occurred.",
        });
        return next;
      }

      return next;
    });
  }, []);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sendQuery = useCallback(
    (text: string) => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      setMessages((prev) => [...prev, { id: uid(), role: "user", text }]);
      ws.send(JSON.stringify({ type: "query", session_id: sessionId, text }));
    },
    [sessionId]
  );

  const respondToAction = useCallback(
    (actionId: string, confirmed: boolean, signature?: string) => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      ws.send(
        JSON.stringify({
          type: "action_response",
          session_id: sessionId,
          action_id: actionId,
          action_confirmed: confirmed,
          signature: signature ?? null,
        })
      );
      setMessages((prev) =>
        prev.map((m) =>
          m.card?.action_id === actionId
            ? { ...m, cardResolved: confirmed ? "confirmed" : "cancelled" }
            : m
        )
      );
    },
    [sessionId]
  );

  return { messages, connState, sendQuery, respondToAction };
}
