"use client";
import { Search, X } from "lucide-react";
import { cn } from "@/lib/utils";


interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onClear?: () => void;
  placeholder?: string;
  className?: string;
}

export function SearchBar({
  value,
  onChange,
  onSubmit,
  onClear,
  placeholder,
  className
}: SearchBarProps) {
  const handleClear = () => {
    onChange("");
    onClear?.();
  };

  return (
    <div className={cn("relative", className)}>
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
      <input
        type="search"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            onSubmit();
          } else if (e.key === "Escape") {
            handleClear();
            onSubmit();
          }
        }}
        className="w-full rounded-sm border border-slate-700 bg-slate-950 py-2 pl-9 pr-9 text-sm text-slate-200 placeholder-slate-500 focus:outline-none"
      />
      {value && (
        <button
          type="button"
          onClick={handleClear}
          aria-label="Clear search"
          className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-slate-500 hover:text-slate-300"
        >
        </button>
      )}
    </div>
  );
}