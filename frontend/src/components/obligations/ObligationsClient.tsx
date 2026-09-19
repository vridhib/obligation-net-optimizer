"use client";
import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getObligations } from "@/lib/api";
import { ObligationList } from "./ObligationList";
import { ObligationForm } from "./ObligationForm";
import { Button } from "@/components/ui/Button";
import { PageHeader } from "../ui/PageHeader";
import { Pagination } from "../ui/Pagination";
import { useRouter, useSearchParams } from "next/navigation";
import { SearchBar } from "../ui/SearchBar";


export function ObligationsClient() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();

  const committedSearch = searchParams.get("q") ?? "";
  const page = Number(searchParams.get("page") ?? "1");

  const [input, setInput] = useState(committedSearch);
  const [isFormOpen, setIsFormOpen] = useState(false);

  useEffect(() => {
    setInput(committedSearch);
  }, [committedSearch]);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["obligations", committedSearch, page],
    queryFn: () => getObligations({ page, search: committedSearch })
  });

  const submitSearch = () => {
    const params = new URLSearchParams();
    if (input) params.set("q", input);
    router.push(`/obligations?${params.toString()}`);
  };

  const changePage = (newPage: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(newPage));
    router.push(`/obligations?${params.toString()}`);
  };

  function handleSuccess() {
    queryClient.invalidateQueries({ queryKey: ["obligations"] });
    setIsFormOpen(false);
  }

  const totalPages = Math.ceil((data?.count ?? 0) / 20);

  return (
    <main className="min-h-screen bg-slate-950 p-8 space-y-6">
      <PageHeader
        title="Obligations"
        description="Manage individual payment instructions"
        action={
          <Button variant="primary" onClick={() => setIsFormOpen(true)}>
            New Obligation
          </Button>
        }
      />

      {/* Search Bar */}
      <SearchBar
        value={input}
        onChange={setInput}
        onSubmit={submitSearch}
        placeholder="Search payer, payee, or tx_id... (press Enter)"
      />

      {/* Master List */}
      <ObligationList
        data={data?.results ?? []}
        isLoading={isLoading}
        isError={isError}
        error={error}
      />

      {/* Pagination */}
      {data && data.count > 0 && (
        <div className="flex justify-center border-t border-slate-800 pt-4">
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onPageChange={changePage}
          />
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