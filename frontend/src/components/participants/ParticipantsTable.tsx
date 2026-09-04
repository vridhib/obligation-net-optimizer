"use client";
import type { ParticipantBalance } from "@/lib/types";
import { formatCurrency } from "@/lib/format";


interface ParticipantsTableProps {
  participants: ParticipantBalance[];
}

export function ParticipantsTable({ participants }: ParticipantsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-800 text-sm">
        <thead>
          <tr>
            <th className="px-4 py-3 text-left font-medium text-slate-400">Participant</th>
            <th className="px-4 py-3 text-right font-medium text-slate-400">Balance</th>
            <th className="px-4 py-3 text-left font-medium text-slate-400">Last Updated</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {participants.map((p) => (
            <tr key={p.participant} className="hover:bg-slate-800/40 transition-colors">
              <td className="px-4 py-3 font-medium text-slate-200">{p.participant}</td>
              <td
                className={`px-4 py-3 text-right font-mono tabular-nums ${
                  Number(p.balance) >= 0 ? "text-emerald-400" : "text-rose-400"
                }`}
              >
                {formatCurrency(p.balance)}
              </td>
              <td className="px-4 py-3 font-mono text-xs text-slate-400">
                {new Date(p.last_updated).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}