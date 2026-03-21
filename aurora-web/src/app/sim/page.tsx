"use client";

import { useEffect, useState } from "react";
import { useSimulationStore } from "@/shared/store";
import { normalizeScenarioId } from "@/shared/scenarios";
import { ControlBar } from "./ControlBar";
import { MapStage } from "./MapStage";
import { RightPanel } from "./RightPanel";
import { SplitViewComparison } from "./SplitViewComparison";

interface SimulationPreset {
  scenarioId?: string;
  scenarioName?: string;
  model?: "ppo" | "hybrid";
  seed?: number;
  note?: string;
  runId?: string;
}

export default function SimulationPage() {
  const reset = useSimulationStore((state) => state.reset);
  const [showSplitView, setShowSplitView] = useState(false);
  const [initialPreset, setInitialPreset] = useState<SimulationPreset | null>(null);

  useEffect(() => {
    reset();
    return () => reset();
  }, [reset]);

  useEffect(() => {
    const preset: SimulationPreset = {};
    const params = new URLSearchParams(window.location.search);
    const scenarioParam = params.get("scenario");
    const runParam = params.get("run");

    if (scenarioParam) {
      preset.scenarioId = normalizeScenarioId(scenarioParam) ?? scenarioParam;
      preset.note = `Scenario handoff received for ${scenarioParam}. Review settings, then start the simulation.`;
    }

    if (runParam) {
      preset.runId = runParam;
      preset.model = runParam.startsWith("ppo_")
        ? "ppo"
        : runParam.startsWith("hybrid_")
          ? "hybrid"
          : undefined;
      preset.note = `Run handoff received for ${runParam}. The simulator will use matching settings when available, then start a new local session.`;
    }

    const storedRun = sessionStorage.getItem("reproduceRun");
    if (storedRun) {
      try {
        const parsed = JSON.parse(storedRun) as {
          scenario?: string;
          model?: "ppo" | "hybrid";
          seed?: number;
          id?: string;
        };

        preset.scenarioName = normalizeScenarioId(parsed.scenario) ?? parsed.scenario;
        preset.model = parsed.model ?? preset.model;
        preset.seed = parsed.seed ?? preset.seed;
        preset.runId = parsed.id ?? preset.runId;
        preset.note = `Run reproduction loaded from history for ${parsed.scenario ?? parsed.id ?? "the selected run"}.`;
      } catch (error) {
        console.error("Failed to parse reproduceRun payload:", error);
      } finally {
        sessionStorage.removeItem("reproduceRun");
      }
    }

    if (preset.scenarioId || preset.scenarioName || preset.model || preset.seed || preset.runId) {
      setInitialPreset(preset);
    } else {
      setInitialPreset(null);
    }
  }, []);

  if (showSplitView) {
    return (
      <div className="flex h-screen flex-col bg-slate-950">
        <SplitViewComparison onClose={() => setShowSplitView(false)} />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-slate-950">
      <ControlBar
        onToggleSplitView={() => setShowSplitView(true)}
        initialPreset={initialPreset}
      />

      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 relative">
          <MapStage />
        </div>

        <RightPanel />
      </div>
    </div>
  );
}
