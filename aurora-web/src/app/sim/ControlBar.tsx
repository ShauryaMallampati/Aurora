"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  Pause,
  Play,
  RotateCcw,
  Settings,
  SkipForward,
  Split,
} from "lucide-react";
import { controlSimulation, SimulationStream, startSimulation } from "@/shared/api";
import {
  findPresetScenarioById,
  formatScenarioLabel,
  normalizeScenarioId,
  PRESET_SCENARIOS,
} from "@/shared/scenarios";
import { useSimulationStore } from "@/shared/store";
import type { SimulationConfig } from "@/shared/types";
import { isSupabaseConfigured } from "@/lib/supabase";

interface ControlBarProps {
  onToggleSplitView?: () => void;
  initialPreset?: {
    scenarioId?: string;
    scenarioName?: string;
    model?: "ppo" | "hybrid";
    seed?: number;
    runId?: string;
    note?: string;
  } | null;
}

interface ScenarioOption {
  id: string;
  label: string;
}

interface ArtifactRunRecord {
  scenarioId?: string;
}

type FireSize = "small" | "medium" | "large" | "extreme";

function buildBaseScenarioOptions(): ScenarioOption[] {
  return [
    { id: "random", label: "Auto-selected scenario" },
    ...PRESET_SCENARIOS.map((scenario) => ({
      id: scenario.id,
      label: `${scenario.name} (${scenario.year})`,
    })),
    { id: "custom", label: "Custom fire" },
  ];
}

function moveMap(lat: number, lng: number, zoom = 10) {
  window.dispatchEvent(
    new CustomEvent("moveMapToFire", {
      detail: { lat, lng, zoom },
    }),
  );
}

