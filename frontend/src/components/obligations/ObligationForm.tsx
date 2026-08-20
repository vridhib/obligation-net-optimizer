"use client";
import { useState } from "react";
import { createObligation, bulkUploadObligations } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import { InputField } from "../ui/InputField";


type Tab = "single" | "bulk";

export function ObligationForm({ 
  onClose, onSuccess 
}: { 
  onClose: () => void, 
  onSuccess: () => void 
}) {
  const [tab, setTab] = useState<Tab>("single");
  const [formData, setFormData] = useState({
    payer: "",
    payee: "",
    amount: "",
    currency: "USD",
    timestamp: new Date().toISOString().slice(0, 16)
  });
  const [file, setFile] = useState<File | null>(null);
  const [json, setJson] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSingleSubmit(e: React.SubmitEvent) {
    e.preventDefault();
    setLoading(true);
    await createObligation({
      payer: formData.payer,
      payee: formData.payee,
      amount: formData.amount,
      currency: formData.currency,
      timestamp: new Date(formData.timestamp).toISOString()
    });
    setLoading(false);
    onSuccess();
  }

  async function handleBulkSubmit(e: React.SubmitEvent) {
    e.preventDefault();
    setLoading(true);
    await bulkUploadObligations(file || undefined, json || undefined);
    setLoading(false);
    onSuccess();
  }
  
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/60 backdrop-blur-sm">
      <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 p-6 shadow-2xl overflow-y-auto">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-100">New Obligation</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            ✕
          </button>
        </div>

        <div className="mt-4 flex gap-2 border-b border-slate-800">
          {(["single", "bulk"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={cn(
                "pb-2 text-sm font-medium capitalize",
                tab === t
                  ? "text-indigo-400 border-b-2 border-indigo-400"
                  : "text-slate-500 hover:text-slate-300"
              )}
            >
              {t}
            </button>
          ))}
        </div>

        {tab === "single" ? (
          <form onSubmit={handleSingleSubmit} className="mt-6 space-y-4">
            <InputField
              label="Payer"
              value={formData.payer}
              onChange={(v) => setFormData({ ...formData, payer: v })}
            />
            <InputField
              label="Payee"
              value={formData.payee}
              onChange={(v) => setFormData({ ...formData, payee: v })}
            />
            <InputField
              label="Amount"
              value={formData.amount}
              onChange={(v) => setFormData({ ...formData, amount: v })}
              type="number"
            />
            <InputField
              label="Currency"
              value={formData.currency}
              onChange={(v) => setFormData({ ...formData, currency: v })}
            />
            <InputField
              label="Timestamp"
              value={formData.timestamp}
              onChange={(v) => setFormData({ ...formData, timestamp: v })}
              type="datetime-local"
            />
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "Submitting..." : "Create Obligation"}
            </Button>
          </form>
        ) : (
          <form onSubmit={handleBulkSubmit} className="mt-6 space-y-4">
            <label className="block">
              <span className="text-sm text-slate-400">CSV File</span>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="mt-1 w-full rounded-md bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-200"
              />
            </label>
            <label className="block">
              <span className="text-sm text-slate-400">JSON</span>
              <textarea
                value={json}
                onChange={(e) => setJson(e.target.value)}
                rows={5}
                className="mt-1 w-full rounded-md bg-slate-800 border border-slate-700 px-3 py-2 font-mono text-sm text-slate-200"
                placeholder='[{"payer":"A","payee":"B","amount":"100.00","timestamp":"2026-08-11T08:00:00Z"}]'
              />
            </label>
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? "Uploading..." : "Upload Bulk"}
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
