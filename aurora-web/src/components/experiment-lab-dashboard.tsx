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
  const [selectedMode, setSelectedMode] = useState<'ppo' | 'hybrid'>('hybrid');
  const [selectedPhase, setSelectedPhase] = useState<string>('quick');
  const [trainingData, setTrainingData] = useState<ExperimentMetrics[]>([]);
  const [realMetricsLoaded, setRealMetricsLoaded] = useState(false);
  const [loadingError, setLoadingError] = useState<string | null>(null);

  // Fetch real training metrics on component mount
  useEffect(() => {
    const fetchRealMetrics = async () => {
      try {
        const response = await fetch('/api/metrics/training');
        if (!response.ok) throw new Error('Failed to fetch metrics');
        
        const data = await response.json();
        
        // Convert real training data to ExperimentMetrics format
        if (data.training_trend && Array.isArray(data.training_trend)) {
          const convertedMetrics: ExperimentMetrics[] = data.training_trend.map((point: any) => ({
            step: point.step || 0,
            episode_return: selectedMode === 'hybrid' 
              ? (point.hybrid_return || point.episode_return || 0)
              : (point.ppo_return || point.episode_return || 0),
            completion_rate: (point.hybrid_success_rate || point.ppo_success_rate || 0) / 100,
            idle_steps: Math.round((point.idle_steps || 0)),
            llm_latency_ms: (point.llm_latency_ms || 0),
            timestamp: point.timestamp || new Date().toISOString(),
          }));
          
          setTrainingData(convertedMetrics);
          setRealMetricsLoaded(true);
          setLoadingError(null);
        }
      } catch (error) {
        console.error('Failed to fetch real metrics:', error);
        setLoadingError('Unable to load real training data');
        setRealMetricsLoaded(true);
      }
    };

    fetchRealMetrics();
  }, [selectedMode]);

  // Calculate statistics from real training data
  const stats = {
    avgReturn: trainingData.length > 0 ? (trainingData.reduce((sum, m) => sum + m.episode_return, 0) / trainingData.length).toFixed(2) : '0',
    avgCompletion: trainingData.length > 0 ? (trainingData.reduce((sum, m) => sum + m.completion_rate, 0) / trainingData.length * 100).toFixed(1) : '0',
    avgIdle: trainingData.length > 0 ? (trainingData.reduce((sum, m) => sum + m.idle_steps, 0) / trainingData.length).toFixed(0) : '0',
    avgLatency: trainingData.length > 0 ? (trainingData.reduce((sum, m) => sum + m.llm_latency_ms, 0) / trainingData.length).toFixed(2) : '0',
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
            className="w-full bg-slate-800 border border-slate-700 text-white rounded px-3 py-2 hover:border-slate-600"
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
            className="w-full bg-slate-800 border border-slate-700 text-white rounded px-3 py-2 hover:border-slate-600"
          >
            <option value="quick">Quick (100 steps)</option>
            <option value="phase_a">Phase A (57K steps, ~1-2h)</option>
            <option value="phase_b">Phase B (147K steps, ~3-4h)</option>
            <option value="phase_c">Phase C (196K steps, ~4-5h)</option>
            <option value="full">Full (401K steps, ~8-12h)</option>
          </select>
        </div>

        {/* Data Status */}
        <div className="bg-slate-800 border border-slate-700 rounded px-4 py-2 flex items-center">
          {!realMetricsLoaded ? (
            <span className="text-yellow-400 text-sm">⏳ Loading real metrics...</span>
          ) : loadingError ? (
            <span className="text-red-400 text-sm">⚠️ {loadingError}</span>
          ) : (
            <span className="text-emerald-400 text-sm">✓ Real data loaded • {trainingData.length} data points</span>
          )}
        </div>
      </div>

      {/* Data Summary */}
      {realMetricsLoaded && !loadingError && trainingData.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Mode:</span>
              <span className="ml-2 font-semibold text-white capitalize">{selectedMode}</span>
            </div>
            <div>
              <span className="text-gray-400">Data Source:</span>
              <span className="ml-2 font-semibold text-emerald-400">Aurora Training</span>
            </div>
            <div>
              <span className="text-gray-400">Total Steps:</span>
              <span className="ml-2 font-semibold text-white">{(trainingData[trainingData.length - 1]?.step || 0).toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-400">Data Points:</span>
              <span className="ml-2 font-semibold text-white">{trainingData.length}</span>
            </div>
          </div>
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
      {trainingData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 1. Episode Return Trend */}
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Episode Return Trend
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={trainingData}>
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
                data={trainingData.slice(-20)} // Last 20 points for clarity
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
              <LineChart data={trainingData}>
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
              <AreaChart data={trainingData}>
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
      {trainingData.length === 0 && realMetricsLoaded && (
        <div className="bg-slate-800 border border-slate-700 border-dashed rounded-lg p-12 text-center">
          <Zap className="w-12 h-12 text-gray-600 mx-auto mb-4 opacity-50" />
          <p className="text-gray-400 mb-4">No training data available</p>
          <p className="text-sm text-gray-500">
            Check if the AURORA training pipeline has generated metrics data
          </p>
        </div>
      )}
    </div>
  );
}
