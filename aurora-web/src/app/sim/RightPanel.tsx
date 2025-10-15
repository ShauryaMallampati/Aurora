"use client";

import { useSimulationStore } from "@/shared/store";
import { MetricsTab } from "./tabs/MetricsTab";
import { TelemetryTab } from "./tabs/TelemetryTab";
import { GuidanceTab } from "./tabs/GuidanceTab";
import { ChartsTab } from "./tabs/ChartsTab";
import { LogsTab } from "./tabs/LogsTab";

const TABS = [
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
    <div className="w-96 bg-gray-900 border-l border-gray-800 flex flex-col">
      {/* Tab Headers */}
      <div className="flex border-b border-gray-800">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setSelectedTab(tab.id)}
            className={`flex-1 px-4 py-3 text-sm font-medium transition ${
              selectedTab === tab.id
                ? "bg-gray-800 text-white border-b-2 border-orange-500"
                : "text-gray-400 hover:text-white hover:bg-gray-800/50"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">
  {selectedTab === "metrics" && <MetricsTab />}
  {selectedTab === "telemetry" && <TelemetryTab />}
  {selectedTab === "guidance" && <GuidanceTab />}
  {selectedTab === "charts" && <ChartsTab />}
  {selectedTab === "logs" && <LogsTab />}
      </div>
    </div>
  );
}
