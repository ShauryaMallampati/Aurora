import { ReactNode } from "react";
import { Navigation } from "@/shared/Navigation";

interface PageStat {
  label: string;
  value: string;
  note?: string;
}

interface ResearchPageShellProps {
  eyebrow: string;
  title: string;
  description: string;
  stats?: PageStat[];
  actions?: ReactNode;
  children: ReactNode;
  contentClassName?: string;
}

export function ResearchPageShell({
  eyebrow,
  title,
  description,
  stats = [],
  actions,
  children,
  contentClassName = "",
}: ResearchPageShellProps) {
  return (
    <div className="min-h-screen">
      <Navigation />

      <main className="mx-auto max-w-6xl px-6 py-8">
        <header className="border-b border-slate-700 pb-8">
          <p className="aurora-kicker">{eyebrow}</p>
          <h1 className="mt-2 text-3xl font-semibold text-white sm:text-4xl">{title}</h1>
          <p className="mt-3 max-w-3xl text-base leading-7 text-slate-300">{description}</p>

          {actions ? <div className="mt-5 flex flex-wrap gap-3">{actions}</div> : null}

          {stats.length > 0 ? (
            <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {stats.map((stat) => (
                <div key={`${stat.label}-${stat.value}`} className="rounded-md border border-slate-700 bg-slate-900 p-4">
                  <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                    {stat.label}
                  </p>
                  <p className="mt-2 text-2xl font-semibold text-white">{stat.value}</p>
                  {stat.note ? <p className="mt-2 text-sm leading-6 text-slate-400">{stat.note}</p> : null}
                </div>
              ))}
            </div>
          ) : null}
        </header>

        <div className={`mt-8 space-y-8 ${contentClassName}`}>{children}</div>
      </main>
    </div>
  );
}

export function ResearchPanel({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <section className={`aurora-panel rounded-md p-6 ${className}`}>{children}</section>;
}

export function ResearchSubtlePanel({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <section className={`aurora-panel-muted rounded-md p-5 ${className}`}>{children}</section>;
}
