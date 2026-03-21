import fs from 'node:fs';
import path from 'node:path';

import type { Drone, LLMGuidance, SimulationConfig, TelemetryTick } from '../../../shared/types';
import { findPresetScenarioById } from '../../../shared/scenarios';

export interface SimSession {
  runId: string;
  config: SimulationConfig;
  createdAt: number;
  currentStep: number;
  stepBudget: number;
  paused: boolean;
  status: 'starting' | 'running' | 'paused' | 'completed';
  speed: number;
}

const SESSION_DIR = path.join(process.cwd(), '.aurora-sim-sessions');

const globalSessions = globalThis as typeof globalThis & {
  __auroraSimSessions?: Map<string, SimSession>;
};

const sessions = globalSessions.__auroraSimSessions ?? new Map<string, SimSession>();
globalSessions.__auroraSimSessions = sessions;

function ensureSessionDirectory() {
  fs.mkdirSync(SESSION_DIR, { recursive: true });
}

function getSessionFilePath(runId: string) {
  ensureSessionDirectory();
  return path.join(SESSION_DIR, `${runId}.json`);
}

function persistSession(session: SimSession) {
  sessions.set(session.runId, session);
  fs.writeFileSync(getSessionFilePath(session.runId), JSON.stringify(session), 'utf8');
}

function hydrateSession(runId: string): SimSession | null {
  const cached = sessions.get(runId);
  if (cached) {
    return cached;
  }

  const sessionFile = getSessionFilePath(runId);
  if (!fs.existsSync(sessionFile)) {
    return null;
  }

  try {
    const session = JSON.parse(fs.readFileSync(sessionFile, 'utf8')) as SimSession;
    sessions.set(runId, session);
    return session;
  } catch (error) {
    console.error('Failed to read simulation session from disk:', error);
    return null;
  }
}

