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
import { useState } from "react";
import { Pagination } from "../ui/Pagination";
import { useRouter, useSearchParams } from "next/navigation";
import { SearchBar } from "../ui/SearchBar";


export function ParticipantsClient() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const committedSearch = searchParams.get("q") ?? "";
  const page = Number(searchParams.get("page") ?? "1");

  const [input, setInput] = useState(committedSearch);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["participants", committedSearch, page],
    queryFn: () => getParticipants({ page, search: committedSearch })
  });

  const submitSearch = () => {
    const params = new URLSearchParams();
    if (input) params.set("q", input);
    router.push(`/participants?${params.toString()}`);
  };

  const changePage = (newPage: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(newPage));
    router.push(`/participants?${params.toString()}`);
  };

  const participants = data?.results ?? [];
  const totalPages = Math.ceil((data?.count ?? 0) / 20);

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

      <SearchBar
        value={input}
        onChange={setInput}
        onSubmit={submitSearch}
        placeholder="Search participant... (press Enter)"
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

      {data && data.count > 0 && (
        <div className="flex justify-center border-t border-slate-800 pt-4">
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onPageChange={changePage}
          />
        </div>
      )}
    </main>
  );
}