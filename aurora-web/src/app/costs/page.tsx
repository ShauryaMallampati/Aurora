"use client";

import Link from "next/link";
import { ArrowRight, Info } from "lucide-react";
import {
  ResearchPageShell,
  ResearchPanel,
  ResearchSubtlePanel,
} from "@/components/ui/research-page-shell";

export default function CostsPage() {
  return (
    <ResearchPageShell
      eyebrow="Cost Analysis"
      title="Cost analysis"
      description="The previous cost surface depended on fixed comparison assumptions. Until that view is wired to artifact-backed or source-backed data, this page stays descriptive instead of presenting synthetic numbers."
      stats={[
        {
          label: "Status",
          value: "Not in judged flow",
          note: "The main presentation should stay focused on simulation, method, runs, and lab output.",
        },
        {
          label: "Data requirement",
          value: "Live source needed",
          note: "Cost reporting should come from explicit source data or recorded evaluation output.",
        },
      ]}
      actions={
        <>
          <Link href="/sim" className="aurora-button-primary">
            Open simulation
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link href="/method" className="aurora-button-secondary">
            View method
            <ArrowRight className="h-4 w-4" />
          </Link>
        </>
      }
    >
      <ResearchPanel className="space-y-5">
        <div className="flex items-start gap-3">
          <Info className="mt-0.5 h-5 w-5 shrink-0 text-slate-300" />
          <div>
            <p className="text-sm font-semibold text-white">Why this page is simplified</p>
            <p className="mt-2 text-sm leading-7 text-slate-300">
              A cost view should not show fixed acreage, response-time, or savings figures unless those
              values are tied to a specific source or experiment output. The current repo does not expose
              that data path cleanly yet.
            </p>
          </div>
        </div>

        <ResearchSubtlePanel>
          <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-400">Recommended presentation</p>
          <p className="mt-3 text-sm leading-7 text-slate-300">
            For the science-fair walkthrough, keep the focus on the simulation, the method page, the run
            archive, and the lab output. Those views now reflect actual local artifacts or backend state.
          </p>
        </ResearchSubtlePanel>
      </ResearchPanel>
    </ResearchPageShell>
  );
}
