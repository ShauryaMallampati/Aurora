"use client";

import { useState } from "react";
import { useSimulationStore } from "@/shared/store";
import { startSimulation, controlSimulation, SimulationStream } from "@/shared/api";
import type { SimulationConfig } from "@/shared/types";
import {
  Play,
  Pause,
  RotateCcw,
  SkipForward,
  Settings,
  Activity,
} from "lucide-react";

export function ControlBar() {
  const {
    status,
    runId,
    config,
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
  
  // Configuration state
  const [model, setModel] = useState<'ppo' | 'hybrid'>('hybrid');
  const [numDrones, setNumDrones] = useState(3);
  const [llmCadence, setLlmCadence] = useState(50);
  const [weather, setWeather] = useState<'live' | 'fixed'>('live');
  const [seed, setSeed] = useState(42);
  const [showSettings, setShowSettings] = useState(false);
  const [fireScenario, setFireScenario] = useState<string>('random');

  // Real fire scenarios from your 116k dataset
  const realFireScenarios = [
    { id: 'random', name: 'Random Historical Fire', year: '', acres: 0, location: 'Nationwide' },
    { id: 'dixie-2021', name: 'Dixie Fire', year: '2021', acres: 963405, location: 'California' },
    { id: 'bootleg-2021', name: 'Bootleg Fire', year: '2021', acres: 413765, location: 'Oregon' },
    { id: 'camp-2018', name: 'Camp Fire', year: '2018', acres: 153336, location: 'California (Paradise)' },
    { id: 'thomas-2017', name: 'Thomas Fire', year: '2017', acres: 281893, location: 'California (Ventura)' },
    { id: 'creek-2020', name: 'Creek Fire', year: '2020', acres: 379895, location: 'California' },
    { id: 'august-2020', name: 'August Complex', year: '2020', acres: 1032648, location: 'California' },
    { id: 'california-2023', name: 'California Recent', year: '2023', acres: 50000, location: 'California' },
    { id: 'montana-2017', name: 'Montana Wildfires', year: '2017', acres: 250000, location: 'Montana' },
    { id: 'arizona-2021', name: 'Arizona Telegraph', year: '2021', acres: 180000, location: 'Arizona' },
  ];

  const handleStart = async () => {
    try {
      addLog('Starting simulation...');
      
      const config: SimulationConfig = {
        scenarioId: fireScenario,
        model,
        seed,
        numDrones,
        llmCadence,
        weather,
        maxSteps: 200,
      };

      setConfig(config);

      // Use mock stream for demo
      const mockStream = new SimulationStream('/api/sim/stream/mock', true);
      
      mockStream
        .onTick((tick) => {
          updateTick(tick);
        })
        .onGuidance((guidance) => {
          updateGuidance(guidance);
          addLog(`LLM Guidance at t=${guidance.t}: ${guidance.strategy.notes}`);
        })
        .onError((error) => {
          addLog(`Error: ${error.message}`);
        })
        .onComplete(() => {
          setStatus('completed');
          addLog('Simulation completed');
        });

      mockStream.start();
      setStream(mockStream);
      setRunId('mock-run-' + Date.now());
      setStatus('running');
      addLog('Simulation started with mock data');
    } catch (error) {
      addLog(`Failed to start: ${(error as Error).message}`);
    }
  };

  const handlePause = () => {
    if (status === 'running') {
      setStatus('paused');
      addLog('Simulation paused');
    } else if (status === 'paused') {
      setStatus('running');
      addLog('Simulation resumed');
    }
  };

  const handleReset = () => {
    if (stream) {
      stream.stop();
      setStream(null);
    }
    reset();
    addLog('Simulation reset');
  };

  const handleStep = () => {
    addLog('Step forward (not implemented in mock)');
  };

  return (
    <div className="bg-gray-900 border-b border-gray-800 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Left: Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-600 rounded-lg flex items-center justify-center">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">Live Simulation</h1>
            <p className="text-xs text-gray-400">
              {status === 'idle' && 'Ready to start'}
              {status === 'running' && 'Running...'}
              {status === 'paused' && 'Paused'}
              {status === 'completed' && 'Completed'}
            </p>
          </div>
        </div>

        {/* Center: Controls */}
        <div className="flex items-center gap-3">
          {status === 'idle' ? (
            <button
              onClick={handleStart}
              className="px-6 py-2.5 bg-gradient-to-r from-orange-500 to-red-600 text-white rounded-lg font-semibold flex items-center gap-2 hover:shadow-lg hover:shadow-orange-500/50 transition"
            >
              <Play className="w-5 h-5" />
              Start
            </button>
          ) : (
            <>
              <button
                onClick={handlePause}
                className="px-4 py-2.5 bg-gray-800 text-white rounded-lg font-semibold flex items-center gap-2 hover:bg-gray-700 transition"
              >
                {status === 'running' ? (
                  <>
                    <Pause className="w-5 h-5" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    Resume
                  </>
                )}
              </button>

              <button
                onClick={handleStep}
                className="px-4 py-2.5 bg-gray-800 text-white rounded-lg font-semibold flex items-center gap-2 hover:bg-gray-700 transition"
              >
                <SkipForward className="w-5 h-5" />
                Step
              </button>

              <button
                onClick={handleReset}
                className="px-4 py-2.5 bg-gray-800 text-white rounded-lg font-semibold flex items-center gap-2 hover:bg-gray-700 transition"
              >
                <RotateCcw className="w-5 h-5" />
                Reset
              </button>
            </>
          )}

          {/* Speed Control */}
          <div className="flex items-center gap-2 px-4 py-2 bg-gray-800 rounded-lg">
            <span className="text-sm text-gray-400">Speed:</span>
            <input
              type="range"
              min="0.25"
              max="8"
              step="0.25"
              value={playbackSpeed}
              onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
              className="w-24"
            />
            <span className="text-sm text-white font-mono w-12">{playbackSpeed}x</span>
          </div>
        </div>

        {/* Right: Settings */}
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="px-4 py-2.5 bg-gray-800 text-white rounded-lg font-semibold flex items-center gap-2 hover:bg-gray-700 transition"
        >
          <Settings className="w-5 h-5" />
          Config
        </button>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="mt-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
          {/* Fire Scenario Selector */}
          <div className="mb-4 pb-4 border-b border-gray-700">
            <label className="block text-sm font-semibold text-white mb-2">🔥 Real Fire Scenario</label>
            <select
              value={fireScenario}
              onChange={(e) => setFireScenario(e.target.value)}
              disabled={status !== 'idle'}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-white disabled:opacity-50"
            >
              {realFireScenarios.map((scenario) => (
                <option key={scenario.id} value={scenario.id}>
                  {scenario.name} {scenario.year && `(${scenario.year})`} 
                  {scenario.acres > 0 && ` - ${(scenario.acres / 1000).toFixed(0)}k acres`}
                  {scenario.location && ` - ${scenario.location}`}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-400 mt-1">
              Choose from 116,337 real historical fires (1308-2024)
            </p>
          </div>

          <div className="grid grid-cols-5 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value as 'ppo' | 'hybrid')}
                disabled={status !== 'idle'}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-white disabled:opacity-50"
              >
                <option value="ppo">PPO</option>
                <option value="hybrid">Hybrid (PPO + LLM)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">Drones</label>
              <input
                type="number"
                min="1"
                max="10"
                value={numDrones}
                onChange={(e) => setNumDrones(parseInt(e.target.value))}
                disabled={status !== 'idle'}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-white disabled:opacity-50"
              />
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">LLM Cadence</label>
              <input
                type="number"
                min="10"
                max="100"
                step="10"
                value={llmCadence}
                onChange={(e) => setLlmCadence(parseInt(e.target.value))}
                disabled={status !== 'idle' || model === 'ppo'}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-white disabled:opacity-50"
              />
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">Weather</label>
              <select
                value={weather}
                onChange={(e) => setWeather(e.target.value as 'live' | 'fixed')}
                disabled={status !== 'idle'}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-white disabled:opacity-50"
              >
                <option value="live">Live (NOAA)</option>
                <option value="fixed">Fixed</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">Seed</label>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(parseInt(e.target.value))}
                disabled={status !== 'idle'}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-white disabled:opacity-50"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
