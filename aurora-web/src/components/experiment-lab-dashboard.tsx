'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Area,
  AreaChart,
} from 'recharts';
import { Play, Pause, RotateCcw, Download, Zap, TrendingUp } from 'lucide-react';

interface ExperimentMetrics {
  step: number;
  episode_return: number;
  completion_rate: number;
  idle_steps: number;
  llm_latency_ms: number;
  timestamp: string;
}

interface ExperimentStatus {
  id: string;
  mode: 'ppo' | 'hybrid';
  phase: string;
  status: 'starting' | 'running' | 'completed' | 'failed';
  start_time: string;
  elapsed_seconds: number;
  metrics: ExperimentMetrics[];
  current_step?: number;
  total_steps?: number;
  message: string;
}

export function ExperimentLabDashboard() {
  const [experimentId, setExperimentId] = useState<string | null>(null);
  const [selectedMode, setSelectedMode] = useState<'ppo' | 'hybrid'>('hybrid');
  const [selectedPhase, setSelectedPhase] = useState<string>('quick');
  const [status, setStatus] = useState<ExperimentStatus | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [metrics, setMetrics] = useState<ExperimentMetrics[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Polling interval (2 seconds)
  const POLL_INTERVAL = 2000;

  // Start experiment
  const handleStartExperiment = useCallback(async () => {
    try {
      const response = await fetch('/api/run_experiment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: selectedMode,
          phase: selectedPhase,
        }),
      });

      const data = await response.json();
      setExperimentId(data.id);
      setStatus(data);
      setIsRunning(true);
      setAutoRefresh(true);
    } catch (error) {
      console.error('Failed to start experiment:', error);
      alert('Failed to start experiment');
    }
  }, [selectedMode, selectedPhase]);

  // Fetch experiment status
  const fetchExperimentStatus = useCallback(async () => {
    if (!experimentId) return;

    try {
      const response = await fetch(`/api/run_experiment?id=${experimentId}`);
      const data: ExperimentStatus = await response.json();

      setStatus(data);
      setMetrics(data.metrics || []);

      // Stop polling when experiment completes
      if (data.status === 'completed' || data.status === 'failed') {
        setIsRunning(false);
        setAutoRefresh(false);
      }
    } catch (error) {
      console.error('Failed to fetch status:', error);
    }
  }, [experimentId]);

  // Auto-refresh polling
  useEffect(() => {
    if (!autoRefresh || !experimentId) return;

    const interval = setInterval(fetchExperimentStatus, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [autoRefresh, experimentId, fetchExperimentStatus]);

  // Calculate statistics
  const stats = {
    avgReturn: metrics.length > 0 ? (metrics.reduce((sum, m) => sum + m.episode_return, 0) / metrics.length).toFixed(2) : '0',
    avgCompletion: metrics.length > 0 ? (metrics.reduce((sum, m) => sum + m.completion_rate, 0) / metrics.length * 100).toFixed(1) : '0',
    avgIdle: metrics.length > 0 ? (metrics.reduce((sum, m) => sum + m.idle_steps, 0) / metrics.length).toFixed(0) : '0',
    avgLatency: metrics.length > 0 ? (metrics.reduce((sum, m) => sum + m.llm_latency_ms, 0) / metrics.length).toFixed(2) : '0',
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 border border-slate-700 rounded-lg p-6">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
          <Zap className="w-8 h-8 text-yellow-400" />
          Experiment Lab
        </h1>
        <p className="text-gray-400">Run live training experiments and monitor real-time metrics</p>
      </div>

      {/* Control Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Mode Selection */}
        <div>
          <label className="block text-sm font-semibold text-white mb-2">Training Mode</label>
          <select
            value={selectedMode}
            onChange={(e) => setSelectedMode(e.target.value as 'ppo' | 'hybrid')}
            disabled={isRunning}
            className="w-full bg-slate-800 border border-slate-700 text-white rounded px-3 py-2 hover:border-slate-600 disabled:opacity-50"
          >
            <option value="ppo">PPO Baseline</option>
            <option value="hybrid">Hybrid PPO+LLM</option>
          </select>
        </div>

        {/* Phase Selection */}
        <div>
          <label className="block text-sm font-semibold text-white mb-2">Training Phase</label>
          <select
            value={selectedPhase}
            onChange={(e) => setSelectedPhase(e.target.value)}
            disabled={isRunning}
            className="w-full bg-slate-800 border border-slate-700 text-white rounded px-3 py-2 hover:border-slate-600 disabled:opacity-50"
          >
            <option value="quick">Quick (100 steps)</option>
            <option value="phase_a">Phase A (57K steps, ~1-2h)</option>
            <option value="phase_b">Phase B (147K steps, ~3-4h)</option>
            <option value="phase_c">Phase C (196K steps, ~4-5h)</option>
            <option value="full">Full (401K steps, ~8-12h)</option>
          </select>
        </div>

        {/* Action Buttons */}
        <div>
          <label className="block text-sm font-semibold text-white mb-2">Actions</label>
          <div className="flex gap-2">
            <button
              onClick={handleStartExperiment}
              disabled={isRunning}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-600 text-white px-3 py-2 rounded font-semibold flex items-center justify-center gap-2 transition"
            >
              <Play className="w-4 h-4" />
              {isRunning ? 'Running...' : 'Start'}
            </button>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              disabled={!isRunning}
              className={`flex-1 ${
                autoRefresh ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-600'
              } text-white px-3 py-2 rounded font-semibold flex items-center justify-center gap-2 transition disabled:opacity-50`}
            >
              {autoRefresh ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              {autoRefresh ? 'Pause' : 'Resume'}
            </button>
          </div>
        </div>
      </div>

      {/* Status Bar */}
      {status && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Mode:</span>
              <span className="ml-2 font-semibold text-white">{status.mode.toUpperCase()}</span>
            </div>
            <div>
              <span className="text-gray-400">Phase:</span>
              <span className="ml-2 font-semibold text-white">{status.phase}</span>
            </div>
            <div>
              <span className="text-gray-400">Status:</span>
              <span
                className={`ml-2 font-semibold ${
                  status.status === 'running'
                    ? 'text-emerald-400'
                    : status.status === 'completed'
                    ? 'text-blue-400'
                    : status.status === 'failed'
                    ? 'text-red-400'
                    : 'text-yellow-400'
                }`}
              >
                {status.status.toUpperCase()}
              </span>
            </div>
            <div>
              <span className="text-gray-400">Time:</span>
              <span className="ml-2 font-semibold text-white">{Math.floor(status.elapsed_seconds / 60)}m</span>
            </div>
          </div>
          {metrics.length > 0 && (
            <div className="mt-3 text-xs text-gray-400">
              {metrics.length} metrics collected • Latest step: {metrics[metrics.length - 1]?.step}
            </div>
          )}
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Avg Return', value: stats.avgReturn, color: 'text-blue-400', icon: TrendingUp },
          {
            label: 'Avg Completion',
            value: `${stats.avgCompletion}%`,
            color: 'text-emerald-400',
            icon: TrendingUp,
          },
          { label: 'Avg Idle Steps', value: stats.avgIdle, color: 'text-yellow-400', icon: TrendingUp },
          { label: 'Avg LLM Latency', value: `${stats.avgLatency}ms`, color: 'text-purple-400', icon: TrendingUp },
        ].map((stat) => (
          <div key={stat.label} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400 text-sm">{stat.label}</span>
              <stat.icon className={`w-4 h-4 ${stat.color}`} />
            </div>
            <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Charts Grid */}
      {metrics.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 1. Episode Return Trend */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Episode Return Trend
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={metrics}>
                <defs>
                  <linearGradient id="colorReturn" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="step"
                  stroke="#94a3b8"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: '#94a3b8' }}
                  formatter={(value: any) => [value.toFixed(2), 'Return']}
                />
                <Area
                  type="monotone"
                  dataKey="episode_return"
                  stroke="#3b82f6"
                  fillOpacity={1}
                  fill="url(#colorReturn)"
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* 2. Completion Rate (Bar Chart) */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Completion Rate
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart
                data={metrics.slice(-20)} // Last 20 points for clarity
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="step" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} domain={[0, 1]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: '#94a3b8' }}
                  formatter={(value: any) => [(value * 100).toFixed(1) + '%', 'Rate']}
                />
                <Bar dataKey="completion_rate" fill="#10b981" radius={[4, 4, 0, 0]} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* 3. Idle Steps (Line Chart) */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Idle Steps Progression
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="step"
                  stroke="#94a3b8"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: '#94a3b8' }}
                  formatter={(value: any) => [value, 'Steps']}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="idle_steps"
                  stroke="#f59e0b"
                  dot={false}
                  isAnimationActive={false}
                  name="Idle Steps"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* 4. LLM Latency (Box Plot / Area Chart) */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              LLM Strategy Latency (ms)
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={metrics}>
                <defs>
                  <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="step"
                  stroke="#94a3b8"
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} label={{ value: 'ms', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: '#94a3b8' }}
                  formatter={(value: any) => [value.toFixed(2) + 'ms', 'Latency']}
                />
                <Area
                  type="monotone"
                  dataKey="llm_latency_ms"
                  stroke="#a855f7"
                  fillOpacity={1}
                  fill="url(#colorLatency)"
                  dot={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Empty State */}
      {metrics.length === 0 && !isRunning && (
        <div className="bg-slate-800 border border-slate-700 border-dashed rounded-lg p-12 text-center">
          <Zap className="w-12 h-12 text-gray-600 mx-auto mb-4 opacity-50" />
          <p className="text-gray-400 mb-4">No experiments running</p>
          <p className="text-sm text-gray-500">
            Select a training mode and phase, then click "Start" to begin a new experiment
          </p>
        </div>
      )}
    </div>
  );
}
