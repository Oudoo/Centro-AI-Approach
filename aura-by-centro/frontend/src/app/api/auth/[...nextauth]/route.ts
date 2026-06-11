/**
 * Aura (by Centro) — Local session handler.
 *
 * Minimal credential exchange endpoint that mints a session payload carrying the
 * RBAC context (account_scope, role, department) used by the backend to sandbox
 * vector retrieval. Swap this for NextAuth providers in production; the shape of
 * the issued session must stay aligned with backend/auth.py UserContext.
 */
import { NextRequest, NextResponse } from "next/server";

interface SessionRequest {
  username?: string;
  account_scope?: "coastline" | "trueblue" | "global";
  role?: "agent" | "team_lead" | "manager" | "admin";
  department?: string;
}

export async function POST(req: NextRequest) {
  const body = (await req.json().catch(() => ({}))) as SessionRequest;

  // Dev-only: trust the posted scope. Replace with real IdP verification.
  const session = {
    user_id: body.username || "dev-user",
    display_name: body.username || "Centro User",
    account_scope: body.account_scope || "global",
    role: body.role || "agent",
    department: body.department || "general",
    issued_at: new Date().toISOString(),
  };

  return NextResponse.json({ session });
}

export async function GET() {
  return NextResponse.json({
    provider: "aura-local",
    note: "POST credentials to receive a dev session. Use a signed JWT in production.",
  });
}
