import { cn } from "@/lib/utils";

export function Card({ className, children }: { className?: string, children: React.ReactNode }) {
  return (
    <div className={cn("rounded-xl border border-neutral-200 p-6 shadow-sm", className)}>
      {children}
    </div>
  );
}