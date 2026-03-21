// Backend API client.

import type {
  SimulationConfig,
  StartSimResponse,
  TelemetryTick,
  LLMGuidance,
  RunSummary,
  ControlCommand,
  Drone,
} from "./types";

const API_ROOT = '/api';

// SSE stream handler
export class SimulationStream {
  private eventSource: EventSource | null = null;
  private onTickCallback: ((tick: TelemetryTick) => void) | null = null;
  private onGuidanceCallback: ((guidance: LLMGuidance) => void) | null = null;
  private onErrorCallback: ((error: Error) => void) | null = null;
  private onCompleteCallback: (() => void) | null = null;
  private intervalId: NodeJS.Timeout | null = null;
  public playbackSpeed: number = 1;
  private isPaused: boolean = false;
  private config: SimulationConfig | null = null;

  constructor(private sseUrl: string, private useMock: boolean = false) {}

  setPlaybackSpeed(speed: number) {
    this.playbackSpeed = speed;
    // If already running, restart at new speed
    if (this.intervalId && this.useMock) {
      this.restartMockStream();
    }
  }

  setConfig(config: SimulationConfig) {
    this.config = config;
  }

  pause() {
    this.isPaused = true;
  }

  resume() {
    this.isPaused = false;
  }

  onTick(callback: (tick: TelemetryTick) => void) {
    this.onTickCallback = callback;
    return this;
  }

  onGuidance(callback: (guidance: LLMGuidance) => void) {
    this.onGuidanceCallback = callback;
    return this;
  }

  onError(callback: (error: Error) => void) {
    this.onErrorCallback = callback;
    return this;
  }

  onComplete(callback: () => void) {
    this.onCompleteCallback = callback;
    return this;
  }

  start() {
    if (this.useMock) {
      this.startMockStream();
      return;
    }

    this.eventSource = new EventSource(this.sseUrl);

    this.eventSource.addEventListener('tick', (event) => {
      try {
        const tick: TelemetryTick = JSON.parse(event.data);
        this.onTickCallback?.(tick);
      } catch (error) {
        this.onErrorCallback?.(error as Error);
      }
    });

    this.eventSource.addEventListener('guidance', (event) => {
      try {
        const guidance: LLMGuidance = JSON.parse(event.data);
        this.onGuidanceCallback?.(guidance);
      } catch (error) {
        this.onErrorCallback?.(error as Error);
      }
    });

    this.eventSource.addEventListener('complete', () => {
      this.onCompleteCallback?.();
      this.stop();
    });

    this.eventSource.onerror = (error) => {
      this.onErrorCallback?.(new Error('SSE connection error'));
      this.stop();
    };
  }

  stop() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  // Mock stream for offline demo
  private currentStep = 0;
  
  private startMockStream() {
    this.currentStep = 0;
    this.restartMockStream();
  }

  private restartMockStream() {
    // Stop any running sim
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }

    const maxSteps = this.config?.maxSteps || 150;

    const tick = () => {
      // If paused, don't advance
      if (this.isPaused) {
        return;
      }

      if (this.currentStep >= maxSteps) {
        this.onCompleteCallback?.();
        if (this.intervalId) clearInterval(this.intervalId);
        return;
      }

      // Generate next step
      const tickData = this.generateMockTick(this.currentStep, maxSteps);
      this.onTickCallback?.(tickData);

      // LLM gives guidance every 50 steps (matches training cadence)
      if (this.currentStep % 50 === 0 && this.currentStep > 0) {
        const guidance = this.generateMockGuidance(this.currentStep);
        this.onGuidanceCallback?.(guidance);
      }

      this.currentStep++;
    };

