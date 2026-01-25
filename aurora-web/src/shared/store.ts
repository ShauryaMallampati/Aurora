// Zustand store for simulation state

import { create } from 'zustand';
import type {
  TelemetryTick,
  LLMGuidance,
  SimulationConfig,
  RunSummary,
} from './types';
import type { SimulationRun, ComparisonMetrics } from './runsDataLoader';

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
  
  // Comparison view state
  comparisonMode: boolean;
  ppoRun: SimulationRun | null;
  hybridRun: SimulationRun | null;
  comparisonMetrics: ComparisonMetrics | null;
  currentComparisonStep: number;
  
  // UI state
  selectedTab: 'metrics' | 'telemetry' | 'guidance' | 'charts' | 'costs' | 'logs';
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
  
  // Comparison actions
  setComparisonMode: (enabled: boolean) => void;
  setComparisonRuns: (ppo: SimulationRun, hybrid: SimulationRun, metrics: ComparisonMetrics) => void;
  setCurrentComparisonStep: (step: number) => void;
}

export const useSimulationStore = create<SimulationState>((set: any) => ({
  runId: null,
  status: 'idle',
  currentTick: null,
  latestGuidance: null,
  ticks: [],
  guidanceHistory: [],
  config: null,
  playbackSpeed: 1,
  comparisonMode: false,
  ppoRun: null,
  hybridRun: null,
  comparisonMetrics: null,
  currentComparisonStep: 0,
  selectedTab: 'metrics',
  logs: [],

  setRunId: (runId: string) => set({ runId }),
  
  setStatus: (status: SimulationState['status']) => set({ status }),
  
  updateTick: (tick: TelemetryTick) => set((state: SimulationState) => ({
    currentTick: tick,
    ticks: [...state.ticks.slice(-500), tick], // Keep last 500 ticks
  })),
  
  updateGuidance: (guidance: LLMGuidance) => set((state: SimulationState) => ({
    latestGuidance: guidance,
    guidanceHistory: [...state.guidanceHistory, guidance],
  })),
  
  setConfig: (config: SimulationConfig) => set({ config }),
  
  setPlaybackSpeed: (playbackSpeed: number) => set({ playbackSpeed }),
  
  setSelectedTab: (selectedTab: SimulationState['selectedTab']) => set({ selectedTab }),
  
  addLog: (message: string) => set((state: SimulationState) => ({
    logs: [...state.logs.slice(-100), `[${new Date().toISOString()}] ${message}`],
  })),
  
  setComparisonMode: (comparisonMode: boolean) => set({ comparisonMode }),
  
  setComparisonRuns: (ppo: SimulationRun, hybrid: SimulationRun, metrics: ComparisonMetrics) => 
    set({ ppoRun: ppo, hybridRun: hybrid, comparisonMetrics: metrics }),
  
  setCurrentComparisonStep: (currentComparisonStep: number) => set({ currentComparisonStep }),
  
  reset: () => set({
    runId: null,
    status: 'idle',
    currentTick: null,
    latestGuidance: null,
    ticks: [],
    guidanceHistory: [],
    comparisonMode: false,
    ppoRun: null,
    hybridRun: null,
    comparisonMetrics: null,
    currentComparisonStep: 0,
    logs: [],
  }),
}));
