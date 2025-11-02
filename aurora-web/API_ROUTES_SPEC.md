/**
 * API Routes for Runs Data
 * 
 * These endpoints should be implemented in the backend to support the Split View Comparison.
 * Example Next.js API route implementations are provided.
 * 
 * Location: /aurora-web/src/app/api/
 */

/**
 * GET /api/runs
 * 
 * List all available simulation runs
 * 
 * Query Parameters:
 *   - model: 'ppo' | 'hybrid' (optional) - Filter by model type
 *   - scenario: string (optional) - Filter by scenario ID
 * 
 * Response:
 * [
 *   {
 *     runId: "ppo_camp-fire-2018_42",
 *     modelType: "ppo",
 *     seed: 42,
 *     timestamp: "2025-10-27T10:30:00Z",
 *     totalSteps: 200,
 *     scenarioId: "camp-fire-2018"
 *   }
 * ]
 */

/**
 * GET /api/runs/:id
 * 
 * Get full simulation run data including all ticks
 * 
 * Response:
 * {
 *   runId: "ppo_camp-fire-2018_42",
 *   modelType: "ppo",
 *   seed: 42,
 *   timestamp: "2025-10-27T10:30:00Z",
 *   config: {
 *     scenarioId: "camp-fire-2018",
 *     numDrones: 4,
 *     llmCadence: 50
 *   },
 *   ticks: [
 *     {
 *       t: 0,
 *       timestamp: "2025-10-27T10:30:00Z",
 *       drones: [
 *         {
 *           id: 0,
 *           lat: 38.8,
 *           lng: -120.8,
 *           battery: 1.0,
 *           water: 1.0,
 *           action: "scout",
 *           heading: 45
 *         }
 *       ],
 *       weather: {
 *         windSpeed: 5.2,
 *         windDir: 90,
 *         temp: 35,
 *         humidity: 0.3
 *       },
 *       metrics: {
 *         burnedArea: 150,
 *         firePerimeter: 45.2,
 *         containment: 0.1,
 *         avgIntensity: 0.8,
 *         waterDropped: 2000
 *       },
 *       events: [],
 *       fireGrid: "...",
 *       fireOrigin: { lat: 38.8, lng: -120.8 }
 *     }
 *   ],
 *   summary: {
 *     totalSteps: 200,
 *     totalBurnedArea: 5000,
 *     totalWaterUsed: 150000,
 *     containmentTime: 140,
 *     successRate: 0.75,
 *     avgReturnPerStep: 2.5
 *   }
 * }
 */

// Example implementation with mock data loading from filesystem:

import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

interface RunMetadata {
  runId: string;
  modelType: 'ppo' | 'hybrid';
  seed: number;
  timestamp: string;
  totalSteps: number;
  scenarioId?: string;
}

// GET /api/runs
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const model = searchParams.get('model') as 'ppo' | 'hybrid' | null;
  const scenario = searchParams.get('scenario');

  try {
    // Load runs from filesystem (in /results or /logs directory)
    const runsDir = path.join(process.cwd(), '..', '..', 'results', 'runs');
    
    if (!fs.existsSync(runsDir)) {
      // Return mock data if directory doesn't exist
      return NextResponse.json([
        {
          runId: 'ppo_camp-fire-2018_42',
          modelType: 'ppo',
          seed: 42,
          timestamp: new Date().toISOString(),
          totalSteps: 200,
          scenarioId: 'camp-fire-2018',
        },
        {
          runId: 'hybrid_camp-fire-2018_42',
          modelType: 'hybrid',
          seed: 42,
          timestamp: new Date().toISOString(),
          totalSteps: 200,
          scenarioId: 'camp-fire-2018',
        },
      ]);
    }

    // Read runs from filesystem
    const runs: RunMetadata[] = [];
    const files = fs.readdirSync(runsDir);

    for (const file of files) {
      if (file.endsWith('.json')) {
        const data = JSON.parse(fs.readFileSync(path.join(runsDir, file), 'utf-8'));
        
        // Apply filters
        if (model && data.modelType !== model) continue;
        if (scenario && data.config?.scenarioId !== scenario) continue;
        
        runs.push({
          runId: data.runId,
          modelType: data.modelType,
          seed: data.seed,
          timestamp: data.timestamp,
          totalSteps: data.ticks?.length || 0,
          scenarioId: data.config?.scenarioId,
        });
      }
    }

    return NextResponse.json(runs);
  } catch (error) {
    console.error('Error fetching runs:', error);
    return NextResponse.json(
      { error: 'Failed to fetch runs' },
      { status: 500 }
    );
  }
}
