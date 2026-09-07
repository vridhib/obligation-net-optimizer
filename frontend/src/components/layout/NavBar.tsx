"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";


const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/obligations", label: "Obligations" },
  { href: "/netting-windows", label: "Netting Windows" },
  { href: "/obligation-graph", label: "Graph" },
  { href: "/participants", label: "Participants" }
];

export function NavBar() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-40 border-b border-slate-800 bg-slate-950/80 backdrop-blur">
      <div className="flex h-14 items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl font-semibold tracking-tight text-indigo-400">
            ONO
          </span>
        </Link>

        <ul className="flex h-full items-center gap-1">
          {navItems.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href);

            return (
              <li key={item.href} className="h-full">
                <Link
                  href={item.href}
                  className={cn(
                    "flex h-full items-center px-3 py-2 font-medium transition-colors",
                    isActive
                      ? "bg-slate-800 text-slate-100"
                      : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
                  )}
                >
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}