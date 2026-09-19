"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { getAnomalies } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { useDismissedAnomalies } from "@/lib/useDismissedAnomalies";


export function AnomaliesClient() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["anomalies"],
    queryFn: getAnomalies
  });
  const { dismiss, isDismissed } = useDismissedAnomalies();

  if (isLoading) return <Skeleton className="h-96 w-full" />;
  if (isError) return <ErrorMessage message={(error as Error).message} />;

  const visible = (data?.anomalies ?? []).filter(
    (a) => !isDismissed(a.window_id, a.metric)
  );

  if (visible.length === 0) {
    return (
      <main className="min-h-screen bg-slate-950 p-8">
        <PageHeader title="Anomalies" description="Detected anomalies across netting windows" />
        <EmptyState message="No anomalies detected. All windows are nominal." />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 p-8 space-y-6">
      <PageHeader
        title="Anomalies"
        description={`${visible.length} anomal${visible.length === 1 ? "y" : "ies"} detected`}
      />

      <div className="space-y-3">
        {visible.map((a, i) => (
          <Card key={i} className="border-amber-500/30 bg-amber-500/5 p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
                <div>
                  <p className="text-sm font-medium text-slate-200">
                    {a.metric} scored{" "}
                    <span className="font-mono text-amber-400">
                      {a.score.toFixed(4)}σ
                    </span>{" "}
                    above normal
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    {a.method === "z_score" ? "Statistical" : "Multivariate"} ·{" "}
                    {new Date(a.window_end).toLocaleString()} ·{" "}
                    <Link
                      href={`/netting-windows?window=${a.window_id}`}
                      className="text-indigo-400 hover:underline"
                    >
                      View window #{a.window_id}
                    </Link>
                  </p>
                </div>
              </div>
              <button
                onClick={() => dismiss(a.window_id, a.metric)}
                className="text-xs text-slate-500 hover:text-slate-300"
              >
                Dismiss
              </button>
            </div>
          </Card>
        ))}
      </div>
    </main>
  );
}