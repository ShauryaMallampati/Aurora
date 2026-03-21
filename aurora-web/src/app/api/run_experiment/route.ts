/**
 * API Route: /api/run_experiment
 * 
 * Handles training experiment execution and live metrics streaming
 * Interfaces with train_manager.py for hybrid PPO+LLM training
 */

import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';

interface ExperimentRequest {
  mode: 'ppo' | 'hybrid';
  phase: 'phase_a' | 'phase_b' | 'phase_c' | 'quick' | 'full';
  resume?: boolean;
  resume_from?: string;
}

interface TrainingMetrics {
  step: number;
  episode_return: number;
  completion_rate: number;
  idle_steps: number;
  llm_latency_ms: number;
  timestamp: string;
}

interface ExperimentResponse {
  id: string;
  mode: string;
  phase: string;
  status: 'starting' | 'running' | 'completed' | 'failed';
  start_time: string;
  elapsed_seconds: number;
  metrics: TrainingMetrics[];
  current_step?: number;
  total_steps?: number;
  message: string;
}

type ExperimentStatus = ExperimentResponse['status'];

type ActiveExperiment = {
  process: any;
  metrics: TrainingMetrics[];
  startTime: number;
  config: ExperimentRequest;
  outputDir: string;
  status: ExperimentStatus;
  exitCode: number | null;
  errorLog: string[];
  stdoutBuffer: string;
};

// In-memory store for active experiments
const activeExperiments = new Map<string, ActiveExperiment>();

