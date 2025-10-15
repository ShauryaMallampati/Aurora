"use client";

import { useSimulationStore } from "@/shared/store";
import { Brain, Target, Shield, Info } from "lucide-react";

export function GuidanceTab() {
  const guidanceHistory = useSimulationStore((state) => state.guidanceHistory);
  const latestGuidance = guidanceHistory[guidanceHistory.length - 1];

  if (!latestGuidance) {
    return (
      <div className="p-6 text-gray-400 text-center">
        <Brain className="w-12 h-12 mx-auto mb-3 text-gray-600" />
        <p>LLM guidance will appear here</p>
        <p className="text-xs mt-2">
          Guidance is generated every N steps (configurable)
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Latest Guidance Summary */}
      <div className="bg-gradient-to-br from-purple-900/50 to-blue-900/50 rounded-lg p-4 border border-purple-700/50">
        <div className="flex items-center gap-2 mb-3">
          <Brain className="w-5 h-5 text-purple-400" />
          <h3 className="font-semibold text-white">Latest Guidance</h3>
          <span className="ml-auto text-xs text-gray-400">t={latestGuidance.t}</span>
        </div>

        <div className="space-y-3">
          {/* Priority Zones */}
          {latestGuidance.strategy.priorityZones &&
            latestGuidance.strategy.priorityZones.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-4 h-4 text-orange-400" />
                  <span className="text-sm font-semibold text-orange-400">
                    Priority Zones
                  </span>
                </div>
                <div className="space-y-1">
                  {latestGuidance.strategy.priorityZones.map((zone, i) => (
                    <div key={i} className="text-sm text-gray-300 ml-6">
                      • ({zone.lat.toFixed(4)}, {zone.lng.toFixed(4)}) - radius{" "}
                      {zone.radius}m
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* Defensive Lines */}
          {latestGuidance.strategy.defensiveLines &&
            latestGuidance.strategy.defensiveLines.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-4 h-4 text-blue-400" />
                  <span className="text-sm font-semibold text-blue-400">
                    Defensive Lines
                  </span>
                </div>
                <div className="space-y-1">
                  {latestGuidance.strategy.defensiveLines.map((line, i) => (
                    <div key={i} className="text-sm text-gray-300 ml-6">
                      • Line {i + 1}: {line.length} points
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* Notes / Rationale */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Info className="w-4 h-4 text-cyan-400" />
              <span className="text-sm font-semibold text-cyan-400">Rationale</span>
            </div>
            <div className="text-sm text-gray-300 ml-6">
              {latestGuidance.strategy.notes || "No rationale provided"}
            </div>
          </div>
        </div>
      </div>

      {/* Guidance History */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="font-semibold text-white mb-3">History</h3>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {guidanceHistory
            .slice()
            .reverse()
            .map((guidance, i) => (
              <div
                key={i}
                className="bg-gray-900 rounded p-3 text-sm"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-gray-400">t={guidance.t}</span>
                  <span className="text-xs text-gray-500">
                    {new Date(guidance.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="text-gray-300 text-xs line-clamp-2">
                  {guidance.strategy.notes || "No notes"}
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
