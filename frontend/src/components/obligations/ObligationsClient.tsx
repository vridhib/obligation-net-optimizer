"use client";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getObligations } from "@/lib/api";
import { ObligationList } from "./ObligationList";
import { ObligationForm } from "./ObligationForm";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "../ui/PageHeader";


export function ObligationsClient() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["obligations", search, page],
    queryFn: () => getObligations({ page, search })
  });

  function handleSuccess() {
    queryClient.invalidateQueries({ queryKey: ["obligations"] });
    setIsFormOpen(false);
  }

  const totalPages = Math.ceil((data?.count ?? 0) / 20);

  return (
    <main className="min-h-screen bg-black p-8 space-y-6">
      <PageHeader
        title="Obligations"
        description="Manage individual payment instructions"
        action={
          <Button variant="primary" onClick={() => setIsFormOpen(true)}>
            New Obligation
          </Button>
        }
      />

      <Card className="bg-slate border-slate-800 p-4">
        <input
          type="search"
          placeholder="Search payer, payee, or tx_id..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="w-full rounded-md bg-slate-950 border border-slate-700 px-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </Card>

      <ObligationList
        data={data?.results ?? []}
        isLoading={isLoading}
        isError={isError}
        error={error}
      />

      {data && data.count > 0 && (
        <div className="flex items-center justify-between border-t border-slate-800 pt-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={!data.previous}
            className="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-transparent"
          >
            Previous
          </button>
          <span className="text-sm text-slate-400">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={!data.next}
            className="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:hover:bg-transparent"
          >
            Next
          </button>
        </div>
      )}

      {isFormOpen && (
        <ObligationForm
          onClose={() => setIsFormOpen(false)}
          onSuccess={handleSuccess}
        />
      )}
    </main>
  );
}