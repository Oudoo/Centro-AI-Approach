"use client";

/**
 * Aura (by Centro) — Interactive request card.
 *
 * Rendered when the backend emits status:"action_card". Shows a friendly title
 * and an interactive form; the request is only filed when the user submits
 * (signed reply sent back over the socket by the parent). No raw API payload or
 * risk messaging is shown — this assistant only files safe, reviewable requests.
 */
import { CheckCircle2, ClipboardList, XCircle } from "lucide-react";
import { useState } from "react";
import type { ActionCardData } from "@/lib/types";

export function ActionCard({
  card,
  resolved,
  onConfirm,
  onCancel,
}: {
  card: ActionCardData;
  resolved?: "confirmed" | "cancelled";
  onConfirm: (formData?: Record<string, any>) => void;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<Record<string, any>>({});

  return (
    <div className="my-3 w-full animate-fade-up overflow-hidden rounded-2xl border border-centro-prussian/20 bg-white shadow-card">
      {/* Header */}
      <div className="flex items-center gap-2 bg-centro-prussian px-4 py-3 text-white">
        <ClipboardList size={18} />
        <span className="text-sm font-semibold tracking-wide">
          {card.target_system}
        </span>
      </div>

      <div className="space-y-4 p-4">
        <p className="text-sm text-centro-onyx/80">{card.summary}</p>

        {card.form_fields && card.form_fields.length > 0 ? (
          <div className="space-y-3 rounded-xl border border-centro-mist bg-gray-50/50 p-4">
            {card.form_fields.map((field) => (
              <div key={field.name}>
                <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-centro-accent">
                  {field.label} {field.required && <span className="text-red-500">*</span>}
                </label>
                {field.type === "textarea" ? (
                  <textarea
                    required={field.required}
                    value={formData[field.name] || ""}
                    onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
                    className="w-full rounded-lg border border-centro-mist bg-white px-3 py-2 text-sm text-centro-onyx outline-none focus:border-centro-prussian"
                    rows={3}
                  />
                ) : (
                  <input
                    type={field.type}
                    required={field.required}
                    value={formData[field.name] || ""}
                    onChange={(e) => setFormData({ ...formData, [field.name]: e.target.value })}
                    className="w-full rounded-lg border border-centro-mist bg-white px-3 py-2 text-sm text-centro-onyx outline-none focus:border-centro-prussian"
                  />
                )}
              </div>
            ))}
          </div>
        ) : null}

        {/* Actions */}
        {resolved ? (
          <div
            className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium ${
              resolved === "confirmed"
                ? "bg-emerald-50 text-emerald-700"
                : "bg-gray-100 text-gray-600"
            }`}
          >
            {resolved === "confirmed" ? (
              <CheckCircle2 size={16} />
            ) : (
              <XCircle size={16} />
            )}
            {resolved === "confirmed" ? "Request submitted" : "Request cancelled"}
          </div>
        ) : (
          <div className="flex gap-3">
            <button
              onClick={() => onConfirm(formData)}
              className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-centro-prussian px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-centro-prussian-700"
            >
              <CheckCircle2 size={16} /> Submit Request
            </button>
            <button
              onClick={onCancel}
              className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-centro-mist bg-white px-4 py-2.5 text-sm font-semibold text-centro-onyx transition hover:bg-centro-mist"
            >
              <XCircle size={16} /> Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
