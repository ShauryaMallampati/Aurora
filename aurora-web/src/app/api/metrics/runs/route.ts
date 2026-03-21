import { NextRequest, NextResponse } from 'next/server';

import { buildRunMetricsPayload } from '../../_lib/run-data';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const runId = request.nextUrl.searchParams.get('id') || undefined;
    return NextResponse.json(buildRunMetricsPayload(runId));
  } catch (error) {
    if (error instanceof Error && error.message.startsWith('Run not found:')) {
      return NextResponse.json({ error: error.message }, { status: 404 });
    }

    console.error('Error fetching run metrics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch run metrics' },
      { status: 500 },
    );
  }
}
