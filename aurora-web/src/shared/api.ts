// API client for AURORA backend

import type {
  SimulationConfig,
  StartSimResponse,
  TelemetryTick,
  LLMGuidance,
  RunSummary,
  ControlCommand,
  Drone,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

// SSE Stream Handler
export class SimulationStream {
  private eventSource: EventSource | null = null;
  private onTickCallback: ((tick: TelemetryTick) => void) | null = null;
  private onGuidanceCallback: ((guidance: LLMGuidance) => void) | null = null;
  private onErrorCallback: ((error: Error) => void) | null = null;
  private onCompleteCallback: (() => void) | null = null;

  constructor(private sseUrl: string, private useMock: boolean = false) {}

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
  }

  // Mock stream for offline demo
  private startMockStream() {
    let t = 0;
    const maxSteps = 150;

    const interval = setInterval(() => {
      if (t >= maxSteps) {
        this.onCompleteCallback?.();
        clearInterval(interval);
        return;
      }

      // Generate mock tick
      const tick = this.generateMockTick(t, maxSteps);
      this.onTickCallback?.(tick);

      // Generate mock guidance every 50 steps
      if (t % 50 === 0 && t > 0) {
        const guidance = this.generateMockGuidance(t);
        this.onGuidanceCallback?.(guidance);
      }

      t++;
    }, 100); // 10 Hz
  }

  private generateMockTick(t: number, maxSteps: number): TelemetryTick {
    const gridSize = 64;
    const numDrones = 3;

    // Generate mock fire grid (2D array, base64 encoded JSON)
    const fireGrid: number[][] = [];
    for (let y = 0; y < gridSize; y++) {
      const row: number[] = [];
      for (let x = 0; x < gridSize; x++) {
        const centerX = 32;
        const centerY = 32;
        const dist = Math.sqrt((x - centerX) ** 2 + (y - centerY) ** 2);
        
        // Fire starts large and shrinks as drones suppress it
        const fireRadius = 18 - t * 0.12;
        const intensity = Math.max(0, 1 - (dist / fireRadius));
        
        // Add noise for realistic fire
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

    // Generate mock drones
    const drones: Drone[] = Array.from({ length: numDrones }, (_, i) => ({
      id: i,
      lat: 36.7783 + (Math.sin((t + i * 120) / 10) * 15) / 111,
      lng: -119.4179 + (Math.cos((t + i * 120) / 10) * 15) / (111 * Math.cos((36.7783 * Math.PI) / 180)),
      battery: Math.max(0.2, 1 - t / maxSteps),
      water: Math.max(0, 0.8 - (t / maxSteps) * 1.2),
      action: ['drop', 'scout', 'idle'][i % 3],
      heading: ((t * 3 + i * 120) % 360),
    }));

    // Count burning cells
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
        waterDropped: t * 3.5,
      },
      events: t % 10 === 0 ? [{
        type: 'drop',
        agent: `D${(t / 10) % numDrones}`,
        x: 32,
        y: 32,
        message: `Drone ${(t / 10) % numDrones} deployed water`,
      }] : [],
      fireGrid: fireBase64,
      fireOrigin: { lat: 36.7783, lng: -119.4179 },
    };
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

// API Functions
export async function startSimulation(config: SimulationConfig): Promise<StartSimResponse> {
  const response = await fetch(`${API_BASE}/api/sim/start`, {
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
  const response = await fetch(`${API_BASE}/api/sim/control`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(command),
  });

  if (!response.ok) {
    throw new Error(`Failed to control simulation: ${response.statusText}`);
  }
}

export async function listRuns(): Promise<RunSummary[]> {
  const response = await fetch(`${API_BASE}/api/runs`);

  if (!response.ok) {
    throw new Error(`Failed to fetch runs: ${response.statusText}`);
  }

  return response.json();
}

export async function getRunDetail(runId: string): Promise<RunSummary> {
  const response = await fetch(`${API_BASE}/api/runs/${runId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch run detail: ${response.statusText}`);
  }

  return response.json();
}

export async function downloadRunData(runId: string, format: 'json' | 'csv'): Promise<Blob> {
  const response = await fetch(`${API_BASE}/api/runs/${runId}/export?format=${format}`);

  if (!response.ok) {
    throw new Error(`Failed to download run data: ${response.statusText}`);
  }

  return response.blob();
}
