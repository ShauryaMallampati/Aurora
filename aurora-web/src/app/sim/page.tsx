"use client";

import { useEffect, useState } from "react";
import { useSimulationStore } from "@/shared/store";
import { ControlBar } from "./ControlBar";
import { MapStage } from "./MapStage";
import { RightPanel } from "./RightPanel";
import { SplitViewComparison } from "./SplitViewComparison";
import { FireCreator, CustomFireConfig } from "./FireCreator";

export default function SimulationPage() {
  const reset = useSimulationStore((state) => state.reset);
  const addLog = useSimulationStore((state) => state.addLog);
  const [showSplitView, setShowSplitView] = useState(false);
  const [showFireCreator, setShowFireCreator] = useState(false);

  useEffect(() => {
    // Reset on mount
    return () => reset();
  }, [reset]);

  const handleCreateFire = (fireConfig: CustomFireConfig) => {
    addLog(`Custom fire created at (${fireConfig.location.lat}, ${fireConfig.location.lng})`);
    addLog(`Strength: ${fireConfig.strength}/10, Wind: ${fireConfig.windFactor}x`);
    addLog(`Resources: ${fireConfig.numDrones} drones, ${fireConfig.waterAmount}gal each`);
    addLog(`Estimated cost: $${fireConfig.estimatedCost.toLocaleString()}`);
    setShowFireCreator(false);
    // TODO: When model is trained, pass fireConfig to simulation
  };

  const handleStartSimulationFromFireCreator = (fireConfig: CustomFireConfig) => {
    addLog(`🔥 Starting simulation with custom fire`);
    addLog(`Location: (${fireConfig.location.lat.toFixed(4)}, ${fireConfig.location.lng.toFixed(4)})`);
    addLog(`Strength: ${fireConfig.strength}/10, Wind: ${fireConfig.windFactor}x`);
    addLog(`Drones: ${fireConfig.numDrones}, Water: ${fireConfig.waterAmount}gal each`);
    addLog(`Estimated cost: $${fireConfig.estimatedCost.toLocaleString()}`);
    setShowFireCreator(false);

    // TODO: Implement actual simulation start with this config
    // For now just log it; backend integration needed
  };

  // If split view is enabled, show comparison instead
  if (showSplitView) {
    return (
      <div className="h-screen flex flex-col bg-[#0a0a0b]">
        <SplitViewComparison onClose={() => setShowSplitView(false)} />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-[#0a0a0b]">
      {/* Top Control Bar */}
      <ControlBar
        onToggleSplitView={() => setShowSplitView(true)}
        onOpenFireCreator={() => setShowFireCreator(true)}
      />

      {/* Main Content: Map + Right Panel */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map Stage */}
        <div className="flex-1 relative">
          <MapStage />
        </div>

        {/* Right Panel */}
        <RightPanel />
      </div>

      {/* Fire Creator Modal */}
      {showFireCreator && (
        <FireCreator
          onClose={() => setShowFireCreator(false)}
          onCreateFire={handleCreateFire}
          onStartSimulation={handleStartSimulationFromFireCreator}
        />
      )}
    </div>
  );
}
