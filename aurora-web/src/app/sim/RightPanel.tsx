"use client";

import { useSimulationStore } from "@/shared/store";
import { MethodTab } from "./tabs/MethodTab";
import { MetricsTab } from "./tabs/MetricsTab";
import { TelemetryTab } from "./tabs/TelemetryTab";
import { GuidanceTab } from "./tabs/GuidanceTab";
import { ChartsTab } from "./tabs/ChartsTab";
import { LogsTab } from "./tabs/LogsTab";

const TABS = [
  { id: "method", label: "Method" },
  { id: "metrics", label: "Metrics" },
  { id: "telemetry", label: "Telemetry" },
  { id: "guidance", label: "Guidance" },
  { id: "charts", label: "Charts" },
  { id: "logs", label: "Logs" },
] as const;

export function RightPanel() {
  const selectedTab = useSimulationStore((state) => state.selectedTab);
  const setSelectedTab = useSimulationStore((state) => state.setSelectedTab);

  return (
    <div className="flex w-80 flex-col border-l border-slate-800 bg-slate-950">
      <div className="flex overflow-x-auto border-b border-slate-800">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id)}
            className={`flex-shrink-0 whitespace-nowrap px-3 py-3 text-xs font-medium transition ${
              selectedTab === tab.id
                ? "border-b-2 border-slate-300 bg-slate-900 text-white"
                : "text-slate-400 hover:bg-slate-900 hover:text-white"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {selectedTab === "method" && <MethodTab />}
        {selectedTab === "metrics" && <MetricsTab />}
        {selectedTab === "telemetry" && <TelemetryTab />}
        {selectedTab === "guidance" && <GuidanceTab />}
        {selectedTab === "charts" && <ChartsTab />}
        {selectedTab === "logs" && <LogsTab />}
      </div>
    </div>
  );
}
