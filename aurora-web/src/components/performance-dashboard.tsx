'use client';

import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Activity, AlertCircle, BarChart3, Download, TrendingUp } from 'lucide-react';

interface ModelPerformance {
  avg_episode_return: number;
  std_return: number;
  success_rate_percent: number;
  avg_decision_latency_ms: number;
  training_time_hours: number;
  num_episodes: number;
  runs: number;
}

interface TrainingMetrics {
  training: {
    total_timesteps: number;
    episodes_completed: number;
    fire_scenarios_trained: number;
    data_source: string;
    weather_source: string;
  };
  model_performance: {
    ppo: ModelPerformance;
    hybrid: ModelPerformance;
  };
  training_trend: Array<{
    step: number;
    ppo_return?: number;
    hybrid_return?: number;
    ppo_completion?: number;
    hybrid_completion?: number;
    timestamp: string;
  }>;
  experiment_runs: Array<{
    id: string;
    model: 'ppo' | 'hybrid';
    phase: string;
    status: string;
    timestamp: string;
    elapsed_seconds: number;
    final_return: number;
    completion_rate: number;
    avg_latency_ms: number;
    episodes: number;
    scenario: string | null;
  }>;
  last_updated: string;
}

export function PerformanceDashboard() {
  const [metrics, setMetrics] = useState<TrainingMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('/api/metrics/training', { cache: 'no-store' });
        if (!response.ok) {
          throw new Error('Failed to fetch metrics');
        }

        const data = (await response.json()) as TrainingMetrics;
        setMetrics(data);
        setError(null);
      } catch (fetchError) {
        console.error('Error fetching metrics:', fetchError);
        setError('Failed to load training metrics');
      } finally {
        setLoading(false);
      }
    };

    void fetchMetrics();
  }, []);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-blue-400 border-t-transparent" />
          <p className="text-gray-400">Loading training metrics...</p>
        </div>
      </div>
    );
  }

  if (error || !metrics) {
    return (
      <div className="rounded-lg border border-yellow-700 bg-yellow-900/20 p-6">
        <div className="flex items-center gap-3">
          <AlertCircle className="h-5 w-5 text-yellow-400" />
          <div>
            <p className="font-semibold text-yellow-300">{error || 'No metrics available'}</p>
            <p className="mt-1 text-sm text-yellow-200">
              Make sure local experiment artifacts exist in the results directory.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const modelRows = [
    {
      label: 'Average return',
      ppo: metrics.model_performance.ppo.avg_episode_return.toFixed(2),
      hybrid: metrics.model_performance.hybrid.avg_episode_return.toFixed(2),
    },
    {
      label: 'Success rate',
      ppo: `${metrics.model_performance.ppo.success_rate_percent.toFixed(1)}%`,
      hybrid: `${metrics.model_performance.hybrid.success_rate_percent.toFixed(1)}%`,
    },
    {
      label: 'Average latency',
      ppo: `${metrics.model_performance.ppo.avg_decision_latency_ms.toFixed(2)} ms`,
      hybrid: `${metrics.model_performance.hybrid.avg_decision_latency_ms.toFixed(2)} ms`,
    },
    {
      label: 'Episodes',
      ppo: metrics.model_performance.ppo.num_episodes.toString(),
      hybrid: metrics.model_performance.hybrid.num_episodes.toString(),
    },
  ];

  return (
    <div className="space-y-8 pb-8">
      <div className="rounded-md border border-slate-700 bg-slate-900 p-6">
        <div className="mb-2 flex items-center gap-3">
          <BarChart3 className="h-6 w-6 text-slate-300" />
          <h2 className="text-2xl font-semibold text-white">Artifact-backed training metrics</h2>
        </div>
        <p className="text-slate-400">
          This dashboard reads the local experiment artifacts and summarizes the currently available PPO
          and hybrid runs.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="Total timesteps"
          value={metrics.training.total_timesteps.toString()}
          note="Across recorded runs"
        />
        <SummaryCard
          title="Episodes"
          value={metrics.training.episodes_completed.toString()}
          note="Parsed from experiment metrics"
        />
        <SummaryCard
          title="Scenarios"
          value={metrics.training.fire_scenarios_trained.toString()}
          note="Unique scenarios present in artifacts"
        />
        <SummaryCard
          title="Last updated"
          value={new Date(metrics.last_updated).toLocaleTimeString()}
          note="Dashboard payload generation time"
        />
      </div>

      <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
        <div className="mb-6 flex items-center gap-2">
          <Activity className="h-5 w-5 text-emerald-400" />
          <h3 className="text-lg font-bold text-white">Model comparison</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700 text-left text-slate-400">
                <th className="px-4 py-3 font-medium">Metric</th>
                <th className="px-4 py-3 font-medium">PPO</th>
                <th className="px-4 py-3 font-medium">Hybrid</th>
              </tr>
            </thead>
            <tbody>
              {modelRows.map((row) => (
                <tr key={row.label} className="border-b border-slate-800 last:border-b-0">
                  <td className="px-4 py-4 text-white">{row.label}</td>
                  <td className="px-4 py-4 font-mono text-sky-300">{row.ppo}</td>
                  <td className="px-4 py-4 font-mono text-emerald-300">{row.hybrid}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
        <div className="mb-6 flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-cyan-400" />
          <h3 className="text-lg font-bold text-white">Latest recorded return trend</h3>
        </div>

        {metrics.training_trend.length > 0 ? (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart
              data={metrics.training_trend}
              margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="step" stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Line
                type="monotone"
                dataKey="ppo_return"
                stroke="#3b82f6"
                dot={{ r: 3 }}
                strokeWidth={2}
                connectNulls
                name="PPO return"
              />
              <Line
                type="monotone"
                dataKey="hybrid_return"
                stroke="#10b981"
                dot={{ r: 3 }}
                strokeWidth={2}
                connectNulls
                name="Hybrid return"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-sm text-slate-400">No artifact metrics were available for the trend chart.</p>
        )}
      </div>

      <div className="rounded-lg border border-slate-700 bg-slate-800 p-6">
        <div className="mb-6 flex items-center gap-2">
          <Activity className="h-5 w-5 text-purple-400" />
          <h3 className="text-lg font-bold text-white">Recent experiment runs</h3>
        </div>

        {metrics.experiment_runs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700 text-left text-slate-400">
                  <th className="px-4 py-3 font-medium">Run</th>
                  <th className="px-4 py-3 font-medium">Model</th>
                  <th className="px-4 py-3 font-medium">Phase</th>
                  <th className="px-4 py-3 font-medium">Return</th>
                  <th className="px-4 py-3 font-medium">Completion</th>
                  <th className="px-4 py-3 font-medium">Latency</th>
                </tr>
              </thead>
              <tbody>
                {metrics.experiment_runs.map((run) => (
                  <tr key={run.id} className="border-b border-slate-800 last:border-b-0">
                    <td className="px-4 py-4 font-mono text-xs text-slate-300">{run.id}</td>
                    <td className="px-4 py-4 text-white">{run.model}</td>
                    <td className="px-4 py-4 text-slate-300">{run.phase}</td>
                    <td className="px-4 py-4 font-mono text-white">{run.final_return.toFixed(2)}</td>
                    <td className="px-4 py-4 font-mono text-white">
                      {(run.completion_rate * 100).toFixed(0)}%
                    </td>
                    <td className="px-4 py-4 font-mono text-slate-300">
                      {run.avg_latency_ms.toFixed(2)} ms
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-400">No recent experiment runs were found.</p>
        )}
      </div>

      <div className="flex justify-center">
        <button
          onClick={() => window.print()}
          className="inline-flex items-center gap-2 rounded-md border border-slate-700 px-6 py-3 text-white transition hover:bg-slate-800"
        >
          <Download className="h-5 w-5" />
          Print / Save Dashboard as PDF
        </button>
      </div>
    </div>
  );
}

function SummaryCard({
  title,
  value,
  note,
}: {
  title: string;
  value: string;
  note: string;
}) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
      <p className="mb-2 text-sm font-medium text-gray-400">{title}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="mt-2 text-xs text-slate-400">{note}</p>
    </div>
  );
}
