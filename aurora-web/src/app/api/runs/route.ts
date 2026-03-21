/**
 * API Route: GET /api/runs
 * List all available simulation runs with optional filtering.
 */

import { NextRequest, NextResponse } from 'next/server';

import { listRunMetadata } from '../_lib/run-data';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const modelType = searchParams.get('model');
    const scenario = searchParams.get('scenario');

    if (modelType && modelType !== 'ppo' && modelType !== 'hybrid') {
      return NextResponse.json({ error: 'Invalid model filter' }, { status: 400 });
    }

    return NextResponse.json(
      listRunMetadata({
        modelType: modelType as 'ppo' | 'hybrid' | undefined,
        scenario: scenario || undefined,
      }),
    );
  } catch (error) {
    console.error('Error listing runs:', error);
    return NextResponse.json(
      { error: 'Failed to list runs' },
      { status: 500 },
    );
  }
}
