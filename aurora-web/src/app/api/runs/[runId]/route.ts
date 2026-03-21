import { NextRequest, NextResponse } from 'next/server';

import { getRunById } from '../../_lib/run-data';

export const dynamic = 'force-dynamic';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ runId: string }> },
) {
  try {
    const { runId } = await params;
    const run = getRunById(runId);

    if (!run) {
      return NextResponse.json({ error: 'Run not found' }, { status: 404 });
    }

    return NextResponse.json(run);
  } catch (error) {
    console.error('Error loading run:', error);
    return NextResponse.json(
      { error: 'Failed to load run' },
      { status: 500 },
    );
  }
}
