"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowRight,
  Clock,
  Download,
  Play,
  RotateCcw,
  TrendingUp,
} from "lucide-react";
import {
  ResearchPageShell,
  ResearchPanel,
  ResearchSubtlePanel,
} from "@/components/ui/research-page-shell";

interface ExperimentRequest {
  mode: "ppo" | "hybrid";
  phase: "phase_a" | "phase_b" | "phase_c" | "quick" | "full";
}

interface TrainingMetric {
  step: number;
  episode_return: number;
  completion_rate: number;
  idle_steps: number;
  llm_latency_ms: number;
  timestamp: string;
}

interface ExperimentResponse {
  id: string;
  mode: "ppo" | "hybrid";
  phase: ExperimentRequest["phase"];
  status: "starting" | "running" | "completed" | "failed";
  start_time: string;
  elapsed_seconds: number;
  metrics: TrainingMetric[];
  current_step?: number;
  total_steps?: number;
  message: string;
}

interface ArtifactRunRecord {
  runId: string;
  modelType: "ppo" | "hybrid";
  seed: number;
  timestamp: string;
  totalSteps: number;
  scenarioId?: string;
  containmentTime: number;
  successRate: number;
  avgReturnPerStep: number;
}

const PHASE_OPTIONS: Array<{
  value: ExperimentRequest["phase"];
  label: string;
  note: string;
}> = [
  { value: "quick", label: "Quick", note: "Short local validation run." },
  { value: "phase_a", label: "Phase A", note: "Early-stage training sweep." },
  { value: "phase_b", label: "Phase B", note: "Intermediate training sweep." },
  { value: "phase_c", label: "Phase C", note: "Full scenario-scale evaluation pass." },
  { value: "full", label: "Full", note: "Longest configured run." },
];

