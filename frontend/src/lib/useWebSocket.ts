"use client";
import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";


const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws/obligations/";

export function useObligationUpdates() {
  const queryClient = useQueryClient();

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;

      ws = new WebSocket(WS_URL);

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        // Update summary in place
        queryClient.setQueryData(["summary"], (old: any) => ({
          ...(old ?? {}),
          total_settled: data.total_settled,
          total_failed: data.total_failed,
          liquidity_saved: data.liquidity_saved,
          gross_volume: data.gross_volume,
          failure_rate: data.failure_rate
        }));

        // Update participants in place
        queryClient.setQueryData(["participants"], (old: any) => {
          const balances = Object.entries(data.balances).map(([participant, balance]) => ({
            participant,
            balance,
            last_updated: new Date().toISOString()
          }));
          if (!old) {
            return { count: balances.length, next: null, previous: null, results: balances };
          }
          return { ...old, results: balances };
        });

        // Invalidate lists/graphs that need to be refetched
        queryClient.invalidateQueries({ queryKey: ["netting-windows"] });
        queryClient.invalidateQueries({ queryKey: ["graph"] });
      };

      ws.onclose = () => {
        if (cancelled) return;
        reconnectTimer = setTimeout(connect, 2000);
      };

      // Silent, onclose will trigger reconnect
      ws.onerror = () => {
        ws?.close();
      };
    };

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, [queryClient]);
}