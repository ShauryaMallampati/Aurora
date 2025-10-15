"use client";

import { useEffect } from "react";
import { useSimulationStore } from "@/shared/store";
import { ControlBar } from "./ControlBar";
import { MapStage } from "./MapStage";
import { RightPanel } from "./RightPanel";

export default function SimulationPage() {
  const reset = useSimulationStore((state) => state.reset);

  useEffect(() => {
    // Reset on mount
    return () => reset();
  }, [reset]);

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      {/* Top Control Bar */}
      <ControlBar />

      {/* Main Content: Map + Right Panel */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map Stage */}
        <div className="flex-1 relative">
          <MapStage />
        </div>

        {/* Right Panel */}
        <RightPanel />
      </div>
    </div>
  );
}
