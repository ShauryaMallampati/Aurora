/**
 * API Route: GET /api/runs/compare
 * Get matched PPO and Hybrid runs for comparison.
 */

import { NextRequest, NextResponse } from 'next/server';

import { getComparisonRuns } from '../../_lib/run-data';
import { calculateComparisonMetrics } from '../../../../shared/runsDataLoader';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const scenario = searchParams.get('scenario') || undefined;
    const seedParam = searchParams.get('seed');
    const seed = seedParam ? parseInt(seedParam, 10) : undefined;

    if (seedParam && Number.isNaN(seed)) {
      return NextResponse.json({ error: 'Invalid seed filter' }, { status: 400 });
    }

    const pair = getComparisonRuns({ scenario, seed });
    if (!pair) {
      return NextResponse.json({ error: 'No matching runs found' }, { status: 404 });
    }

    return NextResponse.json({
      ppo: pair.ppo,
      hybrid: pair.hybrid,
      metrics: calculateComparisonMetrics(pair.ppo, pair.hybrid),
    });
  } catch (error) {
    console.error('Error comparing runs:', error);
    return NextResponse.json(
      { error: 'Failed to compare runs' },
      { status: 500 },
    );
  }
}
