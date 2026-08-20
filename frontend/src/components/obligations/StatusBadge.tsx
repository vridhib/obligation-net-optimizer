import { cn } from "@/lib/utils";


const statusStyles = {
  pending: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  netted: "bg-sky-500/10 text-sky-400 border-sky-500/20",
  settled: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  failed: "bg-rose-500/10 text-rose-400 border-rose-500/20"
};

const statusDot = {
  pending: "bg-amber-400",
  netted: "bg-sky-400",
  settled: "bg-emerald-400",
  failed: "bg-rose-400"
};

export function StatusBadge({ status }: { status: keyof typeof statusStyles }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        statusStyles[status]
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", statusDot[status])} />
      {status}
    </span>
  );
}