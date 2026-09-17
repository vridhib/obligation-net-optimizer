"use client";
import { Anomaly } from "@/lib/types";
import { Card } from "../ui/Card";
import { AlertTriangle } from "lucide-react";
import Link from "next/link";


interface AnomalyBannerProps {
  anomalies: Anomaly[];
  maxDisplay?: number;
}

export function AnomalyBanner({ anomalies, maxDisplay = 3 }: AnomalyBannerProps) {
  if (anomalies.length === 0) return null;

  const displayed = anomalies.slice(0, maxDisplay);
  const remaining = anomalies.length - displayed.length;

  return (
    <Card className="border-amber-500/30 bg-amber-500/5 p-4">
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 text-amber-400" />
        <div className="flex-1">
          <h3 className="text-sm font-medium text-amber-400">
            {anomalies.length} anomal{anomalies.length === 1 ? "y" : "ies"} detected
          </h3>
          <ul className="mt-2 space-y-1">
            {displayed.map((a, i) => (
              <li key={i} className="text-sm text-slate-400">
                <span className="font-mono text-slate-300">
                  {new Date(a.window_end).toLocaleString()}
                </span>
                {" — "}
                <span className="text-slate-300">{a.metric}</span>
                {" scored "}
                <span className="text-slate-400">{a.score.toFixed(4)}σ</span>
                {" via "}
                <span className="text-slate-400">{a.method === "z_score" ? "statistical" : "multivariate"}</span>
              </li>
            ))}
            {remaining > 0 && (
              <li className="text-xs text-slate-500">
                +{" "}
                <Link href="/anomalies" className="text-indigo-400 hover:underline">
                  {remaining} more
                </Link>
              </li>
            )}
          </ul>
        </div>
      </div>
    </Card>
  );
}