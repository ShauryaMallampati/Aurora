import { NextRequest, NextResponse } from 'next/server';

import { createSession } from '../session-store';
import type { SimulationConfig } from '../../../../shared/types';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  try {
    const config: SimulationConfig = await request.json();

    if (!config || !config.model || !config.numDrones || !config.seed) {
      return NextResponse.json({ error: 'Invalid simulation config' }, { status: 400 });
    }

    const session = createSession(config);

    return NextResponse.json({
      runId: session.runId,
      sseUrl: `/api/sim/stream/${session.runId}`,
    });
  } catch (error) {
    console.error('Failed to start simulation session:', error);
    return NextResponse.json(
      { error: 'Failed to start simulation session' },
      { status: 500 },
    );
  }
}
