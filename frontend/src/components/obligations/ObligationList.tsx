"use client";
import { Obligation } from "@/lib/types";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { StatusBadge } from "./StatusBadge";
import { formatCurrency } from "@/lib/format";


interface ObligationListProps {
  data: Obligation[];
  isLoading: boolean;
  isError: boolean;
  error: unknown;
}

export function ObligationList({
  data,
  isLoading,
  isError,
  error
}: ObligationListProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full bg-slate-800" />
        ))}
      </div>
    );
  }

  if (isError) {
    return <ErrorMessage message={(error as Error).message} />;
  }

  if (data.length === 0) {
    return <EmptyState message="No obligations found. Create one to get started." />;
  }

  return (
    <div className="overflow-x-auto rounded-sm border border-slate-900">
      <table className="min-w-full divide-y divide-slate-900 text-sm">
        <thead className="bg-slate">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-slate-400">tx_id</th>
            <th className="px-4 py-3 text-left font-medium text-slate-400">Payer</th>
            <th className="px-4 py-3 text-left font-medium text-slate-400">Payee</th>
            <th className="px-4 py-3 text-right font-medium text-slate-400">Amount</th>
            <th className="px-4 py-3 text-left font-medium text-slate-400">Currency</th>
            <th className="px-4 py-3 text-left font-medium text-slate-400">Timestamp</th>
            <th className="px-4 py-3 text-left font-medium text-slate-400">Status</th>
            <th className="px-4 py-3 text-left font-medium text-slate-400">Window</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-900 bg-black">
          {data.map((obl) => (
            <tr key={obl.tx_id} className="hover:bg-slate-800/40 transition-colors">
              <td className="px-4 py-3 font-mono text-xs text-slate-400">
                {obl.tx_id.slice(0, 8)}...
              </td>
              <td className="px-4 py-3 font-semibold text-slate-200">{obl.payer}</td>
              <td className="px-4 py-3 font-semibold text-slate-200">{obl.payee}</td>
              <td className="px-4 py-3 text-right font-mono tabular-nums text-slate-100">
                {formatCurrency(obl.amount)}
              </td>
              <td className="px-4 py-3">
                <span className="rounded border border-slate-700 px-2 py-0.5 text-xs font-medium text-slate-300">
                  {obl.currency}
                </span>
              </td>
              <td className="px-4 py-3 font-mono text-xs text-slate-400">
                {new Date(obl.timestamp).toLocaleString()}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={obl.status} />
              </td>
              <td className="px-4 py-3">
                {obl.netting_window ? (
                  <a
                    href={`/netting-windows/${obl.netting_window}`}
                    className="font-mono text-indigo-400 hover:underline"
                  >
                    {obl.netting_window}
                  </a>
                ) : (
                  <span className="text-slate-600">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}