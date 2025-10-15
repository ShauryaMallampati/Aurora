// Type definitions for AURORA simulation

export interface SimulationConfig {
  scenarioId?: string; // e.g. 'dixie-2021', 'random'
  model: 'ppo' | 'hybrid';
  seed: number;
  numDrones: number;
  llmCadence: number;
  weather: 'live' | 'fixed';
  maxSteps?: number;
}

export interface StartSimResponse {
  runId: string;
  sseUrl: string;
}

export interface FireGrid {
  width: number;
  height: number;
  fire: string; // base64-encoded uint8 array
}

export interface Drone {
  id: number;
  lat: number;
  lng: number;
  battery: number; // 0-1
  water: number; // 0-1
  action: string; // 'idle', 'drop', 'scout', 'recharge', 'refill'
  heading: number; // 0-360 degrees
}

export interface Weather {
  wind_deg?: number; // Legacy
  wind_mps?: number; // Legacy
  windSpeed: number; // m/s
  windDir: number; // degrees
  temp: number; // Celsius
  humidity: number; // 0-1
  temperature_c?: number; // Legacy
}

export interface SimMetrics {
  return: number;
  areaBurned: number;
  containment: number;
  suppressionUsed: number;
  idleStepsPerAgent: number;
  activeDrones: number;
  burningCells: number;
}

export interface Metrics {
  burnedArea: number; // acres
  firePerimeter: number; // km
  containment: number; // 0-1
  avgIntensity: number; // 0-1
  waterDropped: number; // liters
}

export interface SimEvent {
  type: 'drop' | 'suppress' | 'move' | 'scan' | 'refuel' | 'recharge';
  agent: string;
  x: number;
  y: number;
  message?: string;
}

export interface TelemetryTick {
  t: number;
  timestamp: string; // ISO 8601
  drones: Drone[];
  weather: Weather;
  metrics: Metrics;
  events: SimEvent[];
  fireGrid: string; // base64 encoded JSON array
  fireOrigin: { lat: number; lng: number };
}

export interface PriorityZone {
  lat: number;
  lng: number;
  radius: number; // meters
}

export interface DefensiveLine {
  lat: number;
  lng: number;
}

export interface LLMGuidance {
  t: number;
  timestamp: string;
  strategy: {
    priorityZones?: PriorityZone[];
    defensiveLines?: DefensiveLine[][];
    notes: string;
  };
}

export interface RunSummary {
  runId: string;
  startTime: string;
  endTime?: string;
  status: 'running' | 'paused' | 'completed' | 'failed';
  config: SimulationConfig;
  metrics: {
    totalReturn: number;
    areaBurned: number;
    containmentSteps: number;
    idleStepsPerAgent: number;
    completionRate: number;
    totalSteps: number;
  };
  scenario?: {
    fireName: string;
    fireYear: number;
    sizeAcres: number;
  };
}

export interface ControlCommand {
  action: 'pause' | 'resume' | 'step' | 'reset';
  runId: string;
  steps?: number;
}
