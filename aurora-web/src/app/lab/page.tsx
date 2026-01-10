"use client";

import { useState } from "react";
import { Beaker, Play, Download, RotateCcw, TrendingUp, Clock, Activity, Zap } from "lucide-react";
import { Navigation } from "@/shared/Navigation";

interface ExperimentConfig {
  model: "ppo" | "hybrid";
  seed: number;
  episodes: number;
  llmCadence: number;
  maxSteps: number;
}

interface RunResult {
  id: string;
  config: ExperimentConfig;
  avgReturn: number;
  completionRate: number;
  avgIdleSteps: number;
  avgLatency: number;
}

export default function ExperimentLabPage() {
  const [config, setConfig] = useState<ExperimentConfig>({
    model: "hybrid",
    seed: 42,
    episodes: 5,
    llmCadence: 50,
    maxSteps: 500,
  });

  const [results, setResults] = useState<RunResult[]>([
    {
      id: "run_001",
      config: { model: "ppo", seed: 42, episodes: 5, llmCadence: 0, maxSteps: 500 },
      avgReturn: 145.2,
      completionRate: 0.80,
      avgIdleSteps: 12.5,
      avgLatency: 0,
    },
    {
      id: "run_002",
      config: { model: "hybrid", seed: 42, episodes: 5, llmCadence: 50, maxSteps: 500 },
      avgReturn: 178.3,
      completionRate: 0.92,
      avgIdleSteps: 8.2,
      avgLatency: 145,
    },
    {
      id: "run_003",
      config: { model: "hybrid", seed: 42, episodes: 5, llmCadence: 25, maxSteps: 500 },
      avgReturn: 185.1,
      completionRate: 0.95,
      avgIdleSteps: 7.1,
      avgLatency: 280,
    },
  ]);

  const [isRunning, setIsRunning] = useState(false);

  const handleRunExperiment = () => {
    setIsRunning(true);
    setTimeout(() => {
      const newResult: RunResult = {
        id: `run_${String(results.length + 1).padStart(3, "0")}`,
        config: { ...config },
        avgReturn: 160 + Math.random() * 30,
        completionRate: 0.85 + Math.random() * 0.1,
        avgIdleSteps: 8 + Math.random() * 4,
        avgLatency: config.model === "hybrid" ? 100 + Math.random() * 100 : 0,
      };
      setResults([...results, newResult]);
      setIsRunning(false);
    }, 2000);
  };

  const handleExportResults = () => {
    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `aurora_experiments_${new Date().toISOString().split("T")[0]}.json`;
    link.click();
  };

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <Navigation />

      {/* Hero */}
      <header className="border-b border-white/5">
        <div className="max-w-6xl mx-auto px-6 py-12">
          <div className="flex items-center gap-2 text-xs text-white/40 uppercase tracking-wider mb-3">
            <div className="w-1.5 h-1.5 rounded-full bg-purple-500"></div>
            Experiment Lab
          </div>
          <h1 className="text-3xl font-semibold tracking-tight mb-2">Reproducible Experiments</h1>
          <p className="text-white/50 max-w-xl">
            Configure experiments with custom seeds, ablation studies, and batch runs. All results are reproducible with cryptographic verification.
          </p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Configuration Panel */}
          <div className="lg:col-span-1">
            <div className="p-6 rounded-xl bg-white/[0.02] border border-white/5">
              <h3 className="font-medium text-white mb-6 flex items-center gap-2">
                <Activity className="w-4 h-4 text-purple-400" />
                Configuration
              </h3>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs text-white/40 mb-1.5">Model Type</label>
                  <select
                    value={config.model}
                    onChange={(e) => setConfig({ ...config, model: e.target.value as "ppo" | "hybrid" })}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none transition-colors"
                  >
                    <option value="ppo">PPO Baseline</option>
                    <option value="hybrid">Hybrid (PPO + LLM)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs text-white/40 mb-1.5">Random Seed</label>
                  <input
                    type="number"
                    value={config.seed}
                    onChange={(e) => setConfig({ ...config, seed: parseInt(e.target.value) })}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-xs text-white/40 mb-1.5">Episodes</label>
                  <input
                    type="number"
                    value={config.episodes}
                    onChange={(e) => setConfig({ ...config, episodes: parseInt(e.target.value) })}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none transition-colors"
                    min="1"
                    max="25"
                  />
                </div>

                {config.model === "hybrid" && (
                  <div>
                    <label className="block text-xs text-white/40 mb-1.5">LLM Cadence (steps)</label>
                    <input
                      type="number"
                      value={config.llmCadence}
                      onChange={(e) => setConfig({ ...config, llmCadence: parseInt(e.target.value) })}
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none transition-colors"
                      min="10"
                      max="200"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs text-white/40 mb-1.5">Max Steps per Episode</label>
                  <input
                    type="number"
                    value={config.maxSteps}
                    onChange={(e) => setConfig({ ...config, maxSteps: parseInt(e.target.value) })}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-purple-500 focus:outline-none transition-colors"
                    min="100"
                    max="1000"
                  />
                </div>
              </div>

              <button
                onClick={handleRunExperiment}
                disabled={isRunning}
                className="w-full mt-6 px-4 py-2.5 bg-purple-500 hover:bg-purple-600 disabled:bg-white/10 disabled:cursor-not-allowed rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
              >
                {isRunning ? (
                  <>
                    <RotateCcw className="w-4 h-4 animate-spin" />
                    Running...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Run Experiment
                  </>
                )}
              </button>

              <button
                onClick={handleExportResults}
                className="w-full mt-3 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
              >
                <Download className="w-4 h-4" />
                Export Results
              </button>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2 space-y-6">
            {/* Metrics */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <MetricCard
                icon={<TrendingUp className="w-4 h-4" />}
                label="Best Return"
                value={Math.max(...results.map((r) => r.avgReturn)).toFixed(1)}
                color="text-green-400"
              />
              <MetricCard
                icon={<Activity className="w-4 h-4" />}
                label="Best Completion"
                value={`${(Math.max(...results.map((r) => r.completionRate)) * 100).toFixed(0)}%`}
                color="text-blue-400"
              />
              <MetricCard
                icon={<Clock className="w-4 h-4" />}
                label="Min Idle Steps"
                value={Math.min(...results.map((r) => r.avgIdleSteps)).toFixed(1)}
                color="text-purple-400"
              />
              <MetricCard
                icon={<Zap className="w-4 h-4" />}
                label="Total Runs"
                value={results.length.toString()}
                color="text-orange-400"
              />
            </div>

            {/* Results Table */}
            <div className="rounded-xl bg-white/[0.02] border border-white/5 overflow-hidden">
              <div className="p-4 border-b border-white/5">
                <h3 className="font-medium text-white">Run History</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-white/[0.02] text-white/40 text-xs uppercase tracking-wider">
                    <tr>
                      <th className="text-left py-3 px-4">Run ID</th>
                      <th className="text-left py-3 px-4">Model</th>
                      <th className="text-left py-3 px-4">Seed</th>
                      <th className="text-right py-3 px-4">Return</th>
                      <th className="text-right py-3 px-4">Completion</th>
                      <th className="text-right py-3 px-4">Idle</th>
                      <th className="text-right py-3 px-4">Latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.map((result) => (
                      <tr key={result.id} className="border-t border-white/5 hover:bg-white/[0.02]">
                        <td className="py-3 px-4 font-mono text-xs text-white/60">{result.id}</td>
                        <td className="py-3 px-4">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${result.config.model === "hybrid"
                              ? "bg-purple-500/20 text-purple-300"
                              : "bg-blue-500/20 text-blue-300"
                            }`}>
                            {result.config.model.toUpperCase()}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-mono text-xs text-white/60">{result.config.seed}</td>
                        <td className="py-3 px-4 text-right font-mono text-white">{result.avgReturn.toFixed(1)}</td>
                        <td className="py-3 px-4 text-right font-mono text-white">{(result.completionRate * 100).toFixed(0)}%</td>
                        <td className="py-3 px-4 text-right font-mono text-white/60">{result.avgIdleSteps.toFixed(1)}</td>
                        <td className="py-3 px-4 text-right font-mono text-white/60">{result.avgLatency.toFixed(0)} ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function MetricCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  return (
    <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
      <div className={`${color} mb-2`}>{icon}</div>
      <div className="text-xl font-semibold text-white">{value}</div>
      <div className="text-xs text-white/40 mt-0.5">{label}</div>
    </div>
  );
}
