/**
 * API Route: GET /api/runs
 * List all available simulation runs with optional filtering
 */

import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const modelType = searchParams.get('model'); // 'ppo' | 'hybrid'
    const scenario = searchParams.get('scenario');

    // Mock data for now (prod would load from results/aurora_runs.json)
    const mockRuns = [
      {
        runId: 'ppo_camp-fire-2018_42',
        modelType: 'ppo',
        seed: 42,
        timestamp: new Date(Date.now() - 86400000).toISOString(),
        totalSteps: 200,
        scenarioId: 'camp-fire-2018',
        totalBurnedArea: 5428,
        totalWaterUsed: 187500,
        containmentTime: 140,
        successRate: 0.75,
      },
      {
        runId: 'hybrid_camp-fire-2018_42',
        modelType: 'hybrid',
        seed: 42,
        timestamp: new Date(Date.now() - 85600000).toISOString(),
        totalSteps: 200,
        scenarioId: 'camp-fire-2018',
        totalBurnedArea: 4071,
        totalWaterUsed: 159375,
        containmentTime: 110,
        successRate: 0.88,
      },
    ];

    let runs = mockRuns;

    if (modelType) {
      runs = runs.filter(r => r.modelType === modelType);
    }

    if (scenario) {
      runs = runs.filter(r => r.scenarioId === scenario);
    }

    return NextResponse.json(runs);
  } catch (error) {
    console.error('Error listing runs:', error);
    return NextResponse.json(
      { error: 'Failed to list runs' },
      { status: 500 }
    );
  }
}
