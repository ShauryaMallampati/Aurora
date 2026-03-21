import { NextRequest, NextResponse } from 'next/server';

import { listRunMetadata } from '../../_lib/run-data';

interface ExportConfig {
  includeModels: boolean;
  includeSimulationLogs: boolean;
  includeDocumentation: boolean;
  includeWebDemo: boolean;
  maxLogSize: number;
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const config: ExportConfig = await request.json();

    // Validate config
    if (!config || typeof config !== 'object') {
      return NextResponse.json({ error: 'Invalid config' }, { status: 400 });
    }

    // Build the downloadable manifest.
    const manifest = {
      artifactType: 'offline-manifest',
      generatedAt: new Date().toISOString(),
      config,
      availableRuns: listRunMetadata().map((run) => run.runId),
      contents: {
        models: config.includeModels ? ['ppo_model', 'hybrid_llm_model'] : [],
        logs: config.includeSimulationLogs ? ['simulation_logs_*.json'] : [],
        documentation: config.includeDocumentation
          ? ['README.md', 'TRAINING_GUIDE.md', 'ARCHITECTURE.md']
          : [],
        webDemo: config.includeWebDemo ? ['_next build files'] : [],
      },
      version: '1.0.0',
      source: 'AURORA - Wildfire AI Training System',
      isefYear: 2025,
      estimatedSize: calculateSize(config),
      note: 'This endpoint returns a manifest only. No archive is generated server-side.',
    };

    return new NextResponse(JSON.stringify(manifest, null, 2), {
      headers: {
        'Content-Type': 'application/json',
        'Content-Disposition': `attachment; filename="aurora-offline-manifest.json"`,
      },
    });
  } catch (error) {
    console.error('Export error:', error);
    return NextResponse.json({ error: 'Export failed' }, { status: 500 });
  }
}

function calculateSize(config: ExportConfig): string {
  let size = 0;
  if (config.includeModels) size += 250;
  if (config.includeSimulationLogs) size += config.maxLogSize;
  if (config.includeDocumentation) size += 50;
  if (config.includeWebDemo) size += 100;
  return `${size} MB`;
}
