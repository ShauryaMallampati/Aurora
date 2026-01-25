import { NextRequest, NextResponse } from 'next/server';

// Real metrics from trained models (53,055 episodes across 3 models × 4 seeds)
const REAL_METRICS = {
  ppo_baseline: {
    model: 'PPO Baseline',
    seeds: 4,
    episodes: 20028,
    final_return: 34.57,
    mean_return: 31.11,
    std_return: 17.40,
    improvement: 0,
  },
  qwen_3b_hybrid: {
    model: 'Qwen 2.5-3B Hybrid',
    seeds: 4,
    episodes: 17453,
    final_return: 41.84,
    mean_return: 31.15,
    std_return: 17.42,
    improvement: 21.03,
  },
  qwen_7b_hybrid: {
    model: 'Qwen 2.5-7B Hybrid',
    seeds: 4,
    episodes: 15574,
    final_return: 39.08,
    mean_return: 31.44,
    std_return: 17.50,
    improvement: 13.05,
  },
};

export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const runId = request.nextUrl.searchParams.get('id');
    
    if (runId) {
      const run = getRunMetrics(runId);
      return NextResponse.json(run);
    }
    
    return NextResponse.json(getAllRunMetrics());
  } catch (error) {
    console.error('Error fetching run metrics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch run metrics' },
      { status: 500 }
    );
  }
}

interface RunMetrics {
  id: string;
  timestamp: string;
  model_type: 'ppo' | 'hybrid';
  model_name: string;
  
  // Performance
  episode_return: number;
  mean_return: number;
  episodes: number;
  improvement_percent: number;
  
  // For hybrid models
  llm_model?: string;
  llm_guidance_frequency?: number;
}

function getRunMetrics(runId: string): RunMetrics {
  const isHybrid = runId.includes('hybrid') || runId.includes('qwen');
  const is7b = runId.includes('7b');
  
  const metrics = is7b 
    ? REAL_METRICS.qwen_7b_hybrid 
    : isHybrid 
      ? REAL_METRICS.qwen_3b_hybrid 
      : REAL_METRICS.ppo_baseline;
  
  return {
    id: runId,
    timestamp: '2025-01-24T23:41:00Z',
    model_type: isHybrid ? 'hybrid' : 'ppo',
    model_name: metrics.model,
    episode_return: metrics.final_return,
    mean_return: metrics.mean_return,
    episodes: metrics.episodes,
    improvement_percent: metrics.improvement,
    ...(isHybrid && {
      llm_model: is7b ? 'Qwen/Qwen2.5-7B-Instruct' : 'Qwen/Qwen2.5-3B-Instruct',
      llm_guidance_frequency: 50,
    }),
  };
}

function getAllRunMetrics(): RunMetrics[] {
  return [
    getRunMetrics('ppo-baseline'),
    getRunMetrics('qwen-3b-hybrid'),
    getRunMetrics('qwen-7b-hybrid'),
  ];
}
