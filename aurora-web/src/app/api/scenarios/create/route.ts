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

/**
 * POST /api/scenarios/create
 * Create new fire scenario and optionally run both models
 */
export async function POST(request: NextRequest) {
  try {
    const body: ScenarioRequest = await request.json();

    // Validate request
    if (!body.latitude || !body.longitude) {
      return NextResponse.json(
        { error: 'Missing latitude or longitude' },
        { status: 400 }
      );
    }

    // Validate coordinates
    if (body.latitude < -90 || body.latitude > 90 || body.longitude < -180 || body.longitude > 180) {
      return NextResponse.json(
        { error: 'Invalid coordinates' },
        { status: 400 }
      );
    }

    const scenarioId = `scenario_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

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
      status: 'creating',
      scenario: {
        lat: body.latitude,
        lng: body.longitude,
        fireSize: body.fireSize,
        weather: body.weather,
        numDrones: body.numDrones,
      },
      message: `Scenario created. Ready to run both models on custom fire at ${body.latitude.toFixed(2)}°, ${body.longitude.toFixed(2)}°`,
      estimatedTimeMinutes: estimatedMinutes,
    };

    // Queue both training runs if requested
    if (body.runBothModels) {
      // In real implementation, this would spawn subprocess jobs
      response.status = 'running_ppo';
      response.ppoRunId = `ppo_${scenarioId}`;
      response.hybridRunId = `hybrid_${scenarioId}`;

      // TODO: Actually spawn training processes
      // For now, just return queued status
    }

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

    // Mock scenario status
    const response: ScenarioResponse = {
      id: scenarioId,
      status: 'completed',
      scenario: {
        lat: 36.7783,
        lng: -119.4179,
        fireSize: 'medium',
        weather: {
          temperature_c: 32,
          wind_speed_mph: 15,
          wind_direction: 'NE',
          humidity: 25,
        },
        numDrones: 4,
      },
      ppoRunId: `ppo_${scenarioId}`,
      hybridRunId: `hybrid_${scenarioId}`,
      message: 'Both training runs completed. Ready for comparison.',
      estimatedTimeMinutes: 8,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('Error fetching scenario:', error);
    return NextResponse.json(
      { error: 'Failed to fetch scenario', details: String(error) },
      { status: 500 }
    );
  }
}
