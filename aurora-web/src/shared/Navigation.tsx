"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Flame } from "lucide-react";

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/sim", label: "Mission Control" },
  { href: "/scenarios", label: "Scenarios" },
  { href: "/lab", label: "Lab" },
  { href: "/runs", label: "History" },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="bg-[#0a0a0b]/90 backdrop-blur-xl border-b border-white/5 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg flex items-center justify-center">
              <Flame className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-semibold tracking-tight">AURORA</span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-1">
            {NAV_LINKS.map((link) => {
              const isActive = pathname === link.href ||
                (link.href !== "/" && pathname.startsWith(link.href));

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-1.5 rounded-md text-[13px] transition-colors ${isActive
                      ? "text-white bg-white/10"
                      : "text-white/50 hover:text-white hover:bg-white/5"
                    }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>

          {/* ISEF Badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-orange-500/10 border border-orange-500/20 rounded-full">
            <div className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse"></div>
            <span className="text-xs font-medium text-orange-400">ISEF 2025</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
