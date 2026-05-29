/** Aura (by Centro) — thin REST client for the admin/document API. */

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TOKEN_KEY = "aura.token";

export function getToken(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(TOKEN_KEY) || "";
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(TOKEN_KEY);
  }
}

function authHeaders(): HeadersInit {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export interface DocSummary {
  doc_id: string;
  source: string;
  department: string;
  account_scope: string;
  min_role_required: string;
  uploaded_by: string;
  chunks: number;
}

/** DEV: mint a signed token with chosen RBAC claims. */
export async function devLogin(
  role: string,
  account_scope: string,
  department = "general"
): Promise<string> {
  const body = new FormData();
  body.set("role", role);
  body.set("account_scope", account_scope);
  body.set("department", department);
  const res = await fetch(`${API_URL}/admin/dev-token`, { method: "POST", body });
  if (!res.ok) throw new Error(`dev-token failed (${res.status})`);
  const data = await res.json();
  setToken(data.token);
  return data.token;
}

export async function listDocuments(): Promise<DocSummary[]> {
  const res = await fetch(`${API_URL}/admin/documents`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`list failed (${res.status})`);
  return (await res.json()).documents;
}

export async function uploadDocument(
  file: File,
  department: string,
  account_scope: string,
  min_role_required: string
): Promise<void> {
  const body = new FormData();
  body.set("file", file);
  body.set("department", department);
  body.set("account_scope", account_scope);
  body.set("min_role_required", min_role_required);
  const res = await fetch(`${API_URL}/admin/documents`, {
    method: "POST",
    headers: authHeaders(),
    body,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `upload failed (${res.status})`);
  }
}

export async function deleteDocument(docId: string): Promise<void> {
  const res = await fetch(`${API_URL}/admin/documents/${docId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error(`delete failed (${res.status})`);
}

export async function fetchStats(): Promise<{ total_chunks: number; documents: number }> {
  const res = await fetch(`${API_URL}/admin/stats`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`stats failed (${res.status})`);
  return res.json();
}

export interface EmployeeRequest {
  id: number;
  created_at: string;
  request_type: string;
  target_system: string;
  employee_id: string;
  employee_name: string;
  account_scope: string;
  department: string;
  details: string;
  status: string;
  notified_email: string;
}

export async function listRequests(): Promise<EmployeeRequest[]> {
  const res = await fetch(`${API_URL}/admin/requests`, { headers: authHeaders() });
  if (!res.ok) throw new Error(`requests failed (${res.status})`);
  return (await res.json()).requests;
}

/** CSV download link (token passed as query param so a plain <a> works). */
export function requestsExportUrl(): string {
  return `${API_URL}/admin/requests/export.csv?token=${encodeURIComponent(getToken())}`;
}
