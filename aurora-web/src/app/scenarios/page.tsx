"use client";

import Link from "next/link";
import { ArrowRight, CheckCircle2, Database } from "lucide-react";
import { CustomFireCreator } from "@/components/custom-fire-creator";
import {
  ResearchPageShell,
  ResearchPanel,
  ResearchSubtlePanel,
} from "@/components/ui/research-page-shell";

export default function ScenariosPage() {
  return (
    <ResearchPageShell
      eyebrow="Scenario Setup"
      title="Scenario setup"
      description="Scenario selection for the judged workflow now lives primarily in the simulator settings. This page keeps the custom scenario request path without presenting a fixed in-browser fire catalog."
      stats={[
        {
          label: "Primary flow",
          value: "Use /sim",
          note: "The simulator is the main entry point for scenario playback.",
        },
        {
          label: "Custom requests",
          value: "API-backed",
          note: "This form submits to the scenario creation API rather than generating local placeholder rows.",
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
      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <ResearchPanel>
          <CustomFireCreator />
        </ResearchPanel>

        <div className="space-y-6">
          <ResearchPanel className="space-y-4">
            <div>
              <p className="aurora-kicker">Workflow</p>
              <h2 className="mt-3 text-2xl font-semibold text-white">How to use scenarios now</h2>
            </div>

            <ResearchSubtlePanel className="space-y-3">
              <div className="flex gap-3">
                <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-slate-300" />
                <p className="text-sm leading-7 text-slate-300">
                  Use the simulator settings panel to choose an artifact-backed scenario for playback.
                </p>
              </div>
              <div className="flex gap-3">
                <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-slate-300" />
                <p className="text-sm leading-7 text-slate-300">
                  Use the custom request form only when you need to send a new scenario configuration to the backend.
                </p>
              </div>
              <div className="flex gap-3">
                <CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-slate-300" />
                <p className="text-sm leading-7 text-slate-300">
                  Use the runs page when you need recorded outputs rather than a new request.
                </p>
              </div>
            </ResearchSubtlePanel>
          </ResearchPanel>

          <ResearchPanel className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-sky-300/15 bg-sky-300/[0.08]">
                <Database className="h-5 w-5 text-sky-200" />
              </div>
              <div>
                <p className="aurora-kicker">Notes</p>
                <h3 className="mt-3 text-2xl font-semibold text-white">Why the catalog was removed</h3>
                <p className="mt-3 text-sm leading-7 text-slate-300">
                  The old in-browser scenario cards were a fixed list. For this pass, they were removed so the
                  page no longer claims to be a live scenario library without a real backing source.
                </p>
              </div>
            </div>
          </ResearchPanel>
        </div>
      </div>
    </ResearchPageShell>
  );
}
