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
  const isInitializing = useRef(true);
  const prevSessionId = useRef(sessionId);

  useEffect(() => {
    isInitializing.current = true;
    if (typeof window !== "undefined") {
      try {
        const stored = window.localStorage.getItem(`aura.chat.${sessionId}`);
        if (stored) {
          setMessages(JSON.parse(stored));
        } else {
          setMessages([]);
        }
      } catch (e) {
        setMessages([]);
      }
    }
  }, [sessionId]);

  useEffect(() => {
    if (isInitializing.current) {
      isInitializing.current = false;
      return;
    }
    if (prevSessionId.current !== sessionId) {
      prevSessionId.current = sessionId;
      return;
    }
    if (typeof window !== "undefined") {
      window.localStorage.setItem(`aura.chat.${sessionId}`, JSON.stringify(messages));
    }
  }, [messages, sessionId]);

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
    if (msg.status === "streaming") {
      if (!activeAssistantId.current) {
        activeAssistantId.current = uid();
      }
      const currentId = activeAssistantId.current;
      
      setMessages((prev) => {
        const next = [...prev];
        const idx = next.findIndex((m) => m.id === currentId);
        if (idx >= 0) {
          next[idx] = { ...next[idx], text: next[idx].text + (msg.payload.text ?? ""), isTyping: false, streaming: true };
        } else {
          next.push({ id: currentId, role: "assistant", text: msg.payload.text ?? "", streaming: true, isTyping: false });
        }
        return next;
      });
    } else if (msg.status === "completed") {
      const currentId = activeAssistantId.current;
      if (currentId) {
        setMessages((prev) => {
          const next = [...prev];
          const idx = next.findIndex((m) => m.id === currentId);
          if (idx >= 0) next[idx] = { ...next[idx], streaming: false, isTyping: false };
          return next;
        });
        activeAssistantId.current = null;
      }
    } else if (msg.status === "action_card" && msg.payload.card_data) {
      const currentId = activeAssistantId.current;
      activeAssistantId.current = null;
      const cardData = msg.payload.card_data;
      setMessages((prev) => {
        const next = currentId ? prev.filter((m) => m.id !== currentId) : [...prev];
        next.push({ id: uid(), role: "assistant", text: "", card: cardData });
        return next;
      });
    } else if (msg.status === "error") {
      const currentId = activeAssistantId.current;
      activeAssistantId.current = null;
      const errorText = msg.payload.text ?? "An error occurred.";
      setMessages((prev) => {
        const next = currentId ? prev.filter((m) => m.id !== currentId) : [...prev];
        next.push({ id: uid(), role: "system", text: errorText });
        return next;
      });
    }
  }, []);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  const sendQuery = useCallback(
    (text: string) => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      
      const newAssistantId = uid();
      activeAssistantId.current = newAssistantId;
      
      setMessages((prev) => [
        ...prev, 
        { id: uid(), role: "user", text },
        { id: newAssistantId, role: "assistant", text: "", isTyping: true }
      ]);
      
      ws.send(JSON.stringify({ type: "query", session_id: sessionId, text }));
    },
    [sessionId]
  );

  const respondToAction = useCallback(
    (actionId: string, confirmed: boolean, formData?: Record<string, any>, signature?: string) => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      ws.send(
        JSON.stringify({
          type: "action_response",
          session_id: sessionId,
          action_id: actionId,
          action_confirmed: confirmed,
          form_data: formData ?? {},
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