    // Run the sim at the right speed
    const baseInterval = 100; // 10 Hz base
    this.intervalId = setInterval(tick, baseInterval / this.playbackSpeed);
  }

  private generateMockTick(t: number, maxSteps: number): TelemetryTick {
    const gridSize = 64;
    const numDrones = this.config?.numDrones || 3;
    
    // Use fire location from config or default to CA
    const fireOrigin = this.getFireOrigin();

    // Sim fire grid: starts big, shrinks as drones drop water
    const fireGrid: number[][] = [];
    for (let y = 0; y < gridSize; y++) {
      const row: number[] = [];
      for (let x = 0; x < gridSize; x++) {
        const centerX = 32;
        const centerY = 32;
        const dist = Math.sqrt((x - centerX) ** 2 + (y - centerY) ** 2);
        
        // More drones = faster suppression
        const suppressionRate = 0.12 * (numDrones / 3);
        const fireRadius = 18 - t * suppressionRate;
        const intensity = Math.max(0, 1 - (dist / fireRadius));
        
        // Add a little randomness so it feels real
        const noise = Math.sin(x * 0.5 + t * 0.1) * Math.cos(y * 0.5 + t * 0.1) * 0.15;
        
        if (dist < fireRadius && intensity > 0) {
          row.push(Math.min(1, Math.max(0, intensity + noise)));
        } else {
          row.push(0);
        }
      }
      fireGrid.push(row);
    }
    const fireBase64 = btoa(JSON.stringify(fireGrid));

    // Position drones around the fire
    const drones: Drone[] = Array.from({ length: numDrones }, (_, i) => ({
      id: i,
      lat: fireOrigin.lat + (Math.sin((t + i * 120) / 10) * 15) / 111,
      lng: fireOrigin.lng + (Math.cos((t + i * 120) / 10) * 15) / (111 * Math.cos((fireOrigin.lat * Math.PI) / 180)),
      battery: Math.max(0.2, 1 - t / maxSteps), // drains over time
      water: Math.max(0, 0.8 - (t / maxSteps) * 1.2), // used up
      action: ['drop', 'scout', 'idle'][i % 3], // cycle actions
      heading: ((t * 3 + i * 120) % 360), // heading direction
    }));

    // How much fire is still burning
    const burningCells = fireGrid.flat().filter(v => v > 0.3).length;
    const totalCells = gridSize * gridSize;

    return {
      t,
      timestamp: new Date(Date.now() + t * 1000).toISOString(),
      drones,
      weather: {
        windSpeed: 7.2,
        windDir: 290,
        temp: 35,
        humidity: 0.23,
      },
      metrics: {
        burnedArea: (burningCells / totalCells) * 100,
        firePerimeter: Math.sqrt(burningCells) * 0.1,
        containment: Math.min(1, t / 100),
        avgIntensity: fireGrid.flat().reduce((sum, v) => sum + v, 0) / totalCells,
        waterDropped: t * numDrones * 1.5, // scales with drone count
      },
      events: t % 10 === 0 ? [{
        type: 'drop',
        agent: `D${(t / 10) % numDrones}`,
        x: 32,
        y: 32,
        message: `Drone ${(t / 10) % numDrones} deployed water`,
      }] : [],
      fireGrid: fireBase64,
      fireOrigin,
    };
  }

  private getFireOrigin(): { lat: number; lng: number } {
    // Default to CA
    const defaultOrigin = { lat: 36.7783, lng: -119.4179 };
    
    if (!this.config?.scenarioId || this.config.scenarioId === 'random') {
      console.log('🗺️ Using default fire origin:', defaultOrigin);
      return defaultOrigin;
    }

    // Map scenario IDs to coordinates
    const fireLocations: Record<string, { lat: number; lng: number }> = {
      'smokehouse-2024': { lat: 35.8374, lng: -100.6657 },
      'dixie-2021': { lat: 40.211, lng: -121.0471 },
      'august-complex-2020': { lat: 39.7761, lng: -122.8957 },
      'creek-2020': { lat: 37.325, lng: -119.2788 },
      'scu-2020': { lat: 37.3516, lng: -121.4472 },
      'ranch-2018': { lat: 39.2873, lng: -122.768 },
      'thomas-2017': { lat: 34.4503, lng: -119.2869 },
      'biscuit-2002': { lat: 42.2955, lng: -123.9138 },
      'bootleg-2021': { lat: 42.629, lng: -121.0759 },
      'elk-mountain-2007': { lat: 42.1758, lng: -115.3158 },
      'long-draw-2012': { lat: 42.4395, lng: -117.6385 },
      'holloway-2012': { lat: 42.0118, lng: -118.2537 },
      'wallow-2011': { lat: 33.7986, lng: -109.2994 },
      'rodeo-chediski-2002': { lat: 34.2337, lng: -110.4651 },
      'whitewater-baldy-2012': { lat: 33.335, lng: -108.5955 },
      'hermits-peak-2022': { lat: 35.8164, lng: -105.3385 },
      'black-2022': { lat: 33.207, lng: -107.8878 },
      'park-2024': { lat: 40.1171, lng: -121.7987 },
      'i40-2006': { lat: 35.2973, lng: -100.6239 },
      'martin-2018': { lat: 41.6021, lng: -116.9758 },
      'milford-flat-2007': { lat: 38.6928, lng: -112.7377 },
      'rush-2012': { lat: 40.6137, lng: -120.0921 },
      'north-fork-1988': { lat: 44.7064, lng: -110.8147 },
      'clover-mist-1988': { lat: 44.7393, lng: -109.9855 },
      'mustang-2012': { lat: 45.4581, lng: -114.4401 },
      'fire-1910': { lat: 46.4347, lng: -115.1796 },
      'fire-1919': { lat: 46.0566, lng: -115.4081 },
      'hopkins-2020': { lat: 40.2077, lng: -123.2511 },
      'claremont-2020': { lat: 39.7289, lng: -121.196 },
      'hennessey-2020': { lat: 38.6181, lng: -122.239 },
      'durkee-2024': { lat: 44.3819, lng: -117.4845 },
      'rock-house-2011': { lat: 30.6873, lng: -103.9334 },
      'long-butte-2010': { lat: 42.6652, lng: -115.1636 },
      'saddle-draw-2014': { lat: 43.3028, lng: -118.0967 },
    };

    const location = fireLocations[this.config.scenarioId] || defaultOrigin;
    console.log(`🗺️ Fire origin for ${this.config.scenarioId}:`, location);
    return location;
  }

  private generateMockGuidance(t: number): LLMGuidance {
    return {
      t,
      timestamp: new Date(Date.now() + t * 1000).toISOString(),
      strategy: {
        priorityZones: [
          { lat: 36.78, lng: -119.42, radius: 500 },
          { lat: 36.77, lng: -119.41, radius: 300 },
        ],
        defensiveLines: [
          [
            { lat: 36.775, lng: -119.425 },
            { lat: 36.775, lng: -119.420 },
            { lat: 36.775, lng: -119.415 },
          ]
        ],
        notes: 'Wind from WNW at 7.2 m/s. Deploy defensive line to protect southeastern area. Focus suppression on high-intensity zones near center.',
      },
    };
  }
}

