"use client";
import { useQuery } from "@tanstack/react-query";
import { getParticipants } from "@/lib/api";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { HorizontalBarChart } from "@/components/charts/HorizontalBarChart";
import { ParticipantsTable } from "./ParticipantsTable";


export function ParticipantsClient() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["participants"],
    queryFn: getParticipants
  });

  if (isLoading) {
    return (
      <main className="min-h-screen bg-slate-950 p-8 space-y-6">
        <Skeleton className="h-10 w-1/3" />
        <Skeleton className="h-96 w-full" />
      </main>
    );
  }

  if (isError) {
    return (
      <main className="min-h-screen bg-slate-950 p-8">
        <ErrorMessage message={(error as Error).message || "Failed to load participants."} />
      </main>
    );
  }

  const participants = data ?? [];
  if (participants.length === 0) {
    return (
      <main className="min-h-screen bg-slate-950 p-8">
        <EmptyState message="No participants found. Trigger a simulation first." />
      </main>
    );
  }

  const barData = participants.map((p) => ({
    label: p.participant,
    value: Number(p.balance),
    color: Number(p.balance) >= 0 ? "#10b981" : "#ef4444"
  }));

  return (
    <main className="min-h-screen bg-slate-950 p-8 space-y-6">
      <PageHeader
        title="Participants"
        description="Current liquidity balances across all participants"
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-slate-950 border-slate-800 p-6">
          <h2 className="mb-4 text-lg font-medium font-semibold text-slate-200">Balances</h2>
          <HorizontalBarChart data={barData} />
        </Card>

        <Card className="bg-slate-950 border-slate-800 p-6">
          <h2 className="mb-4 text-lg font-semibold font-medium text-slate-200">Details</h2>
          <ParticipantsTable participants={participants} />
        </Card>
      </div>
    </main>
  );
}