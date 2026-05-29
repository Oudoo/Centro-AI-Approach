"use client";

/**
 * Aura (by Centro) — FEATURE 3: Interactive Disambiguation Action Card.
 *
 * Rendered when the backend emits status:"action_card". Visually isolated,
 * shows Target System / API Payload / Risk Assessment, and exposes Confirm &
 * Cancel. The write only executes when the user confirms (signed reply sent
 * back over the socket by the parent).
 */
import { AlertTriangle, CheckCircle2, ShieldAlert, XCircle } from "lucide-react";
import { useState } from "react";
import type { ActionCardData } from "@/lib/types";

const RISK_STYLES: Record<string, string> = {
  low: "border-emerald-300 bg-emerald-50 text-emerald-700",
  medium: "border-amber-300 bg-amber-50 text-amber-700",
  high: "border-red-300 bg-red-50 text-red-700",
};

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
  const riskClass = RISK_STYLES[card.risk_level] ?? RISK_STYLES.medium;

  return (
    <div className="my-3 w-full animate-fade-up overflow-hidden rounded-2xl border-2 border-centro-prussian/30 bg-white shadow-card">
      {/* Header */}
      <div className="flex items-center gap-2 bg-centro-prussian px-4 py-3 text-white">
        <ShieldAlert size={18} />
        <span className="text-sm font-semibold uppercase tracking-wide">
          Confirmation Required
        </span>
        <span className="ml-auto rounded-full bg-white/15 px-2 py-0.5 text-xs">
          {card.intent}
        </span>
      </div>

      <div className="space-y-4 p-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-centro-accent">
            Target System
          </p>
          <p className="text-[15px] font-medium text-centro-onyx">
            {card.target_system}
          </p>
        </div>

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

        <div className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-sm ${riskClass}`}>
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <span>
            <strong className="uppercase">{card.risk_level} risk.</strong>{" "}
            {card.risk_assessment}
          </span>
        </div>

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
            {resolved === "confirmed" ? "Action confirmed" : "Action cancelled"}
          </div>
        ) : (
          <div className="flex gap-3">
            <button
              onClick={() => onConfirm(formData)}
              className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-centro-prussian px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-centro-prussian-700"
            >
              <CheckCircle2 size={16} /> Confirm Action
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
