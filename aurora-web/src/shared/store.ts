// Zustand store for simulation state

import { create } from 'zustand';
import type {
  TelemetryTick,
  LLMGuidance,
  SimulationConfig,
  RunSummary,
} from './types';

interface SimulationState {
  // Current run
  runId: string | null;
  status: 'idle' | 'running' | 'paused' | 'completed';
  currentTick: TelemetryTick | null;
  latestGuidance: LLMGuidance | null;
  
  // History
  ticks: TelemetryTick[];
  guidanceHistory: LLMGuidance[];
  
  // Configuration
  config: SimulationConfig | null;
  playbackSpeed: number; // 0.25x to 8x
  
  // UI state
  selectedTab: 'metrics' | 'telemetry' | 'guidance' | 'charts' | 'logs';
  logs: string[];
  
  // Actions
  setRunId: (runId: string) => void;
  setStatus: (status: SimulationState['status']) => void;
  updateTick: (tick: TelemetryTick) => void;
  updateGuidance: (guidance: LLMGuidance) => void;
  setConfig: (config: SimulationConfig) => void;
  setPlaybackSpeed: (speed: number) => void;
  setSelectedTab: (tab: SimulationState['selectedTab']) => void;
  addLog: (message: string) => void;
  reset: () => void;
}

export const useSimulationStore = create<SimulationState>((set) => ({
  runId: null,
  status: 'idle',
  currentTick: null,
  latestGuidance: null,
  ticks: [],
  guidanceHistory: [],
  config: null,
  playbackSpeed: 1,
  selectedTab: 'metrics',
  logs: [],

  setRunId: (runId) => set({ runId }),
  
  setStatus: (status) => set({ status }),
  
  updateTick: (tick) => set((state) => ({
    currentTick: tick,
    ticks: [...state.ticks.slice(-500), tick], // Keep last 500 ticks
  })),
  
  updateGuidance: (guidance) => set((state) => ({
    latestGuidance: guidance,
    guidanceHistory: [...state.guidanceHistory, guidance],
  })),
  
  setConfig: (config) => set({ config }),
  
  setPlaybackSpeed: (playbackSpeed) => set({ playbackSpeed }),
  
  setSelectedTab: (selectedTab) => set({ selectedTab }),
  
  addLog: (message) => set((state) => ({
    logs: [...state.logs.slice(-100), `[${new Date().toISOString()}] ${message}`],
  })),
  
  reset: () => set({
    runId: null,
    status: 'idle',
    currentTick: null,
    latestGuidance: null,
    ticks: [],
    guidanceHistory: [],
    logs: [],
  }),
}));
