"use client";
import { useState } from "react";
import { X } from "lucide-react";
import type { UseMutationResult } from "@tanstack/react-query";
import { Button } from "@/components/ui/Button";


interface TriggerNettingDialogProps {
  onClose: () => void;
  mutation: UseMutationResult<{ task_id: string }, Error, File>;
}

export function TriggerNettingDialog({
  onClose,
  mutation,
}: TriggerNettingDialogProps) {
  const [file, setFile] = useState<File | null>(null);

  function handleSubmit(e: React.SubmitEvent) {
    e.preventDefault();
    if (file) {
      mutation.mutate(file);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-100">
            Trigger Netting
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <label className="block">
            <span className="text-sm text-slate-400">CSV File</span>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="mt-1 w-full rounded-md bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-200"
            />
          </label>

          {mutation.isError && (
            <p className="text-sm text-rose-400">{mutation.error?.message || "Failed to trigger netting."}</p>
          )}

          {mutation.isSuccess && (
            <p className="text-sm text-emerald-400"> Task ID: {mutation.data.task_id}</p>
          )}

          <Button
            type="submit"
            disabled={!file || mutation.isPending}
            className="w-full"
          >
            {mutation.isPending ? "Uploading..." : "Run Netting"}
          </Button>
        </form>
      </div>
    </div>
  );
}