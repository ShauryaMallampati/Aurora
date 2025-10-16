"use client";

import { useEffect, useState } from "react";
import { useSimulationStore } from "@/shared/store";
import { MapStage } from "./MapStage";
import { ArrowLeftRight, TrendingUp, TrendingDown, X } from "lucide-react";

interface ComparisonMetrics {
  areaSaved: number;
  timeImprovement: number;
  waterEfficiency: number;
  successRateDelta: number;
}

interface SplitViewComparisonProps {
  onClose?: () => void;
}

export function SplitViewComparison({ onClose }: SplitViewComparisonProps = {}) {
  const ticks = useSimulationStore((state) => state.ticks);
  const [metrics, setMetrics] = useState<ComparisonMetrics>({
    areaSaved: 0,
    timeImprovement: 0,
    waterEfficiency: 0,
    successRateDelta: 0,
  });

  // In a real implementation, this would compare actual PPO vs Hybrid runs
  useEffect(() => {
    if (ticks.length > 10) {
      // Simulated comparison metrics (replace with real data)
      setMetrics({
        areaSaved: 23.4, // % area saved by hybrid
        timeImprovement: 18.2, // % faster containment
        waterEfficiency: 15.7, // % more efficient water use
        successRateDelta: 12.0, // % higher success rate
      });
    }
  }, [ticks]);

  return (
    <div className="flex flex-col h-full">
      {/* Delta KPI Banner */}
      <div className="bg-gradient-to-r from-purple-900 to-blue-900 border-b border-purple-700 px-6 py-3">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <h3 className="text-white font-semibold flex items-center gap-2">
            <ArrowLeftRight className="w-5 h-5" />
            PPO Baseline vs Hybrid Comparison
          </h3>

          <div className="flex items-center gap-6">
            <DeltaMetric
              label="Area Saved"
              value={metrics.areaSaved}
              unit="%"
              positive={true}
            />
            <DeltaMetric
              label="Time Improvement"
              value={metrics.timeImprovement}
              unit="%"
              positive={true}
            />
            <DeltaMetric
              label="Water Efficiency"
              value={metrics.waterEfficiency}
              unit="%"
              positive={true}
            />
            <DeltaMetric
              label="Success Rate"
              value={metrics.successRateDelta}
              unit="%"
              positive={true}
            />
          </div>

          {onClose && (
            <button
              onClick={onClose}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-white rounded-lg flex items-center gap-1.5 text-sm font-medium transition"
            >
              <X className="w-4 h-4" />
              Close
            </button>
          )}
        </div>
      </div>

      {/* Split View Maps */}
      <div className="flex-1 flex">
        {/* Left: PPO Baseline */}
        <div className="flex-1 border-r border-gray-800 relative">
          <div className="absolute top-4 left-4 z-10 bg-blue-600 px-3 py-1 rounded-lg text-white text-sm font-semibold">
            PPO Baseline
          </div>
          <MapStage modelType="ppo" />
        </div>

        {/* Right: Hybrid */}
        <div className="flex-1 relative">
          <div className="absolute top-4 left-4 z-10 bg-purple-600 px-3 py-1 rounded-lg text-white text-sm font-semibold">
            Hybrid (PPO + LLM)
          </div>
          <MapStage modelType="hybrid" />
        </div>
      </div>

      {/* Synchronized Timeline Scrubber */}
      <div className="bg-gray-900 border-t border-gray-800 px-6 py-3">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">Step {ticks.length}</span>
            <input
              type="range"
              min="0"
              max={ticks.length}
              value={ticks.length}
              className="flex-1"
              disabled
            />
            <span className="text-sm text-gray-400">
              {ticks.length > 0 ? `${((ticks.length / 200) * 100).toFixed(0)}%` : "0%"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function DeltaMetric({
  label,
  value,
  unit,
  positive,
}: {
  label: string;
  value: number;
  unit: string;
  positive: boolean;
}) {
  const Icon = positive ? TrendingUp : TrendingDown;
  const colorClass = positive ? "text-green-400" : "text-red-400";

  return (
    <div className="flex items-center gap-2">
      <div className="text-xs text-gray-400">{label}</div>
      <div className={`flex items-center gap-1 font-semibold ${colorClass}`}>
        <Icon className="w-4 h-4" />
        <span>
          {positive ? "+" : ""}
          {value.toFixed(1)}
          {unit}
        </span>
      </div>
    </div>
  );
}
