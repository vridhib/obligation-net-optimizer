"use client";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getNettingWindows, getGraph } from "@/lib/api";
import { GraphView } from "./GraphView";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { EmptyState } from "@/components/ui/EmptyState";
import { PageHeader } from "../ui/PageHeader";
import { Pagination } from "../ui/Pagination";
import { useRouter, useSearchParams } from "next/navigation";
import { SearchBar } from "../ui/SearchBar";


export function ObligationGraph() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const urlWindow = searchParams.get("window") ?? "";
  const page = Number(searchParams.get("page") ?? "1");
  const view = (searchParams.get("view") as "gross" | "net") ?? "net";
  const selectedId = urlWindow && /^\d+$/.test(urlWindow) ? Number(urlWindow) : null;
  const windowIdParam = selectedId ?? undefined;

  const [input, setInput] = useState(urlWindow);
  //const [view, setView] = useState<"gross" | "net">("net");

  useEffect(() => {
    setInput(urlWindow);
  }, [urlWindow]);

  // Fetch netting windows for selection
  const { data: windowsData, isLoading: windowsLoading, error: windowsError } = useQuery({
    queryKey: ["netting-windows-graph", page, windowIdParam],
    queryFn: () => getNettingWindows({ page, window_id: windowIdParam })
  });

  const totalPages = Math.ceil((windowsData?.count ?? 0) / 20);

  // Fetch graph for selected window
  const { data: graphData, isLoading: graphLoading, error: graphError } = useQuery({
    queryKey: ["graph", windowIdParam, view],
    queryFn: () => getGraph(windowIdParam!, view),
    enabled: !!windowIdParam
  });

  const submitSearch = () => {
    const params = new URLSearchParams();
    if (input && /^\d+$/.test(input)) {
      params.set("window", input);
    }
    params.set("page", "1");
    router.push(`/obligation-graph?${params.toString()}`);
  };

  const selectWindow = (id: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("window", String(id));
    router.push(`/obligation-graph?${params.toString()}`);
  };

  const setView = (v: "gross" | "net") => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("view", v);
    router.push(`/obligation-graph?${params.toString()}`);
  };

  const changePage = (newPage: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(newPage));
    router.push(`/obligation-graph?${params.toString()}`);
  };

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

      <SearchBar
        value={input}
        onChange={setInput}
        onSubmit={submitSearch}
        placeholder="Search by window ID... (press Enter)"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Window Selector */}
        <section className="lg:col-span-1">
          <Card className="bg-slate-950 border-slate-800 p-4">
            <h2 className="mb-3 font-semibold font-medium text-slate-300">Windows</h2>
            <ul className="space-y-2">
              {windowsData.results.map((w) => (
                <li key={w.window_id}>
                  <button
                    onClick={() => selectWindow(w.window_id)}
                    className={`w-full text-left p-2 rounded-md text-sm transition-colors ${windowIdParam === w.window_id
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

          {/* Pagination */}
          {windowsData && windowsData.count > 0 && (
            <div className="flex justify-center border-t border-slate-800 pt-4">
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                onPageChange={changePage}
              />
            </div>
          )}
        </section>

        {/* Graph Area */}
        <section className="lg:col-span-2">
        <Card className="bg-slate-900 border-slate-800 p-4">
          {!windowIdParam ? (
            <EmptyState message="Select a window to display the graph." />
          ) : graphLoading ? (
            <Skeleton className="h-[600px] w-full" />
          ) : graphError || !graphData ? (
            <ErrorMessage message="Failed to load graph." />
          ) : (
            <GraphView data={graphData} />
          )}
        </Card>
        </section>
      </div>
    </main>
  );
}