"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Home } from "lucide-react";

const NAV_LINKS = [
  { href: "/", label: "Home", icon: Home },
  { href: "/sim", label: "Mission Control", icon: Activity },
  { href: "/scenarios", label: "Scenarios", icon: null },
  { href: "/lab", label: "Lab", icon: null },
  { href: "/runs", label: "Run History", icon: null },
  { href: "/sources", label: "Data Sources", icon: null },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="bg-gray-950/80 backdrop-blur-xl border-b border-gray-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-600 rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold text-white">AURORA</span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-1">
            {NAV_LINKS.map((link) => {
              const isActive = pathname === link.href;
              const Icon = link.icon;
              
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all relative group ${
                    isActive
                      ? "text-white bg-orange-500/20"
                      : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {Icon && <Icon className="w-4 h-4" />}
                    {link.label}
                  </div>
                  {!isActive && (
                    <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-orange-400 group-hover:w-full transition-all duration-300" />
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