export function ControlBar({ onToggleSplitView, initialPreset }: ControlBarProps = {}) {
  const persistenceAvailable = isSupabaseConfigured;
  const {
    status,
    runId,
    playbackSpeed,
    setRunId,
    setStatus,
    updateTick,
    updateGuidance,
    setConfig,
    setPlaybackSpeed,
    addLog,
    reset,
  } = useSimulationStore();

  const [stream, setStream] = useState<SimulationStream | null>(null);
  const [showSettings, setShowSettings] = useState(true);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [availableScenarios, setAvailableScenarios] = useState<ScenarioOption[]>(buildBaseScenarioOptions);

  const [model, setModel] = useState<"ppo" | "hybrid">("hybrid");
  const [numDrones, setNumDrones] = useState(3);
  const [llmCadence, setLlmCadence] = useState(50);
  const [weather, setWeather] = useState<"live" | "fixed">("live");
  const [seed, setSeed] = useState(42);
  const [maxSteps, setMaxSteps] = useState(200);
  const [fireScenario, setFireScenario] = useState<string>("random");

  const [customLat, setCustomLat] = useState(36.7783);
  const [customLng, setCustomLng] = useState(-119.4179);
  const [customFireSize, setCustomFireSize] = useState<FireSize>("medium");
  const [customWindSpeed, setCustomWindSpeed] = useState(7.2);
  const [customWindDir, setCustomWindDir] = useState(290);
  const [customTemp, setCustomTemp] = useState(35);
  const [customHumidity, setCustomHumidity] = useState(0.23);

  const initialPresetApplied = useRef(false);

  const selectedPreset = useMemo(() => findPresetScenarioById(fireScenario), [fireScenario]);
  const scenarioLabel = useMemo(
    () =>
      availableScenarios.find((scenario) => scenario.id === fireScenario)?.label ??
      formatScenarioLabel(fireScenario),
    [availableScenarios, fireScenario],
  );

  useEffect(() => {
    let cancelled = false;

    const loadScenarioOptions = async () => {
      try {
        const response = await fetch("/api/runs", { cache: "no-store" });
        if (!response.ok) {
          return;
        }

        const records = (await response.json()) as ArtifactRunRecord[];
        const scenarioIds = Array.from(
          new Set(
            records
              .map((record) => normalizeScenarioId(record.scenarioId) ?? record.scenarioId)
              .filter(Boolean) as string[],
          ),
        );

        if (cancelled) {
          return;
        }

        const merged = [...buildBaseScenarioOptions()];
        for (const scenarioId of scenarioIds) {
          if (!merged.some((scenario) => scenario.id === scenarioId)) {
            merged.splice(merged.length - 1, 0, {
              id: scenarioId,
              label: formatScenarioLabel(scenarioId),
            });
          }
        }

        setAvailableScenarios(merged);
      } catch (error) {
        console.error("Failed to load artifact-backed scenarios:", error);
      }
    };

    void loadScenarioOptions();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!initialPreset || initialPresetApplied.current) {
      return;
    }

    initialPresetApplied.current = true;

    if (initialPreset.model) {
      setModel(initialPreset.model);
    }

    if (initialPreset.seed !== undefined) {
      setSeed(initialPreset.seed);
    }

    const scenarioId = normalizeScenarioId(initialPreset.scenarioId ?? initialPreset.scenarioName);
    if (scenarioId) {
      setFireScenario(scenarioId);
      setAvailableScenarios((current) => {
        if (current.some((scenario) => scenario.id === scenarioId)) {
          return current;
        }

        const next = [...current];
        next.splice(next.length - 1, 0, {
          id: scenarioId,
          label: formatScenarioLabel(scenarioId),
        });
        return next;
      });
    }

    if (initialPreset.note) {
      addLog(initialPreset.note);
    }

    if (initialPreset.runId) {
      addLog(`Prepared simulator settings from ${initialPreset.runId}.`);
    }
  }, [initialPreset, addLog]);

  useEffect(() => {
    if (fireScenario === "custom") {
      moveMap(customLat, customLng, 11);
      return;
    }

    if (selectedPreset) {
      moveMap(selectedPreset.lat, selectedPreset.lng, 10);
    }
  }, [customLat, customLng, fireScenario, selectedPreset]);

  useEffect(() => {
    const handleSetCustomFireLocation = (event: Event) => {
      if (fireScenario !== "custom" || status !== "idle") {
        return;
      }

      const customEvent = event as CustomEvent<{ lat: number; lng: number }>;
      const { lat, lng } = customEvent.detail;
      if (Number.isNaN(lat) || Number.isNaN(lng)) {
        return;
      }

      setCustomLat(lat);
      setCustomLng(lng);
      addLog(`Custom ignition point updated from map click: ${lat.toFixed(4)}, ${lng.toFixed(4)}.`);
    };

    window.addEventListener("setCustomFireLocation", handleSetCustomFireLocation as EventListener);
    return () => {
      window.removeEventListener("setCustomFireLocation", handleSetCustomFireLocation as EventListener);
    };
  }, [addLog, fireScenario, status]);

  const handleStart = async () => {
    try {
      const config: SimulationConfig = {
        scenarioId: fireScenario,
        model,
        seed,
        numDrones,
        llmCadence: model === "hybrid" ? llmCadence : 0,
        weather,
        maxSteps,
        ...(fireScenario === "custom" && {
          customScenario: {
            lat: customLat,
            lng: customLng,
            fireSize: customFireSize,
            windSpeed: customWindSpeed,
            windDir: customWindDir,
            temp: customTemp,
            humidity: customHumidity,
          },
        }),
      };

      if (fireScenario === "custom") {
        addLog(
          `Starting custom fire at (${customLat.toFixed(3)}, ${customLng.toFixed(3)}) with ${customFireSize} spread.`,
        );
      } else if (selectedPreset) {
        addLog(
          `Starting ${selectedPreset.name} (${selectedPreset.year}) in ${selectedPreset.location}.`,
        );
        addLog(`Historical footprint: ${selectedPreset.acres.toLocaleString()} acres.`);
      } else {
        addLog(`Starting ${model.toUpperCase()} simulation for ${scenarioLabel}.`);
      }

      setConfig(config);
      const response = await startSimulation(config);
      const liveStream = new SimulationStream(response.sseUrl, false);

      liveStream.setConfig(config);
      liveStream.setPlaybackSpeed(playbackSpeed);
      liveStream
        .onTick((tick) => {
          updateTick(tick);
        })
        .onGuidance((guidance) => {
          updateGuidance(guidance);
          addLog(`Guidance t=${guidance.t}: ${guidance.strategy.notes}`);
        })
        .onError((error) => {
          addLog(`Stream error: ${error.message}`);
        })
        .onComplete(() => {
          setStatus("completed");
          setStream(null);
          addLog("Simulation completed.");
          addLog(
            persistenceAvailable
              ? "Run history is sourced from recorded artifacts and persisted records."
              : "This local session was streamed in memory only.",
          );
        });

      liveStream.start();
      setStream(liveStream);
      setRunId(response.runId);
      setStatus("running");
    } catch (error) {
      addLog(`Failed to start simulation: ${(error as Error).message}`);
    }
  };

  const handlePause = async () => {
    if (!runId) {
      return;
    }

    try {
      if (status === "running") {
        await controlSimulation({ action: "pause", runId });
        stream?.pause();
        setStatus("paused");
        addLog("Simulation paused.");
        return;
      }

      if (status === "paused") {
        await controlSimulation({ action: "resume", runId });
        stream?.resume();
        setStatus("running");
        addLog("Simulation resumed.");
      }
    } catch (error) {
      addLog(`Failed to update simulation state: ${(error as Error).message}`);
    }
  };

  const handleStep = async () => {
    if (!runId) {
      return;
    }

    try {
      await controlSimulation({ action: "step", runId, steps: 1 });
      setStatus("paused");
      addLog("Advanced by one step.");
    } catch (error) {
      addLog(`Failed to step simulation: ${(error as Error).message}`);
    }
  };

  const confirmReset = async () => {
    try {
      if (runId) {
        await controlSimulation({ action: "reset", runId });
      }
    } catch (error) {
      addLog(`Reset warning: ${(error as Error).message}`);
    } finally {
      stream?.stop();
      setStream(null);
      reset();
      setShowResetConfirm(false);
      addLog("Simulation state cleared.");
    }
  };

  const handleSpeedChange = async (newSpeed: number) => {
    setPlaybackSpeed(newSpeed);
    stream?.setPlaybackSpeed(newSpeed);

    if (runId && (status === "running" || status === "paused")) {
      try {
        await controlSimulation({ action: "speed", runId, speed: newSpeed });
      } catch (error) {
        addLog(`Failed to update playback speed: ${(error as Error).message}`);
      }
    }
  };

  return (
    <div className="border-b border-slate-800 bg-slate-950">
      <div className="flex flex-col gap-4 px-6 py-4">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <h1 className="text-lg font-semibold text-white">Simulation</h1>
            <p className="mt-1 text-sm text-slate-400">
              {status === "idle" && "Choose a real scenario or configure a custom fire, then start the run."}
              {status === "running" && "Telemetry stream is active."}
              {status === "paused" && "Stream paused. Step or resume when ready."}
              {status === "completed" && "Session finished. Reset to run again."}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {status === "idle" ? (
              <button
                onClick={handleStart}
                className="inline-flex items-center gap-2 rounded-md border border-blue-600 bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
              >
                <Play className="h-4 w-4" />
                Start
              </button>
            ) : (
              <>
                <button
                  onClick={handlePause}
                  className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
                >
                  {status === "running" ? (
                    <>
                      <Pause className="h-4 w-4" />
                      Pause
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Resume
                    </>
                  )}
                </button>

                <button
                  onClick={handleStep}
                  className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
                >
                  <SkipForward className="h-4 w-4" />
                  Step
                </button>

                <button
                  onClick={() => setShowResetConfirm(true)}
                  className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
                >
                  <RotateCcw className="h-4 w-4" />
                  Reset
                </button>
              </>
            )}

            <label className="flex items-center gap-3 rounded-md border border-slate-800 bg-slate-900 px-4 py-2 text-sm text-slate-300">
              <span>Speed</span>
              <input
                type="range"
                min="0.25"
                max="8"
                step="0.25"
                value={playbackSpeed}
                onChange={(event) => void handleSpeedChange(parseFloat(event.target.value))}
                className="w-24"
              />
              <span className="w-10 text-right font-mono text-white">{playbackSpeed}x</span>
            </label>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {onToggleSplitView ? (
              <button
                onClick={onToggleSplitView}
                className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                <Split className="h-4 w-4" />
                Compare
              </button>
            ) : null}

            <Link
              href="/method"
              className="rounded-md border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              Method
            </Link>
            <Link
              href="/runs"
              className="rounded-md border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              Runs
            </Link>
            <button
              onClick={() => setShowSettings((current) => !current)}
              className="inline-flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              <Settings className="h-4 w-4" />
              Settings
            </button>
          </div>
        </div>

        {showSettings ? (
          <div className="space-y-4 rounded-md border border-slate-800 bg-slate-900 p-4">
            <div className="grid gap-4 lg:grid-cols-6">
              <div className="lg:col-span-2">
                <label className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                  Scenario
                </label>
                <select
                  value={fireScenario}
                  onChange={(event) => setFireScenario(event.target.value)}
                  disabled={status !== "idle"}
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none disabled:opacity-50"
                >
                  {availableScenarios.map((scenario) => (
                    <option key={scenario.id} value={scenario.id}>
                      {scenario.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                  Model
                </label>
                <select
                  value={model}
                  onChange={(event) => setModel(event.target.value as "ppo" | "hybrid")}
                  disabled={status !== "idle"}
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none disabled:opacity-50"
                >
                  <option value="ppo">PPO</option>
                  <option value="hybrid">Hybrid</option>
                </select>
              </div>

              <div>
                <label className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                  Drones
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={numDrones}
                  onChange={(event) => setNumDrones(parseInt(event.target.value, 10) || 1)}
                  disabled={status !== "idle"}
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none disabled:opacity-50"
                />
              </div>

              <div>
                <label className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                  Max steps
                </label>
                <input
                  type="number"
                  min="50"
                  max="1000"
                  step="50"
                  value={maxSteps}
                  onChange={(event) => setMaxSteps(parseInt(event.target.value, 10) || 50)}
                  disabled={status !== "idle"}
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none disabled:opacity-50"
                />
              </div>

              <div>
                <label className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                  Seed
                </label>
                <input
                  type="number"
                  value={seed}
                  onChange={(event) => setSeed(parseInt(event.target.value, 10) || 0)}
                  disabled={status !== "idle"}
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none disabled:opacity-50"
                />
              </div>

              <div>
                <label className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                  Weather mode
                </label>
                <select
                  value={weather}
                  onChange={(event) => setWeather(event.target.value as "live" | "fixed")}
                  disabled={status !== "idle"}
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none disabled:opacity-50"
                >
                  <option value="live">Scenario weather</option>
                  <option value="fixed">Fixed</option>
                </select>
              </div>

              <div>
                <label className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                  LLM cadence
                </label>
                <input
                  type="number"
                  min="10"
                  max="100"
                  step="10"
                  value={llmCadence}
                  onChange={(event) => setLlmCadence(parseInt(event.target.value, 10) || 10)}
                  disabled={status !== "idle" || model === "ppo"}
                  className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white outline-none disabled:opacity-50"
                />
              </div>
            </div>

            {selectedPreset ? (
              <div className="rounded-md border border-slate-800 bg-slate-950 p-4 text-sm text-slate-300">
                <p className="font-semibold text-white">{selectedPreset.name}</p>
                <p className="mt-1">
                  {selectedPreset.location} · {selectedPreset.year} · {selectedPreset.acres.toLocaleString()} acres
                </p>
              </div>
            ) : null}

            {fireScenario === "custom" ? (
              <div className="grid gap-4 rounded-md border border-slate-800 bg-slate-950 p-4 lg:grid-cols-4">
                <div>
                  <label className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                    Latitude
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    value={customLat}
                    onChange={(event) => setCustomLat(parseFloat(event.target.value) || 0)}
                    disabled={status !== "idle"}
                    className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none disabled:opacity-50"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                    Longitude
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    value={customLng}
                    onChange={(event) => setCustomLng(parseFloat(event.target.value) || 0)}
                    disabled={status !== "idle"}
                    className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none disabled:opacity-50"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                    Fire size
                  </label>
                  <select
                    value={customFireSize}
                    onChange={(event) => setCustomFireSize(event.target.value as FireSize)}
                    disabled={status !== "idle"}
                    className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none disabled:opacity-50"
                  >
                    <option value="small">Small</option>
                    <option value="medium">Medium</option>
                    <option value="large">Large</option>
                    <option value="extreme">Extreme</option>
                  </select>
                </div>
                <div>
                  <label className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                    Wind speed (m/s)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="30"
                    step="0.5"
                    value={customWindSpeed}
                    onChange={(event) => setCustomWindSpeed(parseFloat(event.target.value) || 0)}
                    disabled={status !== "idle"}
                    className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none disabled:opacity-50"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                    Wind direction
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="359"
                    value={customWindDir}
                    onChange={(event) => setCustomWindDir(parseFloat(event.target.value) || 0)}
                    disabled={status !== "idle"}
                    className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none disabled:opacity-50"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                    Temperature (°C)
                  </label>
                  <input
                    type="number"
                    min="-10"
                    max="50"
                    step="0.5"
                    value={customTemp}
                    onChange={(event) => setCustomTemp(parseFloat(event.target.value) || 0)}
                    disabled={status !== "idle"}
                    className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none disabled:opacity-50"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-medium uppercase tracking-[0.08em] text-slate-400">
                    Humidity
                  </label>
                  <input
                    type="number"
                    min="0.05"
                    max="1"
                    step="0.01"
                    value={customHumidity}
                    onChange={(event) => setCustomHumidity(parseFloat(event.target.value) || 0)}
                    disabled={status !== "idle"}
                    className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white outline-none disabled:opacity-50"
                  />
                </div>
                <div className="lg:col-span-4 text-sm text-slate-400">
                  Click the map to place the ignition point, or enter coordinates manually. These settings
                  change the simulated origin, spread size, and weather in the live session.
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>

      {showResetConfirm ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-md rounded-md border border-slate-700 bg-slate-950 p-6">
            <h2 className="text-lg font-semibold text-white">Reset simulation?</h2>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              This clears the current stream, telemetry history, and active session state.
            </p>
            <div className="mt-5 flex gap-3">
              <button
                onClick={confirmReset}
                className="rounded-md border border-red-700 bg-red-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-800"
              >
                Reset
              </button>
              <button
                onClick={() => setShowResetConfirm(false)}
                className="rounded-md border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
