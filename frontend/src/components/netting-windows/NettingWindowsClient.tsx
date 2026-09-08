"use client";
import { useState } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { getNettingWindows, triggerNetting } from "@/lib/api";
import { WindowList } from "./WindowList";
import { WindowDetail } from "./WindowDetail";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "../ui/PageHeader";
import { Pagination } from "../ui/Pagination";


export function NettingWindowsClient() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();

  const {
    data: listData,
    isLoading: listLoading,
    isError: listError,
    error: listErrorObj,
  } = useQuery({
    queryKey: ["netting-windows", page],
    queryFn: () => getNettingWindows({ page })
  });

  const mutation = useMutation({
    mutationFn: triggerNetting,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["netting-windows"] });
    },
  });

  const totalPages = Math.ceil((listData?.count ?? 0) / 20);

  return (
    <main className="min-h-screen bg-slate-950 p-8 space-y-6">
      <PageHeader
        title="Netting Windows"
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
              onSelect={setSelectedId}
            />
          </Card>
        </section>

        {/* Pagination */}
        {listData && listData.count > 0 && (
          <div className="flex justify-center border-t border-slate-800 p-4"> 
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              onPageChange={(newPage) => setPage(newPage)}
            />
          </div>
        )}

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