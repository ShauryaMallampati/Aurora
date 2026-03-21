"use client";

import { methodFindings, methodPipeline } from "@/shared/methodContent";

export function MethodTab() {
  return (
    <div className="space-y-4">
      <section className="rounded-md border border-slate-800 bg-slate-900 p-4">
        <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
          Workflow
        </p>
        <div className="mt-4 space-y-3">
          {methodPipeline.map((step, index) => (
            <div key={step.title} className="rounded-md border border-slate-800 bg-slate-950 p-3">
              <p className="text-xs uppercase tracking-[0.08em] text-slate-500">Step {index + 1}</p>
              <h3 className="mt-1 text-sm font-semibold text-white">{step.title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-300">{step.detail}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-md border border-slate-800 bg-slate-900 p-4">
        <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
          Interpretation
        </p>
        <div className="mt-4 space-y-3">
          {methodFindings.map((finding) => (
            <div key={finding} className="rounded-md border border-slate-800 bg-slate-950 p-3">
              <p className="text-sm leading-6 text-slate-300">{finding}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
