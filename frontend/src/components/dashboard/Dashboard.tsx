"use client";
import { useQuery } from "@tanstack/react-query";
import { getSummary, getNettingWindows, getParticipants } from "@/lib/api";
import { KpiCard } from "./KpiCard";
import { TimeSeriesLineChart } from "@/components/charts/TimeSeriesLineChart";
import { HorizontalBarChart } from "@/components/charts/HorizontalBarChart";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatCurrency } from "@/lib/format";


export function Dashboard() {
  const {
    data: summary,
    isLoading: summaryLoading,
    error: summaryError,
  } = useQuery({ queryKey: ["summary"], queryFn: getSummary });

  const {
    data: windows,
    isLoading: windowsLoading,
    error: windowsError,
  } = useQuery({ queryKey: ["netting-windows"], queryFn: getNettingWindows });

  const {
    data: participants,
    isLoading: participantsLoading,
    error: participantsError,
  } = useQuery({ queryKey: ["participants"], queryFn: getParticipants });

  const isLoading = summaryLoading || windowsLoading || participantsLoading;
  const hasError = summaryError || windowsError || participantsError;

  if (isLoading) {
    return (
      <div className="p-8 space-y-6">
        <Skeleton className="h-8 w-1/3" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (hasError) {
    return (
      <div className="p-8">
        <ErrorMessage message="Failed to load dashboard data. Please try again." />
      </div>
    );
  }

  if (!summary || !windows || !participants) {
    return (
      <div className="p-8">
        <EmptyState message="No data available yet. Trigger a simulation first." />
      </div>
    );
  }

  // Prepare time series data from windows
  // For each window, total settled = sum of settled attempt amounts
  const timeSeriesData = windows.map((w) => {
    const settled = w.settlement_attempts
      .filter((a) => a.status === "settled")
      .reduce((sum, a) => sum + Number(a.amount), 0);
    const failed = w.settlement_attempts
      .filter((a) => a.status === "failed")
      .reduce((sum, a) => sum + Number(a.amount), 0);
    const gross = Number(w.gross_volume);
    const liquiditySaved = Number(w.liquidity_saved);
    const failureRate = failed > 0 || settled > 0 ? failed / (settled + failed) : 0;
    return {
      label: new Date(w.end_time).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit"
      }),
      grossVolume: gross,
      settledVolume: settled,
      liquiditySaved,
      failureRate
    };
  });

  const grossVsSettledSeries = [
    {
      name: "Gross Volume",
      color: "#94a3b8",
      data: timeSeriesData.map((d) => ({ label: d.label, value: d.grossVolume }))
    },
    {
      name: "Settled Volume",
      color: "#4f46e5",
      data: timeSeriesData.map((d) => ({ label: d.label, value: d.settledVolume }))
    }
  ];

  const liquiditySavedSeries = [
    {
      name: "Liquidity Saved",
      color: "#10b981",
      data: timeSeriesData.map((d) => ({ label: d.label, value: d.liquiditySaved }))
    }
  ];

  const failureRateSeries = [
    {
      name: "Failure Rate",
      color: "#ef4444",
      data: timeSeriesData.map((d) => ({ label: d.label, value: d.failureRate }))
    }
  ];

  const participantBalances = participants.map((p) => ({
    label: p.participant,
    value: Number(p.balance),
    color: Number(p.balance) >= 0 ? "#10b981" : "#ef4444",
  }));

  return (
    <main className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard label="Total Windows" value={String(summary.total_windows)} />
        <KpiCard label="Gross Volume" value={formatCurrency(summary.gross_volume)} />
        <KpiCard label="Net Volume" value={formatCurrency(summary.net_volume)} />
        <KpiCard label="Liquidity Saved" value={formatCurrency(summary.liquidity_saved)} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h2 className="mb-4 text-lg font-medium">Gross vs Settled Volume</h2>
          <TimeSeriesLineChart series={grossVsSettledSeries} />
        </Card>
        <Card>
          <h2 className="mb-4 text-lg font-medium">Liquidity Saved per Window</h2>
          <TimeSeriesLineChart series={liquiditySavedSeries} />
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h2 className="mb-4 text-lg font-medium">Failure Rate per Window</h2>
          <TimeSeriesLineChart series={failureRateSeries} />
        </Card>
        <Card>
          <h2 className="mb-4 text-lg font-medium">Final Participant Balances</h2>
          <HorizontalBarChart data={participantBalances} />
        </Card>
      </div>
    </main>
  );
}