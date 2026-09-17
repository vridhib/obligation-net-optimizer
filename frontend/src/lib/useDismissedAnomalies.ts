"use client";
import { useCallback, useEffect, useState } from "react";


const STORAGE_KEY = "ono:dismissed-anomalies";

function anomalyKey(window_id: number, metric: string) {
  return `${window_id}::${metric}`;
}

export function useDismissedAnomalies() {
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setDismissed(new Set(JSON.parse(stored)));
      } catch {}
    }
  }, []);

  const dismiss = useCallback((window_id: number, metric: string) => {
    setDismissed((prev) => {
      const next = new Set(prev);
      next.add(anomalyKey(window_id, metric));
      localStorage.setItem(STORAGE_KEY, JSON.stringify([...next]));
      return next;
    });
  }, []);

  const clear = useCallback(() => {
    setDismissed(new Set());
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  const isDismissed = useCallback(
    (window_id: number, metric: string) =>
      dismissed.has(anomalyKey(window_id, metric)),
    [dismissed]
  );

  return { dismiss, isDismissed, clear };
}