"use client";

import { useState } from "react";
import { Beaker, Play, Download, RotateCcw, TrendingUp, Clock, Activity, Zap } from "lucide-react";
import { Navigation } from "@/shared/Navigation";

/**
 * Experiment Lab - Reproducibility & Ablation Studies
 * 
 * Features:
 * - Run picker with seed/config selectors
 * - Batch run controls
 * - Four key charts: Return, Completion, Idle steps, Latency
 * - Export results
 */

interface ExperimentConfig {
  model: "ppo" | "hybrid";
  seed: number;
  episodes: number;
  llmCadence: number;
  maxSteps: number;
  noise: boolean;
}

interface RunResult {
  id: string;
  config: ExperimentConfig;
  avgReturn: number;
  completionRate: number;
  avgIdleSteps: number;
  avgLatency: number;
  timestamp: string;
}

export default function ExperimentLabPage() {
  const [config, setConfig] = useState<ExperimentConfig>({
    model: "hybrid",
    seed: 42,
    episodes: 5,
    llmCadence: 50,
    maxSteps: 500,
    noise: false,
  });

  const [results, setResults] = useState<RunResult[]>([
    // Example data for visualization
    {
      id: "run_001",
      config: { model: "ppo", seed: 42, episodes: 5, llmCadence: 0, maxSteps: 500, noise: false },
      avgReturn: 145.2,
      completionRate: 0.80,
      avgIdleSteps: 12.5,
      avgLatency: 0,
      timestamp: "2025-10-15T14:30:00Z",
    },
    {
      id: "run_002",
      config: { model: "hybrid", seed: 42, episodes: 5, llmCadence: 50, maxSteps: 500, noise: false },
      avgReturn: 178.3,
      completionRate: 0.92,
      avgIdleSteps: 8.2,
      avgLatency: 145,
      timestamp: "2025-10-15T15:45:00Z",
    },
    {
      id: "run_003",
      config: { model: "hybrid", seed: 42, episodes: 5, llmCadence: 25, maxSteps: 500, noise: false },
      avgReturn: 185.1,
      completionRate: 0.95,
      avgIdleSteps: 7.1,
      avgLatency: 280,
      timestamp: "2025-10-15T16:20:00Z",
    },
  ]);

  const [isRunning, setIsRunning] = useState(false);

  const handleRunExperiment = () => {
    setIsRunning(true);
    // TODO: Implement actual API call to backend
    setTimeout(() => {
      const newResult: RunResult = {
        id: `run_${String(results.length + 1).padStart(3, "0")}`,
        config: { ...config },
        avgReturn: 160 + Math.random() * 30,
        completionRate: 0.85 + Math.random() * 0.1,
        avgIdleSteps: 8 + Math.random() * 4,
        avgLatency: config.model === "hybrid" ? 100 + Math.random() * 100 : 0,
        timestamp: new Date().toISOString(),
      };
      setResults([...results, newResult]);
      setIsRunning(false);
    }, 3000);
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
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Navigation */}
      <Navigation />
      
      <div className="p-8">
        {/* Header */}
        <div className="max-w-7xl mx-auto mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Beaker className="w-8 h-8 text-purple-400" />
            <h1 className="text-3xl font-bold">Experiment Lab</h1>
          </div>
          <p className="text-gray-400">
            Reproducible experiments with configurable seeds, ablations, and batch runs
          </p>
        </div>

        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Configuration Panel */}
        <div className="lg:col-span-1 space-y-6">
          {/* Model Selection */}
          <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-400" />
              Model Configuration
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Model Type</label>
                <select
                  value={config.model}
                  onChange={(e) => setConfig({ ...config, model: e.target.value as "ppo" | "hybrid" })}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
                >
                  <option value="ppo">PPO Baseline</option>
                  <option value="hybrid">Hybrid (PPO + LLM)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Random Seed</label>
                <input
                  type="number"
                  value={config.seed}
                  onChange={(e) => setConfig({ ...config, seed: parseInt(e.target.value) })}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-2">Episodes</label>
                <input
                  type="number"
                  value={config.episodes}
                  onChange={(e) => setConfig({ ...config, episodes: parseInt(e.target.value) })}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
                  min="1"
                  max="25"
                />
              </div>

              {config.model === "hybrid" && (
                <div>
                  <label className="block text-sm text-gray-400 mb-2">LLM Cadence (steps)</label>
                  <input
                    type="number"
                    value={config.llmCadence}
                    onChange={(e) => setConfig({ ...config, llmCadence: parseInt(e.target.value) })}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
                    min="10"
                    max="200"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm text-gray-400 mb-2">Max Steps per Episode</label>
                <input
                  type="number"
                  value={config.maxSteps}
                  onChange={(e) => setConfig({ ...config, maxSteps: parseInt(e.target.value) })}
                  className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white"
                  min="100"
                  max="1000"
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.noise}
                  onChange={(e) => setConfig({ ...config, noise: e.target.checked })}
                  className="w-4 h-4"
                />
                <label className="text-sm text-gray-400">Add observation noise (robustness test)</label>
              </div>
            </div>

            {/* Run Button */}
            <button
              onClick={handleRunExperiment}
              disabled={isRunning}
              className="w-full mt-6 px-4 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed rounded-lg font-semibold flex items-center justify-center gap-2 transition"
            >
              {isRunning ? (
                <>
                  <RotateCcw className="w-5 h-5 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Run Experiment
                </>
              )}
            </button>

            <button
              onClick={handleExportResults}
              className="w-full mt-3 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg font-medium flex items-center justify-center gap-2 transition"
            >
              <Download className="w-4 h-4" />
              Export Results
            </button>
          </div>
        </div>

        {/* Right: Results & Charts */}
        <div className="lg:col-span-2 space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              icon={<TrendingUp className="w-5 h-5" />}
              label="Best Return"
              value={Math.max(...results.map((r) => r.avgReturn)).toFixed(1)}
              color="text-green-400"
            />
            <MetricCard
              icon={<Activity className="w-5 h-5" />}
              label="Best Completion"
              value={`${(Math.max(...results.map((r) => r.completionRate)) * 100).toFixed(0)}%`}
              color="text-blue-400"
            />
            <MetricCard
              icon={<Clock className="w-5 h-5" />}
              label="Min Idle Steps"
              value={Math.min(...results.map((r) => r.avgIdleSteps)).toFixed(1)}
              color="text-purple-400"
            />
            <MetricCard
              icon={<Zap className="w-5 h-5" />}
              label="Total Runs"
              value={results.length.toString()}
              color="text-yellow-400"
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartCard title="Average Return" data={results} yKey="avgReturn" color="rgb(34, 197, 94)" />
            <ChartCard title="Completion Rate" data={results} yKey="completionRate" color="rgb(59, 130, 246)" isPercent />
            <ChartCard title="Idle Steps" data={results} yKey="avgIdleSteps" color="rgb(168, 85, 247)" />
            <ChartCard title="LLM Latency (ms)" data={results} yKey="avgLatency" color="rgb(234, 179, 8)" />
          </div>

          {/* Results Table */}
          <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
            <h3 className="font-semibold mb-4">Run History</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-gray-400 border-b border-gray-800">
                  <tr>
                    <th className="text-left py-2 px-3">Run ID</th>
                    <th className="text-left py-2 px-3">Model</th>
                    <th className="text-left py-2 px-3">Seed</th>
                    <th className="text-right py-2 px-3">Return</th>
                    <th className="text-right py-2 px-3">Completion</th>
                    <th className="text-right py-2 px-3">Idle</th>
                    <th className="text-right py-2 px-3">Latency</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((result) => (
                    <tr key={result.id} className="border-b border-gray-800 hover:bg-gray-850">
                      <td className="py-3 px-3 font-mono text-xs">{result.id}</td>
                      <td className="py-3 px-3">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          result.config.model === "hybrid" ? "bg-purple-900 text-purple-300" : "bg-blue-900 text-blue-300"
                        }`}>
                          {result.config.model.toUpperCase()}
                        </span>
                      </td>
                                            <td className="py-3 px-3 font-mono text-xs">{result.config.seed}</td>
                      <td className="py-3 px-3 text-right font-mono">{result.avgReturn.toFixed(1)}</td>
                      <td className="py-3 px-3 text-right font-mono">{(result.completionRate * 100).toFixed(0)}%</td>
                      <td className="py-3 px-3 text-right font-mono">{result.avgIdleSteps.toFixed(1)}</td>
                      <td className="py-3 px-3 text-right font-mono">{result.avgLatency.toFixed(0)} ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  return (
    <div className="bg-gray-900 rounded-lg p-4 border border-gray-800">
      <div className={`${color} mb-2`}>{icon}</div>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs text-gray-400 mt-1">{label}</div>
    </div>
  );
}

function ChartCard({ 
  title, 
  data, 
  yKey, 
  color, 
  isPercent = false 
}: { 
  title: string; 
  data: RunResult[]; 
  yKey: keyof RunResult; 
  color: string;
  isPercent?: boolean;
}) {
  const values = data.map((r) => r[yKey] as number);
  const max = Math.max(...values);
  const min = Math.min(...values);

  return (
    <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
      <h3 className="font-semibold mb-4">{title}</h3>
      <div className="relative h-32">
        {/* Simple bar chart */}
        <div className="flex items-end justify-between h-full gap-1">
          {values.map((value, idx) => {
            const height = max > 0 ? (value / max) * 100 : 0;
            return (
              <div
                key={idx}
                className="flex-1 rounded-t transition-all hover:opacity-80"
                style={{
                  height: `${height}%`,
                  backgroundColor: color,
                  minHeight: "4px",
                }}
                title={`Run ${idx + 1}: ${isPercent ? (value * 100).toFixed(1) + "%" : value.toFixed(1)}`}
              />
            );
          })}
        </div>
      </div>
      <div className="mt-4 flex justify-between text-xs text-gray-400">
        <span>Min: {isPercent ? (min * 100).toFixed(1) + "%" : min.toFixed(1)}</span>
        <span>Max: {isPercent ? (max * 100).toFixed(1) + "%" : max.toFixed(1)}</span>
      </div>
    </div>
  );
}