export function createSession(config: SimulationConfig): SimSession {
  const runId = `sim_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  const session: SimSession = {
    runId,
    config,
    createdAt: Date.now(),
    currentStep: 0,
    stepBudget: 0,
    paused: false,
    status: 'starting',
    speed: 1,
  };

  persistSession(session);
  return session;
}

export function getSession(runId: string): SimSession | null {
  return hydrateSession(runId);
}

export function updateSession(
  runId: string,
  patch: Partial<Pick<SimSession, 'paused' | 'status' | 'speed' | 'currentStep' | 'stepBudget'>>,
): SimSession | null {
  const session = hydrateSession(runId);
  if (!session) {
    return null;
  }

  Object.assign(session, patch);
  persistSession(session);
  return session;
}

export function deleteSession(runId: string): void {
  sessions.delete(runId);
  const sessionFile = getSessionFilePath(runId);
  if (fs.existsSync(sessionFile)) {
    fs.rmSync(sessionFile, { force: true });
  }
}

export function buildTick(session: SimSession, step: number): TelemetryTick {
  const maxSteps = session.config.maxSteps ?? 150;
  const numDrones = session.config.numDrones ?? 3;
  const scenario = resolveScenarioProfile(session.config);
  const fireOrigin = scenario.origin;
  const weather = scenario.weather;
  const gridSize = 64;
  const centerX = 32;
  const centerY = 32;
  const fireGrid: number[][] = [];
  const initialRadius = scenario.initialRadius;
  const windResistance = 1 + weather.windSpeed / 18;
  const humidityModifier = 1 - weather.humidity * 0.35;
  const suppressionRate = (0.18 * (numDrones / 3) * Math.max(0.6, humidityModifier)) / windResistance;
  const fireRadius = Math.max(0, initialRadius - step * suppressionRate);
  const normalizedRadius = initialRadius > 0 ? fireRadius / initialRadius : 0;
  const intensityScale = Math.max(0, normalizedRadius ** 0.9);

  for (let y = 0; y < gridSize; y++) {
    const row: number[] = [];
    for (let x = 0; x < gridSize; x++) {
      const dist = Math.sqrt((x - centerX) ** 2 + (y - centerY) ** 2);
      const intensity = fireRadius > 0 ? Math.max(0, 1 - dist / fireRadius) * intensityScale : 0;
      const noise = Math.sin(x * 0.5 + step * 0.1) * Math.cos(y * 0.5 + step * 0.1) * 0.15;

      row.push(dist < fireRadius && intensity > 0 ? Math.min(1, Math.max(0, intensity + noise)) : 0);
    }
    fireGrid.push(row);
  }

  const drones: Drone[] = Array.from({ length: numDrones }, (_, index) => ({
    id: index,
    lat: fireOrigin.lat + (Math.sin((step + index * 120) / 10) * 15) / 111,
    lng:
      fireOrigin.lng +
      (Math.cos((step + index * 120) / 10) * 15) /
        (111 * Math.cos((fireOrigin.lat * Math.PI) / 180)),
    battery: Math.max(0.2, 1 - step / maxSteps),
    water: Math.max(0, 0.8 - (step / maxSteps) * 1.2),
    action:
      fireRadius <= 1
        ? 'idle'
        : fireRadius <= initialRadius * 0.3
          ? ['drop', 'scout', 'idle', 'move'][index % 4]
          : ['drop', 'scout', 'drop', 'idle'][index % 4],
    heading: (step * 3 + index * 120) % 360,
  }));

  const burningCells = fireGrid.flat().filter((value) => value > 0.12).length;
  const totalCells = gridSize * gridSize;
  const containment = Math.min(1, Math.max(0, 1 - normalizedRadius));
  const waterDropped = step * numDrones * 1.5;

  return {
    t: step,
    timestamp: new Date(Date.now() + step * 1000).toISOString(),
    drones,
    weather,
    metrics: {
      burnedArea: (burningCells / totalCells) * 100,
      firePerimeter: Math.sqrt(burningCells) * 0.1,
      containment,
      avgIntensity: fireGrid.flat().reduce((sum, value) => sum + value, 0) / totalCells,
      waterDropped,
    },
    events: step % 10 === 0
      ? [
          {
            type: 'drop',
            agent: `D${Math.floor(step / 10) % numDrones}`,
            x: 32,
            y: 32,
            message: `Drone ${Math.floor(step / 10) % numDrones} deployed water`,
          },
        ]
      : [],
    fireGrid: Buffer.from(JSON.stringify(fireGrid)).toString('base64'),
    fireOrigin,
  };
}

export function buildGuidance(session: SimSession, step: number): LLMGuidance {
  const fireOrigin = resolveScenarioProfile(session.config).origin;
  return {
    t: step,
    timestamp: new Date(Date.now() + step * 1000).toISOString(),
    strategy: {
      priorityZones: [
        { lat: fireOrigin.lat + 0.002, lng: fireOrigin.lng + 0.002, radius: 500 },
        { lat: fireOrigin.lat - 0.002, lng: fireOrigin.lng - 0.001, radius: 300 },
      ],
      defensiveLines: [
        [
          { lat: fireOrigin.lat + 0.001, lng: fireOrigin.lng - 0.005 },
          { lat: fireOrigin.lat + 0.001, lng: fireOrigin.lng - 0.002 },
          { lat: fireOrigin.lat + 0.001, lng: fireOrigin.lng + 0.001 },
        ],
      ],
      notes: 'Focus suppression on high-intensity zones near the fire perimeter.',
    },
  };
}

function resolveScenarioProfile(config: SimulationConfig): {
  origin: { lat: number; lng: number };
  initialRadius: number;
  weather: {
    windSpeed: number;
    windDir: number;
    temp: number;
    humidity: number;
  };
} {
  const defaultOrigin = { lat: 36.7783, lng: -119.4179 };
  const defaultWeather = {
    windSpeed: 7.2,
    windDir: 290,
    temp: 35,
    humidity: 0.23,
  };

  if (config.scenarioId === 'custom' && config.customScenario) {
    const sizeToRadius = {
      small: 10,
      medium: 16,
      large: 22,
      extreme: 28,
    } as const;

    return {
      origin: {
        lat: config.customScenario.lat,
        lng: config.customScenario.lng,
      },
      initialRadius: sizeToRadius[config.customScenario.fireSize],
      weather: {
        windSpeed: config.customScenario.windSpeed,
        windDir: config.customScenario.windDir,
        temp: config.customScenario.temp,
        humidity: config.customScenario.humidity,
      },
    };
  }

  if (!config.scenarioId || config.scenarioId === 'random') {
    return {
      origin: defaultOrigin,
      initialRadius: 18,
      weather: defaultWeather,
    };
  }

  const preset = findPresetScenarioById(config.scenarioId);
  if (preset) {
    return {
      origin: { lat: preset.lat, lng: preset.lng },
      initialRadius: preset.initialRadius,
      weather: preset.weather,
    };
  }

  return {
    origin: defaultOrigin,
    initialRadius: 18,
    weather: defaultWeather,
  };
}
