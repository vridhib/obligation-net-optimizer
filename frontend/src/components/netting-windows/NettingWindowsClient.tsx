"use client";
import { useEffect, useState } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { getAnomalies, getNettingWindows, triggerNetting } from "@/lib/api";
import { WindowList } from "./WindowList";
import { WindowDetail } from "./WindowDetail";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "../ui/PageHeader";
import { Pagination } from "../ui/Pagination";
import { useRouter, useSearchParams } from "next/navigation";
import { SearchBar } from "../ui/SearchBar";


export function NettingWindowsClient() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();

  const urlWindow = searchParams.get("window") ?? "";
  const page = Number(searchParams.get("page") ?? "1");
  const selectedId = urlWindow && /^\d+$/.test(urlWindow) ? Number(urlWindow) : null;
  const windowIdParam = selectedId ?? undefined;

  const [input, setInput] = useState(urlWindow);

  useEffect(() => {
    setInput(urlWindow);
  }, [urlWindow]);

  const {
    data: listData,
    isLoading: listLoading,
    isError: listError,
    error: listErrorObj
  } = useQuery({
    queryKey: ["netting-windows", page, windowIdParam],
    queryFn: () => getNettingWindows({ page, window_id: windowIdParam })
  });

  const { data: anomalyReport } = useQuery({
    queryKey: ["anomalies"],
    queryFn: getAnomalies
  });

  const mutation = useMutation({
    mutationFn: triggerNetting,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["netting-windows"] });
    }
  });

  const submitSearch = () => {
    const params = new URLSearchParams();
    if (input && /^\d+$/.test(input)) {
      params.set("window", input);
    }
    params.set("page", "1");
    router.push(`/netting-windows?${params.toString()}`);
  };

  const selectWindow = (id: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("window", String(id));
    router.push(`/netting-windows?${params.toString()}`);
  };

  const changePage = (newPage: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(newPage));
    router.push(`/netting-windows?${params.toString()}`);
  };

  const totalPages = Math.ceil((listData?.count ?? 0) / 20);
  const anomalyWindowIds = new Set(
    (anomalyReport?.anomalies ?? []).map((a) => a.window_id)
  );

  return (
    <main className="min-h-screen bg-slate-950 p-8 space-y-6">
      <PageHeader
        title={`Netting Windows`}
        description="Clearing and settlement cycles"
        action={
          <Button
            variant="primary"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
          >
            Trigger Netting
          </Button>
        }
      />

      <SearchBar
        value={input}
        onChange={setInput}
        onSubmit={submitSearch}
        placeholder="Search by window ID... (press Enter)"
      />

      {/* Display Mutation Error/Success */}
      {mutation.isError && (
        <div className="rounded-md bg-rose-500/10 px-4 py-3 text-sm text-rose-400">
          {mutation.error?.message || "Failed to trigger netting."}
        </div>
      )}
      {mutation.isSuccess && (
        <div className="rounded-md bg-emerald-500/10 px-4 py-3 text-sm text-emerald-400">
          Netting triggered. Task ID: {mutation.data.task_id}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Master List */}
        <section className="lg:col-span-1">
          <Card className="bg-slate-950 border-slate-800 p-0 overflow-hidden">
            <div className="p-4 border-b border-slate-800">
              <h2 className="font-medium font-semibold text-slate-200">Windows</h2>
            </div>
            <WindowList
              data={listData?.results ?? []}
              isLoading={listLoading}
              isError={listError}
              error={listErrorObj}
              selectedId={selectedId}
              onSelect={selectWindow}
              anomalyWindowIds={anomalyWindowIds}
            />
          </Card>

          {/* Pagination */}
          {listData && listData.count > 0 && (
            <div className="flex justify-center border-t border-slate-800 p-4">
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                onPageChange={changePage}
              />
            </div>
          )}
        </section>

        {/* Detail Pane */}
        <section className="lg:col-span-2">
          {selectedId ? (
            <WindowDetail windowId={selectedId} />
          ) : (
            <Card className="bg-slate-900 border-slate-800 h-full flex items-center justify-center">
              <p className="text-slate-500">Select a window to view details</p>
            </Card>
          )}
        </section>
      </div>
    </main>
  );
}