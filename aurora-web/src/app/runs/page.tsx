"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { History, Play, Pin, PinOff, Search, Filter, Download, Copy, Trash2, Clock, ArrowUpDown } from "lucide-react";

/**
 * Run History & Reproduction Page
 * 
 * Features:
 * - Sortable/filterable run history
 * - "Reproduce Run" to hydrate Mission Control
 * - Pin important runs to Results
 * - Export run configs
 */

interface RunRecord {
  id: string;
  scenario: string;
  model: "ppo" | "hybrid";
  seed: number;
  config: {
    llmCadence?: number;
    maxSteps: number;
    numDrones: number;
  };
  metrics: {
    return: number;
    completionRate: number;
    containmentSteps: number;
    areaburned: number;
  };
  duration: number; // seconds
  timestamp: string;
  pinned: boolean;
  tags: string[];
}

export default function RunHistoryPage() {
  const router = useRouter();
  
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterModel, setFilterModel] = useState<"all" | "ppo" | "hybrid">("all");
  const [sortBy, setSortBy] = useState<"timestamp" | "return" | "completion">("timestamp");
  const [showComparison, setShowComparison] = useState(false);
  const [selectedComparison, setSelectedComparison] = useState<[string, string] | null>(null);
  const [loadingRuns, setLoadingRuns] = useState(true);

  // Load real training runs from API on mount
  useEffect(() => {
    const fetchRealRuns = async () => {
      try {
        const response = await fetch('/api/metrics/training');
        if (!response.ok) throw new Error('Failed to fetch runs');
        
        const data = await response.json();
        
        // Convert real training data to RunRecord format
        if (data.real_fire_results && Array.isArray(data.real_fire_results)) {
          const convertedRuns: RunRecord[] = data.real_fire_results.map((fireResult: any, idx: number) => ({
            id: `run_${fireResult.fire_id || idx}`,
            scenario: fireResult.fire_name || `Fire ${fireResult.fire_id || idx}`,
            model: fireResult.model === 'hybrid' ? 'hybrid' : 'ppo',
            seed: 42, // Default seed
            config: {
              llmCadence: fireResult.model === 'hybrid' ? 50 : undefined,
              maxSteps: 500,
              numDrones: 3
            },
            metrics: {
              return: fireResult.ppo_outcome?.total_return || fireResult.hybrid_outcome?.total_return || 150,
              completionRate: (fireResult.ppo_outcome?.success_rate || fireResult.hybrid_outcome?.success_rate || 0.8) / 100,
              containmentSteps: Math.round(fireResult.ppo_outcome?.containment_steps || fireResult.hybrid_outcome?.containment_steps || 400),
              areaburned: fireResult.ppo_outcome?.area_burned || fireResult.hybrid_outcome?.area_burned || 40
            },
            duration: 300,
            timestamp: fireResult.timestamp || new Date().toISOString(),
            pinned: idx === 0, // Pin the first one
            tags: [fireResult.model, 'phase-c', 'real-data']
          }));
          
          setRuns(convertedRuns);
        } else {
          // Fallback to empty list if no real data
          setRuns([]);
        }
        setLoadingRuns(false);
      } catch (error) {
        console.error('Failed to fetch real runs:', error);
        setRuns([]);
        setLoadingRuns(false);
      }
    };

    fetchRealRuns();
  }, []);

  // Save to localStorage whenever runs change
  useEffect(() => {
    try {
      localStorage.setItem("aurora_run_history", JSON.stringify(runs));
    } catch (error) {
      console.error("Failed to save run history to localStorage:", error);
    }
  }, [runs]);

  const filteredRuns = runs
    .filter((run) => {
      const matchesSearch = run.scenario.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           run.id.includes(searchTerm) ||
                           run.tags.some((tag) => tag.includes(searchTerm.toLowerCase()));
      const matchesModel = filterModel === "all" || run.model === filterModel;
      return matchesSearch && matchesModel;
    })
    .sort((a, b) => {
      if (sortBy === "timestamp") return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      if (sortBy === "return") return b.metrics.return - a.metrics.return;
      if (sortBy === "completion") return b.metrics.completionRate - a.metrics.completionRate;
      return 0;
    });

  const handleReproduceRun = (run: RunRecord) => {
    // TODO: Store config in session storage or Zustand
    sessionStorage.setItem("reproduceRun", JSON.stringify(run));
    router.push("/sim");
  };

  const handleTogglePin = (runId: string) => {
    setRuns(runs.map((run) => (run.id === runId ? { ...run, pinned: !run.pinned } : run)));
  };

  const handleExportRun = (run: RunRecord) => {
    const dataStr = JSON.stringify(run, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${run.id}_config.json`;
    link.click();
  };

  const handleDeleteRun = (runId: string) => {
    setRuns(runs.filter((run) => run.id !== runId));
  };

  const handleCompareRuns = (runId1: string, runId2: string) => {
    setSelectedComparison([runId1, runId2]);
    setShowComparison(true);
    // Store in session for SplitView
    const run1 = runs.find((r) => r.id === runId1);
    const run2 = runs.find((r) => r.id === runId2);
    if (run1 && run2) {
      sessionStorage.setItem("comparisonRuns", JSON.stringify({ ppo: run1, hybrid: run2 }));
      router.push("/sim?view=comparison");
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center gap-3 mb-2">
          <History className="w-8 h-8 text-blue-400" />
          <h1 className="text-3xl font-bold">Run History</h1>
        </div>
        <p className="text-gray-400">
          Complete history of all experiments with reproduction capabilities
        </p>
      </div>

      {/* Controls */}
      <div className="max-w-7xl mx-auto mb-6 flex gap-4">
        {/* Search */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by scenario, run ID, or tags..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-gray-900 border border-gray-800 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none"
          />
        </div>

        {/* Filter by model */}
        <div className="flex items-center gap-2 bg-gray-900 border border-gray-800 rounded-lg px-4">
          <Filter className="w-5 h-5 text-gray-400" />
          <select
            value={filterModel}
            onChange={(e) => setFilterModel(e.target.value as "all" | "ppo" | "hybrid")}
            className="bg-transparent text-white outline-none cursor-pointer"
          >
            <option value="all">All Models</option>
            <option value="ppo">PPO Only</option>
            <option value="hybrid">Hybrid Only</option>
          </select>
        </div>

        {/* Sort */}
        <div className="flex items-center gap-2 bg-gray-900 border border-gray-800 rounded-lg px-4">
          <span className="text-sm text-gray-400">Sort:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as "timestamp" | "return" | "completion")}
            className="bg-transparent text-white outline-none cursor-pointer"
          >
            <option value="timestamp">Recent First</option>
            <option value="return">Highest Return</option>
            <option value="completion">Best Completion</option>
          </select>
        </div>
      </div>

      {/* Results Count */}
      <div className="max-w-7xl mx-auto mb-4 text-sm text-gray-400">
        {loadingRuns ? (
          <span>⏳ Loading real training data...</span>
        ) : (
          <>
            Showing {filteredRuns.length} of {runs.length} runs
            {filteredRuns.filter((r) => r.pinned).length > 0 && (
              <span className="ml-4">
                · {filteredRuns.filter((r) => r.pinned).length} pinned
              </span>
            )}
          </>
        )}
      </div>

      {/* Pinned Runs Quick View */}
      {filteredRuns.filter((r) => r.pinned).length > 0 && (
        <div className="max-w-7xl mx-auto mb-6 bg-gradient-to-r from-yellow-900/20 to-amber-900/20 border border-yellow-800 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <Pin className="w-4 h-4 text-yellow-400 fill-yellow-400" />
            <h3 className="font-semibold text-yellow-300">Pinned Runs</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filteredRuns
              .filter((r) => r.pinned)
              .map((run) => (
                <div key={run.id} className="bg-gray-900 border border-yellow-700 rounded p-3 flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-white truncate">{run.scenario}</p>
                    <p className="text-xs text-gray-400">
                      {run.model.toUpperCase()} • Return: {run.metrics.return.toFixed(1)} • Completion: {(run.metrics.completionRate * 100).toFixed(0)}%
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      const otherPinned = filteredRuns.filter((r) => r.pinned && r.id !== run.id);
                      if (otherPinned.length > 0) {
                        handleCompareRuns(run.id, otherPinned[0].id);
                      }
                    }}
                    className="ml-2 px-2 py-1 bg-purple-600 hover:bg-purple-700 rounded text-xs font-semibold transition whitespace-nowrap"
                  >
                    Compare
                  </button>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Run Table */}
      <div className="max-w-7xl mx-auto bg-gray-900 rounded-lg border border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-800 text-gray-300">
              <tr>
                <th className="text-left py-3 px-4 font-semibold">Run ID</th>
                <th className="text-left py-3 px-4 font-semibold">Scenario</th>
                <th className="text-left py-3 px-4 font-semibold">Model</th>
                <th className="text-right py-3 px-4 font-semibold">Return</th>
                <th className="text-right py-3 px-4 font-semibold">Completion</th>
                <th className="text-right py-3 px-4 font-semibold">Steps</th>
                <th className="text-right py-3 px-4 font-semibold">Duration</th>
                <th className="text-left py-3 px-4 font-semibold">Tags</th>
                <th className="text-center py-3 px-4 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredRuns.map((run) => (
                <tr
                  key={run.id}
                  className="border-b border-gray-800 hover:bg-gray-850 transition"
                >
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      {run.pinned && <Pin className="w-3 h-3 text-yellow-400 fill-yellow-400" />}
                      <span className="font-mono text-xs text-gray-300">{run.id}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4 font-medium">{run.scenario}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        run.model === "hybrid"
                          ? "bg-purple-900 text-purple-300"
                          : "bg-blue-900 text-blue-300"
                      }`}
                    >
                      {run.model.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono">{run.metrics.return.toFixed(1)}</td>
                  <td className="py-3 px-4 text-right font-mono">
                    {(run.metrics.completionRate * 100).toFixed(0)}%
                  </td>
                  <td className="py-3 px-4 text-right font-mono">{run.metrics.containmentSteps}</td>
                  <td className="py-3 px-4 text-right text-gray-400">
                    {Math.floor(run.duration / 60)}m {run.duration % 60}s
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex flex-wrap gap-1">
                      {run.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 bg-gray-800 text-gray-400 rounded text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-center gap-2">
                      <button
                        onClick={() => handleReproduceRun(run)}
                        className="p-1.5 bg-purple-600 hover:bg-purple-700 rounded transition"
                        title="Reproduce run in Mission Control"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleTogglePin(run.id)}
                        className={`p-1.5 rounded transition ${
                          run.pinned
                            ? "bg-yellow-600 hover:bg-yellow-700"
                            : "bg-gray-700 hover:bg-gray-600"
                        }`}
                        title={run.pinned ? "Unpin" : "Pin to Results"}
                      >
                        {run.pinned ? <PinOff className="w-4 h-4" /> : <Pin className="w-4 h-4" />}
                      </button>
                      <button
                        onClick={() => handleExportRun(run)}
                        className="p-1.5 bg-gray-700 hover:bg-gray-600 rounded transition"
                        title="Export config"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteRun(run.id)}
                        className="p-1.5 bg-red-700 hover:bg-red-600 rounded transition"
                        title="Delete run"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Empty state */}
      {filteredRuns.length === 0 && (
        <div className="max-w-7xl mx-auto mt-12 text-center text-gray-500">
          <History className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p className="text-lg">No runs match your filters</p>
          <p className="text-sm mt-2">Try adjusting your search or filters</p>
        </div>
      )}
    </div>
  );
}
