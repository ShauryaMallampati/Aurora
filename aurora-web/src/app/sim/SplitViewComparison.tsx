"use client";

import { useEffect, useState, useCallback } from "react";
import { useSimulationStore } from "@/shared/store";
import { MapStage } from "./MapStage";
import { ArrowLeftRight, TrendingUp, TrendingDown, X, Loader2 } from "lucide-react";
import { 
  findMatchingRuns,
  calculateComparisonMetrics,
  getMaxSteps,
  type ComparisonMetrics as ComparisonMetricsType
} from "@/shared/runsDataLoader";

interface SplitViewComparisonProps {
  onClose?: () => void;
}

export function SplitViewComparison({ onClose }: SplitViewComparisonProps = {}) {
  const {
    ppoRun,
    hybridRun,
    comparisonMetrics: storedMetrics,
    currentComparisonStep,
    setCurrentComparisonStep,
    setComparisonRuns,
  } = useSimulationStore();

  const [metrics, setMetrics] = useState<ComparisonMetricsType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [maxSteps, setMaxSteps] = useState(0);
  const [animatingMetrics, setAnimatingMetrics] = useState<{
    areaSavedPercent: number;
    timeImprovementPercent: number;
    waterEfficiencyPercent: number;
    successRateDelta: number;
  } | null>(null);

  // Init runs on mount
  useEffect(() => {
    const initializeRuns = async () => {
      try {
        setIsLoading(true);
        
        // Try store first
        if (ppoRun && hybridRun) {
          const computed = calculateComparisonMetrics(ppoRun, hybridRun);
          setMetrics(computed);
          setMaxSteps(getMaxSteps(ppoRun, hybridRun));
          setError(null);
          setAnimatingMetrics({
            areaSavedPercent: computed.areaSavedPercent,
            timeImprovementPercent: computed.timeImprovementPercent,
            waterEfficiencyPercent: computed.waterEfficiencyPercent,
            successRateDelta: computed.successRateDelta,
          });
        } else {
          const matchedRuns = await findMatchingRuns();
          if (!matchedRuns) {
            throw new Error('No matching PPO/Hybrid runs are available for comparison yet.');
          }

          const computed = calculateComparisonMetrics(matchedRuns.ppo, matchedRuns.hybrid);
          setComparisonRuns(matchedRuns.ppo, matchedRuns.hybrid, computed);
          setMetrics(computed);
          setMaxSteps(getMaxSteps(matchedRuns.ppo, matchedRuns.hybrid));
          setError(null);
          setAnimatingMetrics({
            areaSavedPercent: computed.areaSavedPercent,
            timeImprovementPercent: computed.timeImprovementPercent,
            waterEfficiencyPercent: computed.waterEfficiencyPercent,
            successRateDelta: computed.successRateDelta,
          });
        }
      } catch (error) {
        console.error('Error initializing comparison runs:', error);
        setError((error as Error).message);
      } finally {
        setIsLoading(false);
      }
    };

    initializeRuns();
  }, [ppoRun, hybridRun, setComparisonRuns]);

  // Use stored metrics as fallback
  const displayMetrics = metrics || storedMetrics;

  const handleStepChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentComparisonStep(parseInt(event.target.value));
  }, [setCurrentComparisonStep]);

  if (isLoading || !displayMetrics) {
    return (
      <div className="flex flex-col h-full bg-gray-950">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            {error ? null : <Loader2 className="w-12 h-12 animate-spin text-purple-500 mx-auto mb-4" />}
            <p className="text-gray-400">{error || 'Loading PPO vs Hybrid comparison...'}</p>
          </div>
        </div>
      </div>
    );
  }

  const progressPercent = maxSteps > 0 ? (currentComparisonStep / maxSteps) * 100 : 0;

  return (
    <div className="flex flex-col h-full bg-gray-950">
      {/* Delta KPI Banner - Clean dark design */}
      <div className="bg-[#0f0f10] border-b border-white/10 px-6 py-4">
        <div className="flex items-center justify-between max-w-full">
          <h3 className="text-white font-bold flex items-center gap-3 text-lg">
            <ArrowLeftRight className="w-6 h-6 text-purple-400" />
            PPO Baseline vs Hybrid (PPO + LLM) Comparison
          </h3>

          {onClose && (
            <button
              onClick={onClose}
              className="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white rounded-lg flex items-center gap-1.5 text-sm font-medium transition"
            >
              <X className="w-4 h-4" />
              Close
            </button>
          )}
        </div>

        {/* Metrics Display */}
        <div className="mt-4 grid grid-cols-4 gap-4">
          <DeltaMetric
            label="Area Saved"
            value={animatingMetrics?.areaSavedPercent || 0}
            unit="%"
            positive={true}
            subtitle="Less burned area"
          />
          <DeltaMetric
            label="Time Improvement"
            value={animatingMetrics?.timeImprovementPercent || 0}
            unit="%"
            positive={true}
            subtitle="Faster containment"
          />
          <DeltaMetric
            label="Water Efficiency"
            value={animatingMetrics?.waterEfficiencyPercent || 0}
            unit="%"
            positive={true}
            subtitle="Less water used"
          />
          <DeltaMetric
            label="Success Rate"
            value={animatingMetrics?.successRateDelta || 0}
            unit="pp"
            positive={true}
            subtitle="Percentage points"
          />
        </div>
      </div>

      {/* Split View Maps */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: PPO Baseline */}
        <div className="flex-1 border-r border-gray-800 relative overflow-hidden">
          <div className="absolute top-4 left-4 z-20 bg-blue-600/90 px-4 py-2 rounded-lg text-white text-sm font-bold shadow-lg">
            <div>PPO Baseline</div>
            <div className="text-xs text-blue-200">Seed: {displayMetrics.ppoRun.seed}</div>
          </div>
          {ppoRun && <MapStage modelType="ppo" currentStep={currentComparisonStep} />}
        </div>

        {/* Right: Hybrid */}
        <div className="flex-1 relative overflow-hidden">
          <div className="absolute top-4 left-4 z-20 bg-purple-600/90 px-4 py-2 rounded-lg text-white text-sm font-bold shadow-lg">
            <div>Hybrid (PPO + LLM)</div>
            <div className="text-xs text-purple-200">Seed: {displayMetrics.hybridRun.seed}</div>
          </div>
          {hybridRun && <MapStage modelType="hybrid" currentStep={currentComparisonStep} />}
        </div>
      </div>

      {/* Synchronized Timeline Scrubber */}
      <div className="bg-gray-900 border-t border-gray-800 px-6 py-4">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-300 w-12">Step</span>
            <span className="text-sm font-mono bg-gray-800 px-2 py-1 rounded text-purple-300">
              {currentComparisonStep} / {maxSteps}
            </span>
          </div>

          {/* Range input with custom styling */}
          <div className="flex-1 relative">
            <input
              type="range"
              min="0"
              max={maxSteps}
              value={currentComparisonStep}
              onChange={handleStepChange}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
              style={{
                background: `linear-gradient(to right, #a855f7 0%, #a855f7 ${progressPercent}%, #374151 ${progressPercent}%, #374151 100%)`
              }}
            />
          </div>

          {/* Progress percentage */}
          <span className="text-sm font-semibold text-gray-400 w-12 text-right">
            {maxSteps > 0 ? `${progressPercent.toFixed(0)}%` : "0%"}
          </span>
        </div>

        {/* Timeline info */}
        <div className="mt-2 flex justify-between text-xs text-gray-500">
          <div>PPO Steps: {displayMetrics.ppoRun.ticks.length}</div>
          <div>Hybrid Steps: {displayMetrics.hybridRun.ticks.length}</div>
          <div>Synchronized: {Math.min(displayMetrics.ppoRun.ticks.length, displayMetrics.hybridRun.ticks.length)} steps</div>
        </div>
      </div>
    </div>
  );
}

interface DeltaMetricProps {
  label: string;
  value: number;
  unit: string;
  positive: boolean;
  subtitle?: string;
}

function DeltaMetric({
  label,
  value,
  unit,
  positive,
  subtitle,
}: DeltaMetricProps) {
  const Icon = positive ? TrendingUp : TrendingDown;
  const colorClass = positive ? "text-emerald-400" : "text-red-400";
  const bgClass = positive ? "bg-emerald-500/10" : "bg-red-500/10";

  return (
    <div className={`${bgClass} border border-gray-700 rounded-lg p-3`}>
      <div className="text-xs text-gray-400 font-medium">{label}</div>
      <div className={`flex items-center gap-2 mt-2 font-bold text-xl ${colorClass}`}>
        <Icon className="w-5 h-5 flex-shrink-0" />
        <span>
          {positive ? "+" : ""}
          {value.toFixed(1)}
          <span className="text-sm ml-1">{unit}</span>
        </span>
      </div>
      {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
    </div>
  );
}
