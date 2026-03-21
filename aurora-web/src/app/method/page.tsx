import Link from "next/link";
import { ArrowRight } from "lucide-react";
import {
  ResearchPageShell,
  ResearchPanel,
  ResearchSubtlePanel,
} from "@/components/ui/research-page-shell";
import {
  methodArtifacts,
  methodFindings,
  methodPipeline,
  methodStats,
} from "@/shared/methodContent";

export default function MethodPage() {
  return (
    <ResearchPageShell
      eyebrow="System Method"
      title="Method"
      description="AURORA combines PPO control, LLM guidance, and recorded experiment artifacts into a single wildfire-containment workflow. This page summarizes the actual pipeline used by the repo."
      stats={[...methodStats]}
      actions={
        <>
          <Link href="/sim" className="aurora-button-primary">
            Open simulation
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link href="/runs" className="aurora-button-secondary">
            View recorded runs
            <ArrowRight className="h-4 w-4" />
          </Link>
        </>
      }
    >
      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <ResearchPanel className="space-y-5">
          <div>
            <p className="aurora-kicker">Pipeline</p>
            <h2 className="mt-3 text-2xl font-semibold text-white">Control and evaluation loop</h2>
          </div>

          <div className="space-y-4">
            {methodPipeline.map((step, index) => (
              <ResearchSubtlePanel key={step.title}>
                <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                  Step {index + 1}
                </p>
                <h3 className="mt-2 text-lg font-semibold text-white">{step.title}</h3>
                <p className="mt-3 text-sm leading-7 text-slate-300">{step.detail}</p>
              </ResearchSubtlePanel>
            ))}
          </div>
        </ResearchPanel>

        <div className="space-y-6">
          <ResearchPanel className="space-y-5">
            <div>
              <p className="aurora-kicker">Repository mapping</p>
              <h2 className="mt-3 text-2xl font-semibold text-white">Where each part lives</h2>
            </div>

            <div className="overflow-hidden rounded-md border border-slate-700">
              <table className="w-full text-sm">
                <thead className="bg-slate-900 text-left text-[0.72rem] uppercase tracking-[0.18em] text-slate-400">
                  <tr>
                    <th className="px-4 py-3 font-medium">Area</th>
                    <th className="px-4 py-3 font-medium">Files</th>
                    <th className="px-4 py-3 font-medium">Role</th>
                  </tr>
                </thead>
                <tbody>
                  {methodArtifacts.map((artifact) => (
                    <tr key={artifact.label} className="border-t border-slate-800">
                      <td className="px-4 py-4 font-medium text-white">{artifact.label}</td>
                      <td className="px-4 py-4 font-mono text-xs text-slate-300">{artifact.file}</td>
                      <td className="px-4 py-4 text-slate-300">{artifact.detail}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </ResearchPanel>

          <ResearchPanel className="space-y-4">
            <div>
              <p className="aurora-kicker">Presentation notes</p>
              <h2 className="mt-3 text-2xl font-semibold text-white">What the judges should see</h2>
            </div>

            <div className="space-y-3">
              {methodFindings.map((finding) => (
                <ResearchSubtlePanel key={finding}>
                  <p className="text-sm leading-7 text-slate-300">{finding}</p>
                </ResearchSubtlePanel>
              ))}
            </div>
          </ResearchPanel>
        </div>
      </div>
    </ResearchPageShell>
  );
}