// API functions
export async function startSimulation(config: SimulationConfig): Promise<StartSimResponse> {
  const response = await fetch(`${API_ROOT}/sim/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    throw new Error(`Failed to start simulation: ${response.statusText}`);
  }

  return response.json();
}

export async function controlSimulation(command: ControlCommand): Promise<void> {
  const response = await fetch(`${API_ROOT}/sim/control`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(command),
  });

  if (!response.ok) {
    throw new Error(`Failed to control simulation: ${response.statusText}`);
  }
}

export async function listRuns(): Promise<RunSummary[]> {
  const response = await fetch(`${API_ROOT}/runs`);

  if (!response.ok) {
    throw new Error(`Failed to fetch runs: ${response.statusText}`);
  }

  return response.json();
}

export async function getRunDetail(runId: string): Promise<RunSummary> {
  const response = await fetch(`${API_ROOT}/runs/${encodeURIComponent(runId)}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch run detail: ${response.statusText}`);
  }

  return response.json();
}

export async function downloadRunData(runId: string, format: 'json' | 'csv'): Promise<Blob> {
  const response = await fetch(`${API_ROOT}/runs/${encodeURIComponent(runId)}/export?format=${format}`);

  if (!response.ok) {
    throw new Error(`Failed to download run data: ${response.statusText}`);
  }

  return response.blob();
}
