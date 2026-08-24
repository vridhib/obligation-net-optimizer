"use client";
import { useState } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { getNettingWindows, triggerNetting } from "@/lib/api";
import { WindowList } from "./WindowList";
import { WindowDetail } from "./WindowDetail";
import { TriggerNettingDialog } from "./TriggerNettingDialog";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { PageHeader } from "../ui/PageHeader";


export function NettingWindowsClient() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const {
    data: listData,
    isLoading: listLoading,
    isError: listError,
    error: listErrorObj,
  } = useQuery({
    queryKey: ["netting-windows", page],
    queryFn: () => getNettingWindows({ page }),
  });

  const mutation = useMutation({
    mutationFn: triggerNetting,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["netting-windows"] });
      setIsDialogOpen(false);
    },
  });

  const totalPages = Math.ceil((listData?.count ?? 0) / 20);

  return (
    <main className="min-h-screen bg-slate-950 p-8 space-y-6">
      <PageHeader
        title="Netting Windows"
        description="Clearing and settlement cycles"
        action={
          <Button variant="primary" onClick={() => setIsDialogOpen(true)}>
            Trigger Netting
          </Button>
        }
      />

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

            {/* Pagination */}
            {listData && listData.count > 0 && (
              <div className="flex items-center justify-between border-t border-slate-800 p-4">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={!listData.previous}
                  className="rounded border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-40"
                >
                  Previous
                </button>
                <span className="text-xs text-slate-400">Page {page} of {totalPages}</span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!listData.next}
                  className="rounded border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800 disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            )}
          </Card>
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

      {/* Trigger Dialog */}
      {isDialogOpen && (
        <TriggerNettingDialog
          onClose={() => setIsDialogOpen(false)}
          mutation={mutation}
        />
      )}
    </main>
  );
}