"use client";
import { NettingWindow } from "@/lib/types";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { cn } from "@/lib/utils";
import { formatCurrency } from "@/lib/format";


interface WindowListProps {
  data: NettingWindow[];
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export function WindowList({
  data,
  isLoading,
  isError,
  error,
  selectedId,
  onSelect
}: WindowListProps) {
  if (isLoading) {
    return (
      <div className="p-4 space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full bg-slate-800" />
        ))}
      </div>
    );
  }

  if (isError) {
    return <ErrorMessage message={(error as Error).message} />;
  }

  if (data.length === 0) {
    return <EmptyState message="No netting windows yet." />;
  }

  return (
    <ul className="divide-y divide-slate-900">
      {data.map((window) => (
        <li key={window.window_id}>
          <button
            onClick={() => onSelect(window.window_id)}
            className={cn(
              "w-full text-left p-4 transition-colors hover:bg-slate-800/40",
              selectedId === window.window_id && "bg-slate-800/60"
            )}
          >
            <div className="flex items-center justify-between">
              <span className="font-mono text-sm text-slate-200">
                #{window.window_id}
              </span>
              <span className="text-xs text-slate-400">
                {new Date(window.end_time).toLocaleString([], {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-400">
              <span>Gross Obligation Count: {window.gross_obligation_count}</span>
              <span>Net Obligation Count: {window.net_obligation_count}</span>
              <span>Net Volume: {formatCurrency(window.net_volume)}</span>
              <span className="text-emerald-400">
                Liquidity Saved: {formatCurrency(window.liquidity_saved)}
              </span>
            </div>
          </button>
        </li>
      ))}
    </ul>
  );
}