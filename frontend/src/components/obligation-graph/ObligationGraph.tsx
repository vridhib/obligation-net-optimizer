"use client";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getNettingWindows, getGraph } from "@/lib/api";
import { GraphView } from "./GraphView";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "../ui/PageHeader";


export function ObligationGraph() {
  const [selectedWindow, setSelectedWindow] = useState<number | null>(null);
  const [view, setView] = useState<"gross" | "net">("gross");

  // Fetch first page of windows for selection
  const { data: windowsData, isLoading: windowsLoading, error: windowsError } = useQuery({
    queryKey: ["netting-windows-graph"],
    queryFn: () => getNettingWindows({ page: 1 })
  });

  // Fetch graph for selected window
  const { data: graphData, isLoading: graphLoading, error: graphError } = useQuery({
    queryKey: ["graph", selectedWindow, view],
    queryFn: () => getGraph(selectedWindow ?? "latest", view),
    enabled: !!selectedWindow
  });

  if (windowsLoading) return <Skeleton className="h-96 w-full" />;
  if (windowsError) return <ErrorMessage message="Failed to load windows." />;
  if (!windowsData?.results.length) return <EmptyState message="No windows available." />;

  return (
    <main className="min-h-screen bg-slate-950 p-8 space-y-6">
      <PageHeader
        title="Obligation Graph"
        description="Visualize payment flows between participants"
        action={
          <>
            <Button
              variant={view === "net" ? "primary" : "secondary"}
              size="sm"
              onClick={() => setView("net")}
            >
              Net
            </Button>
            <Button
              variant={view === "gross" ? "primary" : "secondary"}
              size="sm"
              onClick={() => setView("gross")}
            >
              Gross
            </Button>
          </>
        }
      />
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Window Selector */}
        <Card className="lg:col-span-1 bg-slate-950 border-slate-800 p-4">
          <h2 className="mb-3 font-semibold font-medium text-slate-300">Windows</h2>
          <ul className="space-y-2">
            {windowsData.results.map((w) => (
              <li key={w.window_id}>
                <button
                  onClick={() => setSelectedWindow(w.window_id)}
                  className={`w-full text-left p-2 rounded-md text-sm transition-colors ${selectedWindow === w.window_id
                    ? "bg-indigo-600/20 text-indigo-300"
                    : "text-slate-400 hover:bg-slate-800"
                    }`}
                >
                  #{w.window_id} — {new Date(w.end_time).toLocaleString([], { hour: "2-digit", minute: "2-digit" })}
                </button>
              </li>
            ))}
          </ul>
        </Card>

        {/* Graph Area */}
        <Card className="lg:col-span-3 bg-slate-950 border-slate-800 p-4">
          {!selectedWindow ? (
            <EmptyState message="Select a window to display the graph." />
          ) : graphLoading ? (
            <Skeleton className="h-[600px] w-full" />
          ) : graphError || !graphData ? (
            <ErrorMessage message="Failed to load graph." />
          ) : (
            <GraphView data={graphData} />
          )}
        </Card>
      </div>
    </main>
  );
}