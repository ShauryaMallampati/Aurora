/**
 * API Route: GET /api/runs/compare
 * Get matched PPO and Hybrid runs for comparison
 */

import { NextRequest, NextResponse } from 'next/server';

// Fake run data - would load actual results in production
const MOCK_RUNS = {
  ppo: {
    runId: 'ppo_camp-fire-2018_42',
    modelType: 'ppo' as const,
    seed: 42,
    timestamp: new Date(Date.now() - 86400000).toISOString(),
    config: { scenarioId: 'camp-fire-2018', numDrones: 4 },
    ticks: Array.from({ length: 200 }, (_, t) => ({
      t,
      timestamp: new Date(Date.now() - 86400000 + t * 1000).toISOString(),
      drones: Array.from({ length: 4 }, (_, d) => ({
        id: d,
        lat: 38.8 + Math.sin((t * 0.1 + d * Math.PI / 2) % (2 * Math.PI)) * 0.1,
        lng: -120.8 + Math.cos((t * 0.1 + d * Math.PI / 2) % (2 * Math.PI)) * 0.1,
        battery: Math.max(0, 1 - (t / 200) * 0.7),
        water: Math.max(0, 1 - (t / 200) * 0.8),
        action: t % 5 === 0 ? 'drop' : 'scout',
        heading: ((((t * 0.1 + d * Math.PI / 2) % (2 * Math.PI)) * 180) / Math.PI),
      })),
      weather: {
        windSpeed: 5 + Math.sin(t * 0.05) * 3,
        windDir: (45 + t * 0.1) % 360,
        temp: 35 + Math.sin(t * 0.02) * 5,
        humidity: 0.3 + Math.sin(t * 0.03) * 0.2,
      },
      metrics: {
        burnedArea: Math.round(50 * (0.8 - t / 200 * 0.5) * (1 - 0.15) * t),
        firePerimeter: Math.round(Math.sqrt(50 * (0.8 - t / 200 * 0.5) * (1 - 0.15) * t) * 3),
        containment: Math.min(1, (t / 200) * 1),
        avgIntensity: Math.max(0, 0.8 - t / 200 * 0.5),
        waterDropped: Math.round(1000 * (0.8 - t / 200 * 0.5) * t),
      },
      events: [],
      fireGrid: '',
      fireOrigin: { lat: 38.8, lng: -120.8 },
    })),
    summary: {
      totalSteps: 200,
      totalBurnedArea: 5428,
      totalWaterUsed: 187500,
      containmentTime: 140,
      successRate: 0.75,
      avgReturnPerStep: 2.5,
    },
  },
  hybrid: {
    runId: 'hybrid_camp-fire-2018_42',
    modelType: 'hybrid' as const,
    seed: 42,
    timestamp: new Date(Date.now() - 85600000).toISOString(),
    config: { scenarioId: 'camp-fire-2018', numDrones: 4, llmCadence: 50 },
    ticks: Array.from({ length: 200 }, (_, t) => ({
      t,
      timestamp: new Date(Date.now() - 85600000 + t * 1000).toISOString(),
      drones: Array.from({ length: 4 }, (_, d) => ({
        id: d,
        lat: 38.8 + Math.sin((t * 0.1 + d * Math.PI / 2) % (2 * Math.PI)) * 0.1,
        lng: -120.8 + Math.cos((t * 0.1 + d * Math.PI / 2) % (2 * Math.PI)) * 0.1,
        battery: Math.max(0, 1 - (t / 200) * 0.7),
        water: Math.max(0, 1 - (t / 200) * 0.8),
        action: t % 5 === 0 ? 'drop' : 'scout',
        heading: ((((t * 0.1 + d * Math.PI / 2) % (2 * Math.PI)) * 180) / Math.PI),
      })),
      weather: {
        windSpeed: 5 + Math.sin(t * 0.05) * 3,
        windDir: (45 + t * 0.1) % 360,
        temp: 35 + Math.sin(t * 0.02) * 5,
        humidity: 0.3 + Math.sin(t * 0.03) * 0.2,
      },
      metrics: {
        burnedArea: Math.round(50 * (0.8 - t / 200 * 0.5) * 1.15 * (1 - 0.15) * t * 0.75),
        firePerimeter: Math.round(Math.sqrt(50 * (0.8 - t / 200 * 0.5) * 1.15 * (1 - 0.15) * t * 0.75) * 3),
        containment: Math.min(1, (t / 200) * 1.2),
        avgIntensity: Math.max(0, (0.8 - t / 200 * 0.5) * 0.9),
        waterDropped: Math.round(1000 * (0.8 - t / 200 * 0.5) * 0.9 * t),
      },
      events: [],
      fireGrid: '',
      fireOrigin: { lat: 38.8, lng: -120.8 },
    })),
    summary: {
      totalSteps: 200,
      totalBurnedArea: Math.round(5428 * 0.75),
      totalWaterUsed: Math.round(187500 * 0.85),
      containmentTime: 110,
      successRate: 0.88,
      avgReturnPerStep: 3.2,
    },
  },
};

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const scenario = searchParams.get('scenario');
    const seed = searchParams.get('seed') ? parseInt(searchParams.get('seed')!) : undefined;

    // In production, find matching pair from database
    // For now, return mock data
    const ppo = MOCK_RUNS.ppo;
    const hybrid = MOCK_RUNS.hybrid;

    // Verify they match scenario and seed if specified
    if (scenario && (ppo.config.scenarioId !== scenario || hybrid.config.scenarioId !== scenario)) {
      return NextResponse.json(
        { error: 'No matching runs found for scenario' },
        { status: 404 }
      );
    }

    if (seed && (ppo.seed !== seed || hybrid.seed !== seed)) {
      return NextResponse.json(
        { error: 'No matching runs found for seed' },
        { status: 404 }
      );
    }

    return NextResponse.json({ ppo, hybrid });
  } catch (error) {
    console.error('Error comparing runs:', error);
    return NextResponse.json(
      { error: 'Failed to compare runs' },
      { status: 500 }
    );
  }
}
