'use client';

import Link from "next/link";
import { ArrowRight, PackageCheck } from "lucide-react";
import { OfflineExportPanel } from '@/components/offline-export-panel';
import {
  ResearchPageShell,
  ResearchPanel,
  ResearchSubtlePanel,
} from "@/components/ui/research-page-shell";

export default function ExportPage() {
  return (
    <ResearchPageShell
      eyebrow="Offline Export"
      title="Offline export"
      description="This page packages the site, documentation, and model artifacts for offline review."
      stats={[
        {
          label: "Audience",
          value: "Judges",
          note: "Built for take-home review after the live walkthrough.",
        },
        {
          label: "Contents",
          value: "Models + Docs",
          note: "Package configuration includes checkpoints, logs, documentation, and the web export.",
        },
      ]}
      actions={
        <Link
          href="/dashboard"
          className="aurora-button-secondary"
        >
          View dashboard
          <ArrowRight className="h-4 w-4" />
        </Link>
      }
    >
      <ResearchPanel className="space-y-4">
        <div className="flex items-start gap-3">
          <PackageCheck className="mt-1 h-5 w-5 shrink-0 text-orange-200" />
          <div>
            <p className="text-sm font-semibold text-white">Use this page as the final handoff step</p>
            <p className="mt-1 text-sm leading-7 text-slate-300">
              Use this page to export a portable package containing documents, model artifacts, logs, and a browser-viewable copy of the interface.
            </p>
          </div>
        </div>

        <ResearchSubtlePanel>
          <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-400">Notes</p>
          <p className="mt-3 text-sm leading-7 text-slate-300">
            Offline review is useful when the site needs to be shared without a live environment.
          </p>
        </ResearchSubtlePanel>
      </ResearchPanel>

      <div className="mt-6 max-w-5xl">
        <OfflineExportPanel />
      </div>
    </ResearchPageShell>
  );
}
