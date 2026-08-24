"use client";
import { useQuery } from "@tanstack/react-query";
import { getNettingWindow } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { HorizontalBarChart } from "@/components/charts/HorizontalBarChart";
import { formatCurrency } from "@/lib/format";


export function WindowDetail({ windowId }: { windowId: number }) {
  const { data: window, isLoading, isError, error } = useQuery({
    queryKey: ["netting-window", windowId],
    queryFn: () => getNettingWindow(windowId),
  });

  if (isLoading) {
    return <Skeleton className="h-96 w-full bg-slate-800" />;
  }

  if (isError || !window) {
    return <ErrorMessage message={(error as Error)?.message || "Failed to load window."} />;
  }

  const positionsData = window.net_positions.map((p) => ({
    label: p.participant,
    value: Number(p.net_amount),
    color: Number(p.net_amount) >= 0 ? "#10b981" : "#ef4444",
  }));

  return (
    <article className="space-y-6">
      {/* Header Cards */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="border-slate-800 p-4">
          <p className="text-xs text-slate-500">Gross Volume</p>
          <p className="text-xl font-semibold text-slate-100 mt-1">
            {formatCurrency(window.gross_volume)}
          </p>
        </Card>
        <Card className="border-slate-800 p-4">
          <p className="text-xs text-slate-500">Liquidity Saved</p>
          <p className="text-xl font-semibold text-emerald-400 mt-1">
            {formatCurrency(window.liquidity_saved)}
          </p>
        </Card>
      </div>

      {/* Net Positions Chart */}
      <Card className="border-slate-800 p-6">
        <h3 className="text-sm font-medium text-slate-300 mb-4">Net Positions</h3>
        {positionsData.length > 0 ? (
          <HorizontalBarChart data={positionsData} />
        ) : (
          <p className="text-sm text-slate-500">No positions recorded.</p>
        )}
      </Card>

      {/* Settlement Attempts Table */}
      <Card className="border-slate-800 p-6">
        <h3 className="text-sm font-medium text-slate-300 mb-4">Settlement Attempts</h3>
        {window.settlement_attempts.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-500 border-b border-slate-800">
                  <th className="py-2 pr-4">Payer</th>
                  <th className="py-2 pr-4">Payee</th>
                  <th className="py-2 pr-4 text-right">Amount</th>
                  <th className="py-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {window.settlement_attempts.map((attempt, idx) => (
                  <tr key={idx} className="text-slate-200">
                    <td className="py-2 pr-4 font-medium">{attempt.payer}</td>
                    <td className="py-2 pr-4 font-medium">{attempt.payee}</td>
                    <td className="py-2 pr-4 text-right font-mono tabular-nums">
                      {formatCurrency(attempt.amount)}
                    </td>
                    <td className="py-2">
                      <span
                        className={attempt.status === "settled" ? "text-emerald-400" : "text-rose-400"}
                      >
                        {attempt.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-500">No settlement attempts.</p>
        )}
      </Card>
    </article>
  );
}