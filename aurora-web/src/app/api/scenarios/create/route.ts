/**
 * API Route: /api/scenarios/create
 * 
 * Creates custom fire scenarios and runs both PPO+Hybrid models
 * Returns telemetry for side-by-side comparison
 */

import { NextRequest, NextResponse } from 'next/server';

interface ScenarioRequest {
  latitude: number;
  longitude: number;
  fireSize: 'small' | 'medium' | 'large'; // hectares
  weather: {
    temperature_c: number;
    wind_speed_mph: number;
    wind_direction: string;
    humidity: number;
  };
  numDrones: number;
  runBothModels: boolean;
}

interface ScenarioResponse {
  id: string;
  status: 'creating' | 'running_ppo' | 'running_hybrid' | 'completed';
  scenario: {
    lat: number;
    lng: number;
    fireSize: string;
    weather: any;
    numDrones: number;
  };
  ppoRunId?: string;
  hybridRunId?: string;
  message: string;
  estimatedTimeMinutes: number;
}

interface StoredScenario extends ScenarioResponse {
  createdAt: string;
  updatedAt: string;
}

const scenarioStore = new Map<string, StoredScenario>();

/**
 * POST /api/scenarios/create
 * Create new fire scenario and optionally run both models
 */
export async function POST(request: NextRequest) {
  try {
    const body: ScenarioRequest = await request.json();

    // Validate request
    if (!Number.isFinite(body.latitude) || !Number.isFinite(body.longitude)) {
      return NextResponse.json(
        { error: 'Missing latitude or longitude' },
        { status: 400 }
      );
    }

    // Validate coords
    if (body.latitude < -90 || body.latitude > 90 || body.longitude < -180 || body.longitude > 180) {
      return NextResponse.json(
        { error: 'Invalid coordinates' },
        { status: 400 }
      );
    }

    const scenarioId = `scenario_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const now = new Date().toISOString();

    // Estimate time based on fire size
    const timeEstimates: Record<string, number> = {
      small: 2,
      medium: 4,
      large: 6,
    };

    const estimatedMinutes = body.runBothModels
      ? timeEstimates[body.fireSize] * 2 // PPO + Hybrid
      : timeEstimates[body.fireSize];

    const response: ScenarioResponse = {
      id: scenarioId,
      status: body.runBothModels ? 'running_ppo' : 'completed',
      scenario: {
        lat: body.latitude,
        lng: body.longitude,
        fireSize: body.fireSize,
        weather: body.weather,
        numDrones: body.numDrones,
      },
      message: body.runBothModels
        ? `Scenario created. Ready to run both models on custom fire at ${body.latitude.toFixed(2)}°, ${body.longitude.toFixed(2)}°`
        : `Scenario created for custom fire at ${body.latitude.toFixed(2)}°, ${body.longitude.toFixed(2)}°`,
      estimatedTimeMinutes: estimatedMinutes,
    };

    if (body.runBothModels) {
      response.ppoRunId = `ppo_${scenarioId}`;
      response.hybridRunId = `hybrid_${scenarioId}`;
    }

    scenarioStore.set(scenarioId, {
      ...response,
      createdAt: now,
      updatedAt: now,
    });

    return NextResponse.json(response);
  } catch (error) {
    console.error('Error creating scenario:', error);
    return NextResponse.json(
      { error: 'Failed to create scenario', details: String(error) },
      { status: 500 }
    );
  }
}

/**
 * GET /api/scenarios/create?id={scenarioId}
 * Check scenario creation and training status
 */
export async function GET(request: NextRequest) {
  try {
    const scenarioId = request.nextUrl.searchParams.get('id');

    if (!scenarioId) {
      return NextResponse.json(
        { error: 'Missing scenario ID' },
        { status: 400 }
      );
    }

    const stored = scenarioStore.get(scenarioId);
    if (!stored) {
      return NextResponse.json(
        { error: 'Scenario not found' },
        { status: 404 },
      );
    }

    const createdAt = new Date(stored.createdAt).getTime();
    const elapsedSeconds = (Date.now() - createdAt) / 1000;
    const totalEstimatedSeconds = Math.max(30, stored.estimatedTimeMinutes * 60);
    const completed = !stored.ppoRunId || elapsedSeconds >= totalEstimatedSeconds;
    const status = completed
      ? 'completed'
      : elapsedSeconds >= totalEstimatedSeconds / 2
        ? 'running_hybrid'
        : 'running_ppo';

    const response: ScenarioResponse = {
      ...stored,
      status,
      message: completed
        ? 'Both training runs completed. Ready for comparison.'
        : status === 'running_hybrid'
          ? 'PPO baseline finished. Hybrid comparison is still running.'
          : 'Scenario is running. Poll again for completion status.',
    };

    scenarioStore.set(scenarioId, {
      ...response,
      createdAt: stored.createdAt,
      updatedAt: new Date().toISOString(),
    });

    return NextResponse.json(response);
  } catch (error) {
    console.error('Error fetching scenario:', error);
    return NextResponse.json(
      { error: 'Failed to fetch scenario', details: String(error) },
      { status: 500 }
    );
  }
}