// Generate unique experiment ID
function generateExperimentId(): string {
  return `exp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function resolvePythonPath(projectRoot: string): string {
  const candidates = [
    process.env.AURORA_PYTHON_BIN,
    process.env.PYTHON_BIN,
    path.join(projectRoot, '.venv', 'bin', 'python'),
    path.join(projectRoot, 'venv', 'bin', 'python'),
    'python3',
  ].filter((candidate): candidate is string => Boolean(candidate));

  for (const candidate of candidates) {
    if (candidate === 'python3' || fs.existsSync(candidate)) {
      return candidate;
    }
  }

  return 'python3';
}

function resolveResultsPath(projectRoot: string, experimentId: string): string | null {
  const directPath = path.join(projectRoot, 'results', experimentId);
  if (fs.existsSync(directPath)) {
    return directPath;
  }

  const legacyPath = path.join(projectRoot, 'results', `exp_${experimentId}`);
  if (fs.existsSync(legacyPath)) {
    return legacyPath;
  }

  return null;
}

function formatExperimentMessage(experiment: ActiveExperiment): string {
  if (experiment.status === 'failed') {
    const lastError = experiment.errorLog.at(-1);
    return lastError ? `Training failed: ${lastError}` : 'Training failed';
  }

  if (experiment.status === 'completed') {
    return 'Training completed';
  }

  if (experiment.status === 'running') {
    return 'Training in progress';
  }

  return 'Training is starting';
}

/**
 * POST /api/run_experiment
 * Start a new training experiment
 */
export async function POST(request: NextRequest) {
  try {
    const body: ExperimentRequest = await request.json();

    // Validate request
    if (!body.mode || !body.phase) {
      return NextResponse.json(
        { error: 'Missing required fields: mode, phase' },
        { status: 400 }
      );
    }

    const experimentId = generateExperimentId();
    const startTime = Date.now();

    // Vercel/cloud environment check
    if (process.env.VERCEL) {
      return NextResponse.json({
        id: experimentId,
        mode: body.mode,
        phase: body.phase,
        status: 'failed',
        start_time: new Date(startTime).toISOString(),
        elapsed_seconds: 0,
        metrics: [],
        message: 'Training experiments requires a local Python environment and cannot be run on Vercel.',
      } as ExperimentResponse);
    }

    // Build command
    const projectRoot = process.env.AURORA_PROJECT_ROOT || path.resolve(process.cwd(), '..');
    const pythonPath = resolvePythonPath(projectRoot);
    const scriptPath = path.join(projectRoot, 'train_manager.py');
    const outputDir = path.join(projectRoot, 'results', experimentId);

    // Ensure output dir exists
    // Only attempt if not on Vercel (extra safety)
    if (!fs.existsSync(outputDir)) {
      try {
        fs.mkdirSync(outputDir, { recursive: true });
      } catch (e) {
        console.error('Failed to create output directory:', e);
        return NextResponse.json({ error: 'Failed to create output directory' }, { status: 500 });
      }
    }

    const args = [
      scriptPath,
      '--mode', body.mode,
      '--phase', body.phase,
      '--output_dir', outputDir,
    ];

    if (body.resume && body.resume_from) {
      args.push('--resume', body.resume_from);
    }

    // Spawn training process
    const trainProcess = spawn(pythonPath, args, {
      cwd: projectRoot,
      detached: false, // don't detach; we need to monitor it
    });

    // Store experiment metadata
    activeExperiments.set(experimentId, {
      process: trainProcess,
      metrics: [],
      startTime,
      config: body,
      outputDir,
      status: 'starting',
      exitCode: null,
      errorLog: [],
      stdoutBuffer: '',
    });

    // Capture stdout for metrics
    if (trainProcess.stdout) {
      trainProcess.stdout.on('data', (data: Buffer) => {
        parseMetrics(experimentId, data.toString('utf-8'));
      });
    }

    // Capture stderr
    if (trainProcess.stderr) {
      trainProcess.stderr.on('data', (data: Buffer) => {
        const output = data.toString('utf-8').trim();
        const experiment = activeExperiments.get(experimentId);
        if (experiment && output) {
          experiment.errorLog.push(output);
          if (experiment.errorLog.length > 50) {
            experiment.errorLog = experiment.errorLog.slice(-50);
          }
        }
        console.error(`[Experiment ${experimentId}] stderr:`, output);
      });
    }

    trainProcess.on('error', (error: Error) => {
      const experiment = activeExperiments.get(experimentId);
      if (!experiment) {
        return;
      }

      experiment.status = 'failed';
      experiment.exitCode = -1;
      experiment.errorLog.push(error.message);
    });

    // Handle process exit
    trainProcess.on('exit', (code: number | null, signal: NodeJS.Signals | null) => {
      const exp = activeExperiments.get(experimentId);
      if (exp) {
        exp.exitCode = code;
        exp.status = code === 0 ? 'completed' : 'failed';
        const diskMetrics = loadMetricsFromDisk(exp.outputDir);
        if (diskMetrics.length > 0) {
          exp.metrics = diskMetrics;
        }
        if (signal) {
          exp.errorLog.push(`Process terminated with signal ${signal}`);
        }
        if (code === 0) {
          console.log(`✅ Experiment ${experimentId} completed successfully`);
        } else {
          console.error(`❌ Experiment ${experimentId} failed with code ${code}`);
        }
      }
    });

    const elapsedSeconds = (Date.now() - startTime) / 1000;

    return NextResponse.json({
      id: experimentId,
      mode: body.mode,
      phase: body.phase,
      status: 'starting',
      start_time: new Date(startTime).toISOString(),
      elapsed_seconds: elapsedSeconds,
      metrics: [],
      message: `Started ${body.mode.toUpperCase()} training on ${body.phase}. Experiment ID: ${experimentId}`,
    } as ExperimentResponse);

  } catch (error) {
    console.error('Error starting experiment:', error);
    return NextResponse.json(
      { error: 'Failed to start experiment', details: String(error) },
      { status: 500 }
    );
  }
}

/**
 * GET /api/run_experiment?id={experimentId}
 * Get current status and metrics for a training experiment
 */
export async function GET(request: NextRequest) {
  try {
    const experimentId = request.nextUrl.searchParams.get('id');

    if (!experimentId) {
      return NextResponse.json(
        { error: 'Missing experiment ID' },
        { status: 400 }
      );
    }

    const experiment = activeExperiments.get(experimentId);

    if (!experiment) {
      // Check if experiment data exists on disk
      const projectRoot = process.env.AURORA_PROJECT_ROOT || path.resolve(process.cwd(), '..');
      const resultsPath = resolveResultsPath(projectRoot, experimentId);
      
      if (!resultsPath || !fs.existsSync(resultsPath)) {
        return NextResponse.json(
          { error: `Experiment ${experimentId} not found` },
          { status: 404 }
        );
      }

      // Load from disk
      const metadataPath = path.join(resultsPath, 'run_metadata.json');
      if (fs.existsSync(metadataPath)) {
        const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf-8'));
        return NextResponse.json({
          id: experimentId,
          mode: metadata.mode,
          phase: metadata.phase,
          status: metadata.status || 'unknown',
          start_time: metadata.start_time,
          elapsed_seconds: (new Date(metadata.end_time || new Date()).getTime() - new Date(metadata.start_time).getTime()) / 1000,
          metrics: loadMetricsFromDisk(resultsPath),
          message: 'Experiment data loaded from disk',
        } as ExperimentResponse);
      }
    }

    if (experiment) {
      const elapsedSeconds = (Date.now() - experiment.startTime) / 1000;
      const metadataPath = path.join(experiment.outputDir, 'run_metadata.json');
      const hasDiskMetadata = fs.existsSync(metadataPath);

      if (hasDiskMetadata && experiment.status !== 'starting' && experiment.status !== 'running') {
        const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf-8'));
        return NextResponse.json({
          id: experimentId,
          mode: metadata.mode,
          phase: metadata.phase,
          status: metadata.status || experiment.status,
          start_time: metadata.start_time,
          elapsed_seconds: metadata.elapsed_seconds ?? elapsedSeconds,
          metrics: loadMetricsFromDisk(experiment.outputDir),
          current_step: metadata.current_step,
          total_steps: metadata.total_steps,
          message: metadata.error ? `Training failed: ${metadata.error}` : 'Experiment data loaded from disk',
        } as ExperimentResponse);
      }

      return NextResponse.json({
        id: experimentId,
        mode: experiment.config.mode,
        phase: experiment.config.phase,
        status: experiment.status === 'starting' ? 'starting' : experiment.status,
        start_time: new Date(experiment.startTime).toISOString(),
        elapsed_seconds: elapsedSeconds,
        metrics: experiment.metrics,
        current_step: experiment.metrics.at(-1)?.step,
        total_steps: experiment.metrics.at(-1)?.step,
        message: formatExperimentMessage(experiment),
      } as ExperimentResponse);
    }

    return NextResponse.json(
      { error: `Could not find experiment ${experimentId}` },
      { status: 404 }
    );

  } catch (error) {
    console.error('Error fetching experiment:', error);
    return NextResponse.json(
      { error: 'Failed to fetch experiment', details: String(error) },
      { status: 500 }
    );
  }
}

/**
 * Parse metrics from training output
 */
function parseMetrics(experimentId: string, output: string): void {
  const experiment = activeExperiments.get(experimentId);
  if (!experiment) return;

  experiment.status = 'running';
  experiment.stdoutBuffer += output;
  const lines = experiment.stdoutBuffer.split(/\r?\n/);
  experiment.stdoutBuffer = lines.pop() ?? '';

  const metricsRegex = /Step:\s*(\d+).*?Return:\s*([\d.-]+).*?Completion:\s*([\d.-]+).*?Idle:\s*(\d+).*?LLM_Latency:\s*([\d.-]+)/;

  for (const line of lines) {
    const match = line.match(metricsRegex);
    if (!match) {
      continue;
    }

    const metric: TrainingMetrics = {
      step: parseInt(match[1]),
      episode_return: parseFloat(match[2]),
      completion_rate: parseFloat(match[3]),
      idle_steps: parseInt(match[4]),
      llm_latency_ms: parseFloat(match[5]),
      timestamp: new Date().toISOString(),
    };

    experiment.metrics.push(metric);

    if (experiment.metrics.length > 1000) {
      experiment.metrics = experiment.metrics.slice(-1000);
    }
  }
}

/**
 * Load metrics from disk for completed experiments
 */
function loadMetricsFromDisk(resultsPath: string): TrainingMetrics[] {
  try {
    const metricsPath = path.join(resultsPath, 'metrics.json');
    if (fs.existsSync(metricsPath)) {
      const data = fs.readFileSync(metricsPath, 'utf-8');
      return JSON.parse(data);
    }
  } catch (error) {
    console.error('Error loading metrics from disk:', error);
  }
  return [];
}

// Simulated training output for testing (matches Phase C curves)
function generateMockExperimentMetrics(): TrainingMetrics[] {
  const metrics: TrainingMetrics[] = [];
  let episodeReturn = 10;
  let completionRate = 0.2;
  let idleSteps = 500;
  let llmLatency = 50;

  for (let step = 0; step <= 50000; step += 1000) {
    // Realistic-ish training behavior: better returns, fewer wasted steps
    episodeReturn += Math.random() * 5 - 0.5; // gradually improves
    completionRate = Math.min(0.95, completionRate + Math.random() * 0.01); // success rate goes up
    idleSteps = Math.max(50, idleSteps - Math.random() * 20); // more efficient over time
    llmLatency += (Math.random() - 0.5) * 2; // some noise but stable
    metrics.push({
      step,
      episode_return: Math.max(0, episodeReturn),
      completion_rate: Math.min(1, completionRate),
      idle_steps: Math.round(idleSteps),
      llm_latency_ms: Math.max(5, llmLatency),
      timestamp: new Date(Date.now() - (50000 - step) * 3600).toISOString(),
    });
  }

  return metrics;
}
