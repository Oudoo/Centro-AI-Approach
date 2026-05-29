"use client";

/**
 * Aura (by Centro) — Admin / Knowledge Base dashboard.
 *
 * Lets a department head (role >= manager) upload, scope, and remove the
 * documents Aura retrieves from. Branded per the Centro Brand Book.
 */
import { useCallback, useEffect, useState } from "react";
import {
  FileText,
  LogIn,
  RefreshCw,
  ShieldCheck,
  Trash2,
  UploadCloud,
} from "lucide-react";
import { BRAND } from "@/lib/brand";
import {
  type DocSummary,
  deleteDocument,
  devLogin,
  fetchStats,
  getToken,
  listDocuments,
  uploadDocument,
} from "@/lib/api";

const SCOPES = ["global", "coastline", "trueblue"];
const ROLES = ["agent", "team_lead", "manager", "admin"];

export default function AdminPage() {
  const [authed, setAuthed] = useState(false);
  const [docs, setDocs] = useState<DocSummary[]>([]);
  const [stats, setStats] = useState({ total_chunks: 0, documents: 0 });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // Upload form state
  const [file, setFile] = useState<File | null>(null);
  const [department, setDepartment] = useState("hr");
  const [scope, setScope] = useState("global");
  const [minRole, setMinRole] = useState("agent");

  const refresh = useCallback(async () => {
    try {
      setDocs(await listDocuments());
      setStats(await fetchStats());
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    if (getToken()) {
      setAuthed(true);
      refresh();
    }
  }, [refresh]);

  const login = async (role: string, account_scope: string) => {
    setBusy(true);
    try {
      await devLogin(role, account_scope);
      setAuthed(true);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    try {
      await uploadDocument(file, department, scope, minRole);
      setFile(null);
      (document.getElementById("file-input") as HTMLInputElement).value = "";
      await refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async (docId: string) => {
    setBusy(true);
    try {
      await deleteDocument(docId);
      await refresh();
    } finally {
      setBusy(false);
    }
  };

  if (!authed) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6">
        <div className="w-full max-w-md rounded-3xl border border-centro-mist bg-white p-8 shadow-card">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-centro-prussian text-white">
              <ShieldCheck size={22} />
            </div>
            <div>
              <h1 className="text-lg font-bold text-centro-onyx">
                {BRAND.fullName} — Admin
              </h1>
              <p className="text-xs text-centro-onyx/60">Knowledge base management</p>
            </div>
          </div>
          <p className="mb-4 text-sm text-centro-onyx/70">
            Dev sign-in. Choose a role/scope to mint a session token. In
            production this is replaced by your SSO provider.
          </p>
          <div className="space-y-2">
            <button
              disabled={busy}
              onClick={() => login("manager", "global")}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-centro-prussian px-4 py-3 text-sm font-semibold text-white hover:bg-centro-prussian-700 disabled:opacity-50"
            >
              <LogIn size={16} /> Sign in as Global Manager
            </button>
            <button
              disabled={busy}
              onClick={() => login("manager", "coastline")}
              className="w-full rounded-lg border border-centro-mist px-4 py-3 text-sm font-medium text-centro-onyx hover:bg-centro-mist"
            >
              Sign in as Coastline Manager
            </button>
          </div>
          {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl p-6">
      {/* Header */}
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-centro-prussian text-white">
          <ShieldCheck size={22} />
        </div>
        <div>
          <h1 className="text-xl font-bold text-centro-onyx">
            {BRAND.fullName} — Knowledge Base
          </h1>
          <p className="text-xs text-centro-onyx/60">
            {stats.documents} documents · {stats.total_chunks} chunks indexed
          </p>
        </div>
        <button
          onClick={refresh}
          className="ml-auto flex items-center gap-1.5 rounded-lg border border-centro-mist px-3 py-2 text-sm text-centro-onyx hover:bg-centro-mist"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Upload card */}
      <form
        onSubmit={submit}
        className="mb-8 rounded-2xl border border-centro-mist bg-white p-6 shadow-card"
      >
        <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-centro-accent">
          <UploadCloud size={16} /> Upload a document
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm">
            <span className="mb-1 block font-medium text-centro-onyx">File (.md/.txt/.csv/.json)</span>
            <input
              id="file-input"
              type="file"
              accept=".md,.markdown,.txt,.csv,.json"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="w-full rounded-lg border border-centro-mist px-3 py-2 text-sm"
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium text-centro-onyx">Department</span>
            <input
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full rounded-lg border border-centro-mist px-3 py-2 text-sm"
            />
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium text-centro-onyx">Account scope</span>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value)}
              className="w-full rounded-lg border border-centro-mist px-3 py-2 text-sm"
            >
              {SCOPES.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </label>
          <label className="text-sm">
            <span className="mb-1 block font-medium text-centro-onyx">Min role required</span>
            <select
              value={minRole}
              onChange={(e) => setMinRole(e.target.value)}
              className="w-full rounded-lg border border-centro-mist px-3 py-2 text-sm"
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </label>
        </div>
        <button
          type="submit"
          disabled={!file || busy}
          className="mt-4 flex items-center gap-2 rounded-lg bg-centro-prussian px-5 py-2.5 text-sm font-semibold text-white hover:bg-centro-prussian-700 disabled:opacity-50"
        >
          <UploadCloud size={16} /> {busy ? "Working…" : "Ingest document"}
        </button>
      </form>

      {/* Document table */}
      <div className="overflow-hidden rounded-2xl border border-centro-mist bg-white shadow-card">
        <table className="w-full text-left text-sm">
          <thead className="bg-centro-mist/50 text-xs uppercase tracking-wide text-centro-onyx/60">
            <tr>
              <th className="px-4 py-3">Document</th>
              <th className="px-4 py-3">Department</th>
              <th className="px-4 py-3">Scope</th>
              <th className="px-4 py-3">Min role</th>
              <th className="px-4 py-3">Chunks</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {docs.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-centro-onyx/50">
                  No documents yet. Upload one above.
                </td>
              </tr>
            )}
            {docs.map((d) => (
              <tr key={d.doc_id} className="border-t border-centro-mist">
                <td className="px-4 py-3 font-medium text-centro-onyx">
                  <span className="flex items-center gap-2">
                    <FileText size={15} className="text-centro-accent" />
                    {d.source}
                  </span>
                </td>
                <td className="px-4 py-3 text-centro-onyx/70">{d.department}</td>
                <td className="px-4 py-3">
                  <span className="rounded-full bg-centro-prussian/10 px-2 py-0.5 text-xs font-medium text-centro-prussian">
                    {d.account_scope}
                  </span>
                </td>
                <td className="px-4 py-3 text-centro-onyx/70">{d.min_role_required}</td>
                <td className="px-4 py-3 text-centro-onyx/70">{d.chunks}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => remove(d.doc_id)}
                    className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                  >
                    <Trash2 size={13} /> Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
