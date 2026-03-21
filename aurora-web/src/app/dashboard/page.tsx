'use client';

import Link from "next/link";
import { ArrowRight, LineChart } from "lucide-react";
import { PerformanceDashboard } from '@/components/performance-dashboard';
import {
  ResearchPageShell,
  ResearchPanel,
  ResearchSubtlePanel,
} from "@/components/ui/research-page-shell";

export default function DashboardPage() {
  return (
    <ResearchPageShell
      eyebrow="Training Metrics"
      title="Training dashboard"
      description="This page summarizes the local training artifacts for the PPO baseline and hybrid controller."
      stats={[
        {
          label: "Source",
          value: "results/",
          note: "Metrics are loaded from local experiment artifacts.",
        },
        {
          label: "Display",
          value: "Artifact summary",
          note: "This view reports what is currently available on disk.",
        },
      ]}
      actions={
        <Link
          href="/runs"
          className="aurora-button-secondary"
        >
          Open runs
          <ArrowRight className="h-4 w-4" />
        </Link>
      }
    >
      <ResearchPanel className="space-y-4">
        <div className="flex items-start gap-3">
          <LineChart className="mt-1 h-5 w-5 shrink-0 text-sky-200" />
          <div>
            <p className="text-sm font-semibold text-white">How to present this page</p>
            <p className="mt-1 text-sm leading-7 text-slate-300">
              Use this page for the current artifact-backed aggregate metrics and trend charts.
            </p>
          </div>
        </div>

        <ResearchSubtlePanel>
          <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-400">Notes</p>
          <p className="mt-3 text-sm leading-7 text-slate-300">
            For configuration details, use the lab page. For per-run records, use the runs page. For live interactive behavior, use the simulation page.
          </p>
        </ResearchSubtlePanel>
      </ResearchPanel>

      <div className="mt-6">
        <PerformanceDashboard />
      </div>
    </ResearchPageShell>
  );
}
