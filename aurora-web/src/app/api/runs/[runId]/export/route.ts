import { NextRequest, NextResponse } from 'next/server';

import { getRunById } from '../../../_lib/run-data';
import type { SimulationRun } from '../../../../../shared/runsDataLoader';

export const dynamic = 'force-dynamic';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ runId: string }> },
) {
  try {
    const { runId } = await params;
    const format = request.nextUrl.searchParams.get('format') || 'json';
    const run = getRunById(runId);

    if (!run) {
      return NextResponse.json({ error: 'Run not found' }, { status: 404 });
    }

    if (format === 'csv') {
      const csv = buildRunCsv(run);
      return new NextResponse(csv, {
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': `attachment; filename="${runId}.csv"`,
        },
      });
    }

    return new NextResponse(JSON.stringify(run, null, 2), {
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Disposition': `attachment; filename="${runId}.json"`,
      },
    });
  } catch (error) {
    console.error('Error exporting run:', error);
    return NextResponse.json(
      { error: 'Failed to export run' },
      { status: 500 },
    );
  }
}

function buildRunCsv(run: SimulationRun): string {
  const header = ['step', 'timestamp', 'burnedArea', 'waterDropped', 'containment', 'avgIntensity'];
  const lines = [header.join(',')];

  for (const tick of run.ticks) {
    lines.push([
      tick.t,
      tick.timestamp,
      tick.metrics.burnedArea,
      tick.metrics.waterDropped,
      tick.metrics.containment,
      tick.metrics.avgIntensity,
    ].join(','));
  }

  return lines.join('\n');
}
