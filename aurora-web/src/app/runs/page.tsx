"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  Download,
  Filter,
  History,
  Pin,
  PinOff,
  Play,
  Search,
  Trash2,
} from "lucide-react";
import {
  ResearchPageShell,
  ResearchPanel,
  ResearchSubtlePanel,
} from "@/components/ui/research-page-shell";
import {
  deleteRun,
  getRuns,
  isSupabaseConfigured,
  updateRunPin,
} from "@/lib/supabase";

interface RunRecord {
  id: string;
  scenario: string;
  model: "ppo" | "hybrid";
  seed: number;
  metrics: {
    return: number;
    completionRate: number;
    containmentSteps: number;
  };
  duration: number;
  timestamp: string;
  pinned: boolean;
  tags: string[];
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

type DataSource = "supabase" | "artifacts" | "empty";

export default function RunHistoryPage() {
  const router = useRouter();
  const persistenceAvailable = isSupabaseConfigured;
  const fieldClassName =
    "rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white transition outline-none focus:border-orange-300/50 focus:bg-white/[0.06]";

  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [dataSource, setDataSource] = useState<DataSource>("empty");
  const [searchTerm, setSearchTerm] = useState("");
  const [filterModel, setFilterModel] = useState<"all" | "ppo" | "hybrid">("all");
  const [sortBy, setSortBy] = useState<"timestamp" | "return" | "completion">("timestamp");

  const loadRuns = useCallback(async () => {
    setIsLoading(true);

    try {
      const persistedRuns = await getRuns();
      if (persistedRuns.length > 0) {
        setRuns(
          persistedRuns.map((record) => ({
            id: record.id,
            scenario: record.scenario,
            model: record.model,
            seed: record.seed,
            metrics: {
              return: record.return_value,
              completionRate: record.completion_rate,
              containmentSteps: record.containment_steps,
            },
            duration: record.duration,
            timestamp: record.timestamp,
            pinned: record.pinned,
            tags: record.tags,
          })),
        );
        setDataSource("supabase");
        return;
      }

      const response = await fetch("/api/runs", { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to fetch artifact-backed runs");
      }

      const artifactRuns = (await response.json()) as ArtifactRunRecord[];
      if (artifactRuns.length > 0) {
        setRuns(
          artifactRuns.map((record) => ({
            id: record.runId,
            scenario: formatScenarioLabel(record.scenarioId),
            model: record.modelType,
            seed: record.seed,
            metrics: {
              return: record.avgReturnPerStep * record.totalSteps,
              completionRate: record.successRate,
              containmentSteps: record.containmentTime,
            },
            duration: record.totalSteps,
            timestamp: record.timestamp,
            pinned: false,
            tags: ["artifacts", record.modelType, record.scenarioId || "unspecified"].filter(Boolean),
          })),
        );
        setDataSource("artifacts");
        return;
      }

      setRuns([]);
      setDataSource("empty");
    } catch (error) {
      console.error("Failed to load runs:", error);
      setRuns([]);
      setDataSource("empty");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadRuns();
  }, [loadRuns]);

  const filteredRuns = useMemo(
    () =>
      runs
        .filter((run) => {
          const matchesSearch =
            run.scenario.toLowerCase().includes(searchTerm.toLowerCase()) ||
            run.id.includes(searchTerm);
          const matchesModel = filterModel === "all" || run.model === filterModel;
          return matchesSearch && matchesModel;
        })
        .sort((a, b) => {
          if (sortBy === "return") {
            return b.metrics.return - a.metrics.return;
          }
          if (sortBy === "completion") {
            return b.metrics.completionRate - a.metrics.completionRate;
          }
          return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
        }),
    [filterModel, runs, searchTerm, sortBy],
  );

  const pinnedCount = filteredRuns.filter((run) => run.pinned).length;
  const bestReturn = filteredRuns.length > 0 ? Math.max(...filteredRuns.map((run) => run.metrics.return)) : 0;
  const bestCompletion =
    filteredRuns.length > 0
      ? Math.max(...filteredRuns.map((run) => run.metrics.completionRate))
      : 0;
  const ppoBaselineReturn =
    runs.filter((run) => run.model === "ppo").reduce((sum, run) => sum + run.metrics.return, 0) /
      Math.max(1, runs.filter((run) => run.model === "ppo").length) || 0;

  const handleReproduceRun = (run: RunRecord) => {
    sessionStorage.setItem("reproduceRun", JSON.stringify(run));
    router.push("/sim");
  };

  const handleTogglePin = async (runId: string) => {
    if (!persistenceAvailable || dataSource !== "supabase") {
      return;
    }

    const run = runs.find((candidate) => candidate.id === runId);
    if (!run) {
      return;
    }

    const newPinned = !run.pinned;
    setRuns(runs.map((candidate) => (candidate.id === runId ? { ...candidate, pinned: newPinned } : candidate)));
    await updateRunPin(runId, newPinned);
  };

  const handleExportRun = (run: RunRecord) => {
    const improvementPercent =
      run.model === "hybrid" && ppoBaselineReturn > 0
        ? ((run.metrics.return / ppoBaselineReturn - 1) * 100).toFixed(1)
        : null;

    const exportData = {
      ...run,
      exported_at: new Date().toISOString(),
      data_source: dataSource,
      baseline_reference_return: ppoBaselineReturn || null,
      model_improvement_percent: improvementPercent,
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${run.id}_aurora_run.json`;
    link.click();
  };

  const handleDeleteRun = async (runId: string) => {
    if (!persistenceAvailable || dataSource !== "supabase") {
      return;
    }

    setRuns(runs.filter((run) => run.id !== runId));
    await deleteRun(runId);
  };

  return (
    <ResearchPageShell
      eyebrow="Run History"
      title="Run history"
      description="This table only shows persisted or artifact-backed runs. If no runs are available locally, the page reports that directly instead of filling the table with placeholders."
      stats={[
        {
          label: "Visible runs",
          value: filteredRuns.length.toString(),
          note: "Filtered subset of the currently available run records.",
        },
        {
          label: "Pinned",
          value: pinnedCount.toString(),
          note: "Pinned runs are available only for Supabase-backed records.",
        },
        {
          label: "Best return",
          value: filteredRuns.length > 0 ? bestReturn.toFixed(1) : "N/A",
          note: "Highest return in the current filtered table.",
        },
        {
          label: "Source",
          value:
            dataSource === "supabase"
              ? "Supabase"
              : dataSource === "artifacts"
                ? "Artifacts"
                : "No run data",
          note:
            dataSource === "supabase"
              ? "Loaded from Supabase."
              : dataSource === "artifacts"
                ? "Loaded from local experiment artifacts in the results directory."
                : "No persisted or artifact-backed runs were found.",
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
      <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
        <ResearchPanel className="space-y-5">
          <div>
            <p className="aurora-kicker">Data source</p>
            <h2 className="mt-3 text-2xl font-semibold text-white">Current run table</h2>
          </div>

          <ResearchSubtlePanel>
            <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-400">Current mode</p>
            <p className="mt-3 text-sm leading-7 text-slate-300">
              {dataSource === "supabase"
                ? "Run history is being loaded from Supabase."
                : dataSource === "artifacts"
                  ? "Run history is being loaded from local experiment artifacts."
                  : "No run records are available from Supabase or the local results directory."}
            </p>
          </ResearchSubtlePanel>

          <ResearchSubtlePanel>
            <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-400">Usage</p>
            <ul className="mt-3 space-y-3 text-sm leading-7 text-slate-300">
              <li>1. Filter the available run list.</li>
              <li>2. Open a recorded run in the simulation page.</li>
              <li>3. Export a run record when you need a local handoff.</li>
            </ul>
          </ResearchSubtlePanel>
        </ResearchPanel>

        <ResearchPanel className="space-y-5">
          <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr_0.7fr]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                placeholder="Search scenarios or run IDs..."
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                className={`${fieldClassName} w-full pl-11`}
              />
            </div>

            <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] px-4">
              <Filter className="h-4 w-4 text-slate-500" />
              <select
                value={filterModel}
                onChange={(event) => setFilterModel(event.target.value as "all" | "ppo" | "hybrid")}
                className="w-full bg-transparent py-3 text-sm text-white outline-none"
              >
                <option value="all">All models</option>
                <option value="ppo">PPO only</option>
                <option value="hybrid">Hybrid only</option>
              </select>
            </div>

            <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] px-4">
              <select
                value={sortBy}
                onChange={(event) => setSortBy(event.target.value as typeof sortBy)}
                className="w-full bg-transparent py-3 text-sm text-white outline-none"
              >
                <option value="timestamp">Sort: Recent</option>
                <option value="return">Sort: Best return</option>
                <option value="completion">Sort: Best completion</option>
              </select>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-400">
            <p>
              Showing {filteredRuns.length} of {runs.length} runs.
              {pinnedCount > 0 ? ` ${pinnedCount} pinned in this view.` : ""}
            </p>
            <p>
              Best completion in view:{" "}
              <span className="font-mono text-white">
                {filteredRuns.length > 0 ? `${(bestCompletion * 100).toFixed(0)}%` : "N/A"}
              </span>
            </p>
          </div>

          <div className="overflow-x-auto rounded-[24px] border border-white/10">
            <table className="w-full text-sm">
              <thead className="bg-white/[0.03] text-[0.72rem] uppercase tracking-[0.18em] text-slate-400">
                <tr>
                  <th className="px-5 py-4 text-left font-medium">Run ID</th>
                  <th className="px-5 py-4 text-left font-medium">Scenario</th>
                  <th className="px-5 py-4 text-left font-medium">Model</th>
                  <th className="px-5 py-4 text-right font-medium">Return</th>
                  <th className="px-5 py-4 text-right font-medium">Completion</th>
                  <th className="px-5 py-4 text-right font-medium">Steps</th>
                  <th className="px-5 py-4 text-left font-medium">Tags</th>
                  <th className="px-5 py-4 text-center font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRuns.map((run) => (
                  <tr key={run.id} className="border-t border-white/10 transition hover:bg-white/[0.03]">
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2">
                        {run.pinned ? <Pin className="h-3.5 w-3.5 fill-orange-200 text-orange-200" /> : null}
                        <span className="font-mono text-xs text-slate-300">{run.id}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4 font-medium text-white">{run.scenario}</td>
                    <td className="px-5 py-4">
                      <span
                        className={`rounded-full px-3 py-1 text-[0.72rem] font-semibold uppercase tracking-[0.12em] ${
                          run.model === "hybrid"
                            ? "bg-orange-400/15 text-orange-100"
                            : "bg-sky-300/15 text-sky-100"
                        }`}
                      >
                        {run.model}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right font-mono text-white">{run.metrics.return.toFixed(1)}</td>
                    <td className="px-5 py-4 text-right font-mono text-white">
                      {(run.metrics.completionRate * 100).toFixed(0)}%
                    </td>
                    <td className="px-5 py-4 text-right font-mono text-slate-300">
                      {run.metrics.containmentSteps}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex flex-wrap gap-2">
                        {run.tags.map((tag) => (
                          <span
                            key={tag}
                            className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[0.72rem] text-slate-300"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => handleReproduceRun(run)}
                          className="rounded-full bg-orange-400/15 p-2 text-orange-100 transition hover:bg-orange-400/25"
                          title="Reproduce"
                        >
                          <Play className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleTogglePin(run.id)}
                          disabled={!persistenceAvailable || dataSource !== "supabase"}
                          className={`rounded-full bg-white/[0.06] p-2 text-slate-200 transition hover:bg-white/[0.12] ${
                            !persistenceAvailable || dataSource !== "supabase"
                              ? "cursor-not-allowed opacity-50 hover:bg-white/[0.06]"
                              : ""
                          }`}
                          title={run.pinned ? "Unpin" : "Pin"}
                        >
                          {run.pinned ? <PinOff className="h-3.5 w-3.5" /> : <Pin className="h-3.5 w-3.5" />}
                        </button>
                        <button
                          onClick={() => handleExportRun(run)}
                          className="rounded-full bg-white/[0.06] p-2 text-slate-200 transition hover:bg-white/[0.12]"
                          title="Export"
                        >
                          <Download className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleDeleteRun(run.id)}
                          disabled={!persistenceAvailable || dataSource !== "supabase"}
                          className={`rounded-full bg-red-500/12 p-2 text-red-200 transition hover:bg-red-500/20 ${
                            !persistenceAvailable || dataSource !== "supabase"
                              ? "cursor-not-allowed opacity-50 hover:bg-red-500/12"
                              : ""
                          }`}
                          title="Delete"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredRuns.length === 0 && !isLoading ? (
            <ResearchSubtlePanel className="text-center">
              <History className="mx-auto h-10 w-10 text-slate-500" />
              <p className="mt-4 text-sm text-slate-300">
                {runs.length === 0
                  ? "No persisted or artifact-backed runs were found."
                  : "No runs match the current filters."}
              </p>
            </ResearchSubtlePanel>
          ) : null}

          {isLoading ? <p className="text-sm text-slate-400">Loading run history...</p> : null}
        </ResearchPanel>
      </div>
    </ResearchPageShell>
  );
}

function formatScenarioLabel(scenarioId?: string): string {
  if (!scenarioId) {
    return "Unspecified scenario";
  }

  return scenarioId
    .split("-")
    .map((part) =>
      part.length <= 4 && /^\d+$/.test(part)
        ? part
        : part.charAt(0).toUpperCase() + part.slice(1),
    )
    .join(" ");
}
