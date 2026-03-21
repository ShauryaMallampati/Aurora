import { NextRequest, NextResponse } from 'next/server';

import { buildTrainingMetricsPayload } from '../../_lib/run-data';

export const dynamic = 'force-dynamic';

export async function GET(_request: NextRequest): Promise<NextResponse> {
  try {
    return NextResponse.json(buildTrainingMetricsPayload());
  } catch (error) {
    console.error('Error fetching training metrics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch metrics', details: String(error) },
      { status: 500 },
    );
  }
}
