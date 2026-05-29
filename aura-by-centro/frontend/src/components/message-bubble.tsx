"use client";

import { Sparkles, User2 } from "lucide-react";
import type { ChatMessage } from "@/lib/types";

/** A single chat bubble, branded per Centro palette. */
export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="mx-auto my-2 max-w-xl animate-fade-up rounded-lg border border-amber-300/40 bg-amber-50 px-4 py-2 text-center text-sm text-amber-800">
        {message.text}
      </div>
    );
  }

  return (
    <div
      className={`flex w-full animate-fade-up items-start gap-3 ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      <div
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
          isUser ? "bg-centro-onyx text-white" : "bg-centro-prussian text-white"
        }`}
      >
        {isUser ? <User2 size={18} /> : <Sparkles size={18} />}
      </div>
      <div
        className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-[15px] leading-relaxed shadow-sm ${
          isUser
            ? "rounded-tr-sm bg-centro-onyx text-white"
            : "rounded-tl-sm border border-centro-mist bg-white text-centro-onyx"
        }`}
      >
        {message.text}
        {message.streaming && (
          <span className="ml-0.5 inline-block h-4 w-[2px] animate-blink bg-centro-prussian align-middle" />
        )}
      </div>
    </div>
  );
}
