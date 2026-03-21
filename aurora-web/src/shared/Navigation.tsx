"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const PRIMARY_ROUTES = [
  { href: "/sim", label: "Simulation" },
  { href: "/method", label: "Method" },
  { href: "/runs", label: "Runs" },
  { href: "/lab", label: "Lab" },
] as const;

export function Navigation() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-950/95">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <Link href="/sim" className="text-xl font-semibold tracking-[0.14em] text-white">
            AURORA
          </Link>
          <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-400">
            Wildfire containment simulation and evaluation
          </p>
        </div>

        <nav className="flex flex-wrap gap-2">
          {PRIMARY_ROUTES.map((route) => {
            const isActive = pathname === route.href || pathname.startsWith(`${route.href}/`);

            return (
              <Link
                key={route.href}
                href={route.href}
                aria-current={isActive ? "page" : undefined}
                className={`rounded-md border px-4 py-2 text-sm font-medium transition ${
                  isActive
                    ? "border-slate-500 bg-slate-800 text-white"
                    : "border-slate-800 bg-slate-900 text-slate-300 hover:border-slate-700 hover:text-white"
                }`}
              >
                {route.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
