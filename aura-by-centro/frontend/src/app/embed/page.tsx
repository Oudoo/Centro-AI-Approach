"use client";

/**
 * Aura (by Centro) — Embeddable widget for the Zoho People Web Tab.
 *
 * Renders the chat with no page chrome so it sits cleanly inside an iframe.
 * Zoho passes the signed user token + session id as query params, e.g.:
 *   /embed?token=<JWT>&session=<empId>
 * The token's RBAC claims drive vector sandboxing exactly like the main app.
 */
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ChatInterface } from "@/components/chat-interface";

function EmbedInner() {
  const params = useSearchParams();
  const token = params.get("token") || undefined;
  const session = params.get("session") || "embed-session";

  return (
    <main className="h-screen w-screen bg-white">
      <ChatInterface sessionId={session} token={token} />
    </main>
  );
}

export default function EmbedPage() {
  return (
    <Suspense fallback={null}>
      <EmbedInner />
    </Suspense>
  );
}