export default function ExperimentLabPage() {
  const fieldClassName =
    "w-full rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white transition outline-none placeholder:text-slate-500 focus:border-orange-300/50 focus:bg-white/[0.06]";

  const [config, setConfig] = useState<ExperimentRequest>({
    mode: "hybrid",
    phase: "quick",
  });
  const [activeExperiment, setActiveExperiment] = useState<ExperimentResponse | null>(null);
  const [recentRuns, setRecentRuns] = useState<ArtifactRunRecord[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const metrics = activeExperiment?.metrics ?? [];
  const bestReturn = metrics.length > 0 ? Math.max(...metrics.map((metric) => metric.episode_return)) : 0;
  const bestCompletion =
    metrics.length > 0 ? Math.max(...metrics.map((metric) => metric.completion_rate)) : 0;
  const minIdleSteps =
    metrics.length > 0 ? Math.min(...metrics.map((metric) => metric.idle_steps)) : 0;
  const avgLatency =
    metrics.length > 0
      ? metrics.reduce((sum, metric) => sum + metric.llm_latency_ms, 0) / metrics.length
      : 0;

  const phaseNote = useMemo(
    () => PHASE_OPTIONS.find((option) => option.value === config.phase)?.note ?? "",
    [config.phase],
  );

  useEffect(() => {
    let cancelled = false;

    const loadRecentRuns = async () => {
      try {
        const response = await fetch("/api/runs", { cache: "no-store" });
        if (!response.ok) {
          return;
        }

        const data = (await response.json()) as ArtifactRunRecord[];
        if (!cancelled) {
          setRecentRuns(data.slice(0, 8));
        }
      } catch (fetchError) {
        console.error("Failed to load recent artifacts:", fetchError);
      }
    };

    void loadRecentRuns();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!activeExperiment || !["starting", "running"].includes(activeExperiment.status)) {
      return;
    }

    const interval = window.setInterval(async () => {
      try {
        const response = await fetch(`/api/run_experiment?id=${activeExperiment.id}`, {
          cache: "no-store",
        });
        if (!response.ok) {
          throw new Error("Failed to poll experiment");
        }

        const data = (await response.json()) as ExperimentResponse;
        setActiveExperiment(data);
        setError(null);

        if (!["starting", "running"].includes(data.status)) {
          window.clearInterval(interval);
          const refreshedRuns = await fetch("/api/runs", { cache: "no-store" });
          if (refreshedRuns.ok) {
            setRecentRuns(((await refreshedRuns.json()) as ArtifactRunRecord[]).slice(0, 8));
          }
        }
      } catch (pollError) {
        console.error("Failed to poll experiment:", pollError);
        setError((pollError as Error).message);
        window.clearInterval(interval);
      }
    }, 2000);

    return () => {
      window.clearInterval(interval);
    };
  }, [activeExperiment]);

  const handleRunExperiment = async () => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch("/api/run_experiment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      const data = (await response.json()) as ExperimentResponse | { error?: string; details?: string };
      if (!response.ok) {
        throw new Error(data && "error" in data && data.error ? data.error : "Failed to start experiment");
      }

      setActiveExperiment(data as ExperimentResponse);
    } catch (submitError) {
      console.error("Failed to start experiment:", submitError);
      setError((submitError as Error).message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleExportResults = () => {
    if (!activeExperiment) {
      return;
    }

    const dataBlob = new Blob([JSON.stringify(activeExperiment, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${activeExperiment.id}_experiment.json`;
    link.click();
  };

  return (
    <ResearchPageShell
      eyebrow="Experiment Lab"
      title="Experiment lab"
      description="This page starts local experiment runs through `/api/run_experiment` and reports live status from the backend. It does not generate browser-side placeholder metrics."
      stats={[
        {
          label: "Current status",
          value: activeExperiment?.status ?? "idle",
          note: activeExperiment?.message ?? "No active experiment.",
        },
        {
          label: "Metric points",
          value: metrics.length.toString(),
          note: "Parsed from backend experiment output.",
        },
        {
          label: "Recent artifacts",
          value: recentRuns.length.toString(),
          note: "Experiment artifacts currently visible in the results directory.",
        },
        {
          label: "Phase",
          value: config.phase,
          note: phaseNote,
        },
      ]}
      actions={
        <>
          <Link href="/runs" className="aurora-button-primary">
            View runs
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link href="/method" className="aurora-button-secondary">
            View method
            <ArrowRight className="h-4 w-4" />
          </Link>
        </>
      }
    >
      <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
        <ResearchPanel className="space-y-6">
          <div>
            <p className="aurora-kicker">Launch configuration</p>
            <h2 className="mt-3 text-2xl font-semibold text-white">Backend experiment controls</h2>
            <p className="mt-3 text-sm leading-7 text-slate-300">
              Only backend-supported fields are shown here. The local training manager chooses the exact
              step counts and output artifacts for each phase.
            </p>
          </div>

          <ResearchSubtlePanel>
            <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-400">Environment note</p>
            <p className="mt-3 text-sm leading-7 text-slate-300">
              This route requires the local Python environment. If the process cannot start, the error
              returned by the backend is shown directly below.
            </p>
          </ResearchSubtlePanel>

          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                Model
              </label>
              <select
                value={config.mode}
                onChange={(event) =>
                  setConfig((current) => ({
                    ...current,
                    mode: event.target.value as ExperimentRequest["mode"],
                  }))
                }
                className={fieldClassName}
              >
                <option value="ppo">PPO baseline</option>
                <option value="hybrid">Hybrid controller</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                Phase
              </label>
              <select
                value={config.phase}
                onChange={(event) =>
                  setConfig((current) => ({
                    ...current,
                    phase: event.target.value as ExperimentRequest["phase"],
                  }))
                }
                className={fieldClassName}
              >
                {PHASE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <p className="mt-2 text-sm text-slate-400">{phaseNote}</p>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleRunExperiment}
              disabled={isSubmitting || activeExperiment?.status === "running" || activeExperiment?.status === "starting"}
              className="inline-flex flex-1 items-center justify-center gap-2 rounded-md border border-blue-600 bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:border-slate-700 disabled:bg-slate-700"
            >
              {isSubmitting ? (
                <>
                  <RotateCcw className="h-4 w-4 animate-spin" />
                  Starting
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Start experiment
                </>
              )}
            </button>

            <button
              onClick={handleExportResults}
              disabled={!activeExperiment}
              className="inline-flex flex-1 items-center justify-center gap-2 rounded-md border border-slate-700 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Download className="h-4 w-4" />
              Export run JSON
            </button>
          </div>

          {error ? (
            <div className="rounded-md border border-red-800 bg-red-950/40 p-4 text-sm text-red-100">
              {error}
            </div>
          ) : null}

          {activeExperiment ? (
            <ResearchSubtlePanel>
              <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-400">Active run</p>
              <div className="mt-3 space-y-2 text-sm text-slate-300">
                <div className="flex justify-between gap-4">
                  <span>Experiment ID</span>
                  <span className="font-mono text-white">{activeExperiment.id}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span>Status</span>
                  <span className="font-mono text-white">{activeExperiment.status}</span>
                </div>
                <div className="flex justify-between gap-4">
                  <span>Elapsed</span>
                  <span className="font-mono text-white">
                    {activeExperiment.elapsed_seconds.toFixed(1)} s
                  </span>
                </div>
                <div className="flex justify-between gap-4">
                  <span>Current step</span>
                  <span className="font-mono text-white">
                    {activeExperiment.current_step ?? metrics.at(-1)?.step ?? 0}
                  </span>
                </div>
              </div>
            </ResearchSubtlePanel>
          ) : null}
        </ResearchPanel>

        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <MetricCard
              icon={<TrendingUp className="h-4 w-4" />}
              label="Best Return"
              value={metrics.length > 0 ? bestReturn.toFixed(1) : "N/A"}
              color="text-emerald-200"
            />
            <MetricCard
              icon={<Activity className="h-4 w-4" />}
              label="Best Completion"
              value={metrics.length > 0 ? `${(bestCompletion * 100).toFixed(0)}%` : "N/A"}
              color="text-sky-200"
            />
            <MetricCard
              icon={<Clock className="h-4 w-4" />}
              label="Min Idle Steps"
              value={metrics.length > 0 ? minIdleSteps.toFixed(0) : "N/A"}
              color="text-orange-200"
            />
            <MetricCard
              icon={<Activity className="h-4 w-4" />}
              label="Avg Latency"
              value={metrics.length > 0 ? `${avgLatency.toFixed(1)} ms` : "N/A"}
              color="text-sky-200"
            />
          </div>

          <ResearchPanel className="overflow-hidden p-0">
            <div className="border-b border-white/10 px-6 py-5">
              <p className="aurora-kicker">Live output</p>
              <h3 className="mt-2 text-2xl font-semibold text-white">Backend metric stream</h3>
              <p className="mt-2 text-sm leading-7 text-slate-300">
                Rows below come from the active experiment output. If no experiment is active, the table stays empty.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-white/[0.03] text-[0.72rem] uppercase tracking-[0.18em] text-slate-400">
                  <tr>
                    <th className="px-5 py-4 text-left font-medium">Step</th>
                    <th className="px-5 py-4 text-right font-medium">Return</th>
                    <th className="px-5 py-4 text-right font-medium">Completion</th>
                    <th className="px-5 py-4 text-right font-medium">Idle</th>
                    <th className="px-5 py-4 text-right font-medium">Latency</th>
                    <th className="px-5 py-4 text-left font-medium">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {metrics.map((metric) => (
                    <tr key={`${metric.step}-${metric.timestamp}`} className="border-t border-white/10 transition hover:bg-white/[0.03]">
                      <td className="px-5 py-4 font-mono text-xs text-slate-300">{metric.step}</td>
                      <td className="px-5 py-4 text-right font-mono text-white">
                        {metric.episode_return.toFixed(2)}
                      </td>
                      <td className="px-5 py-4 text-right font-mono text-white">
                        {(metric.completion_rate * 100).toFixed(0)}%
                      </td>
                      <td className="px-5 py-4 text-right font-mono text-slate-300">{metric.idle_steps}</td>
                      <td className="px-5 py-4 text-right font-mono text-slate-300">
                        {metric.llm_latency_ms.toFixed(2)} ms
                      </td>
                      <td className="px-5 py-4 text-slate-300">
                        {new Date(metric.timestamp).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {metrics.length === 0 ? (
              <div className="px-6 py-8 text-sm text-slate-400">
                No live experiment metrics are available yet.
              </div>
            ) : null}
          </ResearchPanel>

          <ResearchPanel className="space-y-4">
            <div>
              <p className="aurora-kicker">Recent artifacts</p>
              <h3 className="mt-2 text-2xl font-semibold text-white">Completed experiment outputs</h3>
            </div>

            {recentRuns.length > 0 ? (
              <div className="overflow-x-auto rounded-md border border-slate-700">
                <table className="w-full text-sm">
                  <thead className="bg-slate-900 text-left text-[0.72rem] uppercase tracking-[0.18em] text-slate-400">
                    <tr>
                      <th className="px-4 py-3 font-medium">Run ID</th>
                      <th className="px-4 py-3 font-medium">Model</th>
                      <th className="px-4 py-3 font-medium">Return</th>
                      <th className="px-4 py-3 font-medium">Completion</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentRuns.map((run) => (
                      <tr key={run.runId} className="border-t border-slate-800">
                        <td className="px-4 py-4 font-mono text-xs text-slate-300">{run.runId}</td>
                        <td className="px-4 py-4 text-white">{run.modelType}</td>
                        <td className="px-4 py-4 font-mono text-white">
                          {(run.avgReturnPerStep * run.totalSteps).toFixed(1)}
                        </td>
                        <td className="px-4 py-4 font-mono text-white">
                          {(run.successRate * 100).toFixed(0)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <ResearchSubtlePanel>
                <p className="text-sm leading-7 text-slate-300">
                  No completed experiment artifacts were found in the local results directory.
                </p>
              </ResearchSubtlePanel>
            )}
          </ResearchPanel>
        </div>
      </div>
    </ResearchPageShell>
  );
}

function MetricCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="rounded-[24px] border border-white/10 bg-white/[0.04] p-5">
      <div className={`${color} mb-3`}>{icon}</div>
      <div className="text-2xl font-semibold text-white">{value}</div>
      <div className="mt-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
        {label}
      </div>
    </div>
  );
}
