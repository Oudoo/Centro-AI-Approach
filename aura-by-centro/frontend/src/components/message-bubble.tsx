"use client";

import type { ChatMessage } from "@/lib/types";
import ReactMarkdown from "react-markdown";
import { Logo } from "@/components/logo";

/** A single chat bubble, branded per Centro palette. */
export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="my-2 animate-fade-up rounded-lg border border-amber-300/40 bg-amber-50 px-4 py-2 text-sm text-amber-800">
        {message.text}
      </div>
    );
  }

  return (
    <div
      className={`flex w-full animate-fade-up items-start gap-3 ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      {!isUser && (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-centro-prussian text-white">
          <Logo className="h-5 w-5" />
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-[15px] leading-relaxed shadow-sm ${
          isUser
            ? "rounded-tr-sm bg-centro-onyx text-white"
            : "rounded-tl-sm border border-centro-mist bg-white text-centro-onyx"
        }`}
      >
        {message.isTyping ? (
          <div className="flex h-6 items-center gap-1.5 px-1">
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-centro-prussian/60 [animation-delay:-0.3s]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-centro-prussian/60 [animation-delay:-0.15s]" />
            <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-centro-prussian/60" />
          </div>
        ) : (
          <>
            <div className="prose prose-sm max-w-none break-words dark:prose-invert">
              <ReactMarkdown>{message.text}</ReactMarkdown>
              {message.streaming && (
                <span className="ml-0.5 inline-block h-4 w-[2px] animate-blink bg-centro-prussian align-middle" />
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
