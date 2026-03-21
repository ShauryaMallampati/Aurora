import fs from 'fs';
import path from 'path';

import type { SimulationRun } from '../../../shared/runsDataLoader';

export interface RunListItem {
  runId: string;
  modelType: 'ppo' | 'hybrid';
  seed: number;
  timestamp: string;
  totalSteps: number;
  scenarioId?: string;
  totalBurnedArea: number;
  totalWaterUsed: number;
  containmentTime: number;
  successRate: number;
  avgReturnPerStep: number;
}

export interface RunMetricsItem {
  id: string;
  timestamp: string;
  model_type: 'ppo' | 'hybrid';
  model_name: string;
  episode_return: number;
  mean_return: number;
  episodes: number;
  improvement_percent: number;
  llm_model?: string;
  llm_guidance_frequency?: number;
}

export interface TrainingMetricsPayload {
  training: {
    total_timesteps: number;
    episodes_completed: number;
    fire_scenarios_trained: number;
    data_source: string;
    weather_source: string;
  };
  model_performance: {
    ppo: ModelPerformance;
    hybrid: ModelPerformance;
  };
  training_trend: TrainingTrendPoint[];
  experiment_runs: ExperimentRunSummary[];
  last_updated: string;
}

export interface ModelPerformance {
  avg_episode_return: number;
  std_return: number;
  success_rate_percent: number;
  avg_decision_latency_ms: number;
  training_time_hours: number;
  num_episodes: number;
  runs: number;
}

export interface TrainingTrendPoint {
  step: number;
  ppo_return?: number;
  hybrid_return?: number;
  ppo_completion?: number;
  hybrid_completion?: number;
  timestamp: string;
}

export interface ExperimentRunSummary {
  id: string;
  model: 'ppo' | 'hybrid';
  phase: string;
  status: string;
  timestamp: string;
  elapsed_seconds: number;
  final_return: number;
  completion_rate: number;
  avg_latency_ms: number;
  episodes: number;
  scenario: string | null;
}

interface ExperimentRunMetadata {
  id?: string;
  runId?: string;
  mode?: 'ppo' | 'hybrid' | string;
  phase?: string;
  status?: string;
  start_time?: string;
  end_time?: string;
  current_step?: number;
  total_steps?: number;
  seed?: number;
  requested_training_steps?: number;
  episodes_per_iteration?: number;
  episode_horizon?: number;
  summary?: {
    best_return?: number;
    best_completion_rate?: number;
    final_return?: number;
    final_completion_rate?: number;
    final_idle_steps?: number;
    [key: string]: unknown;
  };
  artifacts?: {
    metrics?: string;
    metadata?: string;
  };
  [key: string]: unknown;
}

interface ExperimentMetricRecord {
  step?: number;
  episode_return?: number;
  completion_rate?: number;
  idle_steps?: number;
  llm_latency_ms?: number;
  timestamp?: string;
  [key: string]: unknown;
}

interface LoadedRunArtifacts {
  metadataPath: string;
  metricsPath?: string;
  runMetadata: ExperimentRunMetadata;
  metrics: ExperimentMetricRecord[];
}

type LoadedRun = SimulationRun & {
  artifacts?: LoadedRunArtifacts;
};

const RESULTS_DIR = path.resolve(process.cwd(), '..', 'results');
const CATALOG_FILES = ['aurora_runs.json', 'runs.json', 'run_index.json'];

function readJsonFile<T>(filePath: string): T | null {
  if (!fs.existsSync(filePath)) {
    return null;
  }

  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8')) as T;
  } catch (error) {
    console.warn(`Failed to read run data from ${filePath}:`, error);
    return null;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function asString(value: unknown): string | undefined {
  return typeof value === 'string' && value.length > 0 ? value : undefined;
}

function asNumber(value: unknown): number | undefined {
  return typeof value === 'number' && Number.isFinite(value) ? value : undefined;
}

function isSimulationRun(candidate: unknown): candidate is SimulationRun {
  if (!candidate || typeof candidate !== 'object') {
    return false;
  }

  const value = candidate as Partial<SimulationRun>;
  return Boolean(
    value.runId &&
    value.modelType &&
    value.seed !== undefined &&
    value.timestamp &&
    value.config &&
    Array.isArray(value.ticks) &&
    value.summary
  );
}

function normalizeRunCatalog(candidate: unknown): SimulationRun[] | null {
  if (Array.isArray(candidate)) {
    const runs = candidate.filter(isSimulationRun);
    return runs.length > 0 ? runs : null;
  }

  if (!candidate || typeof candidate !== 'object') {
    return null;
  }

  const value = candidate as Record<string, unknown>;
  if (Array.isArray(value.runs)) {
    return normalizeRunCatalog(value.runs);
  }

  if (isSimulationRun(value.ppo) && isSimulationRun(value.hybrid)) {
    return [value.ppo, value.hybrid];
  }

  if (isSimulationRun(value.run)) {
    return [value.run];
  }

  return null;
}

function normalizeExperimentMetrics(candidate: unknown): ExperimentMetricRecord[] {
  if (Array.isArray(candidate)) {
    return candidate.filter(isRecord) as ExperimentMetricRecord[];
  }

  if (isRecord(candidate) && Array.isArray(candidate.metrics)) {
    return normalizeExperimentMetrics(candidate.metrics);
  }

  return [];
}

function normalizeExperimentMetadata(candidate: unknown): ExperimentRunMetadata | null {
  if (!isRecord(candidate)) {
    return null;
  }

  const mode = asString(candidate.mode) ?? asString(candidate.modelType) ?? asString(candidate.model_type);
  const normalizedMode = mode === 'hybrid_ppo_llm' ? 'hybrid' : mode;
  if (normalizedMode !== 'ppo' && normalizedMode !== 'hybrid') {
    return null;
  }

  return {
    ...candidate,
    mode: normalizedMode,
  } as ExperimentRunMetadata;
}

function buildLoadedExperimentRun(directoryPath: string): LoadedRun | null {
  const metadataPath = path.join(directoryPath, 'run_metadata.json');
  if (!fs.existsSync(metadataPath)) {
    return null;
  }

  const metadata = normalizeExperimentMetadata(readJsonFile(metadataPath));
  if (!metadata) {
    return null;
  }

  const metricsPath = path.join(directoryPath, 'metrics.json');
  const metrics = normalizeExperimentMetrics(readJsonFile(metricsPath));
  const runId = asString(metadata.id) ?? asString(metadata.runId) ?? path.basename(directoryPath);
  const modelType = metadata.mode === 'hybrid' ? 'hybrid' : 'ppo';
  const timestamp = asString(metadata.start_time) ?? asString(metadata.end_time) ?? new Date().toISOString();
  const totalSteps = asNumber(metadata.total_steps) ?? asNumber(metadata.current_step) ?? metrics.length;
  const summary = metadata.summary ?? {};
  const finalReturn = asNumber(summary.final_return) ?? asNumber(summary.best_return) ?? 0;
  const completionRate = asNumber(summary.final_completion_rate) ?? asNumber(summary.best_completion_rate) ?? 0;
  const avgReturnPerStep = totalSteps > 0 ? finalReturn / totalSteps : 0;

  return {
    runId,
    modelType,
    seed: asNumber(metadata.seed) ?? 0,
    timestamp,
    // Preserve the experiment metadata as-is while exposing the run in the existing run APIs.
    config: {
      scenarioId:
        asString(metadata.scenarioId) ??
        asString(metadata.scenario_id) ??
        (isRecord(metadata.config) ? asString(metadata.config.scenarioId) ?? asString(metadata.config.scenario_id) : undefined),
      numDrones:
        asNumber(metadata.numDrones) ??
        asNumber(metadata.num_drones) ??
        (isRecord(metadata.config) ? asNumber(metadata.config.numDrones) ?? asNumber(metadata.config.num_drones) : undefined) ??
        0,
      llmCadence:
        asNumber(metadata.llmCadence) ??
        asNumber(metadata.llm_cadence) ??
        (isRecord(metadata.config) ? asNumber(metadata.config.llmCadence) ?? asNumber(metadata.config.llm_cadence) : undefined),
      maxSteps: asNumber(metadata.total_steps) ?? asNumber(metadata.requested_training_steps),
    },
    ticks: [],
    summary: {
      totalSteps,
      totalBurnedArea: asNumber(summary.totalBurnedArea) ?? asNumber(summary.total_burned_area) ?? 0,
      totalWaterUsed: asNumber(summary.totalWaterUsed) ?? asNumber(summary.total_water_used) ?? 0,
      containmentTime: asNumber(summary.containmentTime) ?? asNumber(summary.containment_time) ?? totalSteps,
      successRate: completionRate,
      avgReturnPerStep,
    },
    artifacts: {
      metadataPath,
      metricsPath: fs.existsSync(metricsPath) ? metricsPath : undefined,
      runMetadata: metadata,
      metrics,
    },
  };
}

function loadExperimentRunsFromDisk(): LoadedRun[] {
  if (!fs.existsSync(RESULTS_DIR)) {
    return [];
  }

  const runs: LoadedRun[] = [];
  for (const entry of fs.readdirSync(RESULTS_DIR, { withFileTypes: true })) {
    if (!entry.isDirectory()) {
      continue;
    }

    const loaded = buildLoadedExperimentRun(path.join(RESULTS_DIR, entry.name));
    if (loaded) {
      runs.push(loaded);
    }
  }

  return runs;
}

function loadRunCatalogFromDisk(): LoadedRun[] {
  const runs: LoadedRun[] = [];

  for (const fileName of CATALOG_FILES) {
    const catalog = normalizeRunCatalog(readJsonFile(path.join(RESULTS_DIR, fileName)));
    if (catalog) {
      runs.push(...catalog);
    }
  }

  return runs;
}

function dedupeRuns(runs: LoadedRun[]): LoadedRun[] {
  const byRunId = new Map<string, LoadedRun>();

  for (const run of runs) {
    byRunId.set(run.runId, run);
  }

  return Array.from(byRunId.values());
}

function loadPersistedRuns(): LoadedRun[] {
  return dedupeRuns([
    ...loadRunCatalogFromDisk(),
    ...loadExperimentRunsFromDisk(),
  ]);
}

function getPersistedComparableRuns(): LoadedRun[] {
  return loadPersistedRuns().filter((run) => run.ticks.length > 0);
}

export function getAvailableRuns(): LoadedRun[] {
  return loadPersistedRuns();
}

export function getRunById(runId: string): LoadedRun | null {
  return getAvailableRuns().find((run) => run.runId === runId) ?? null;
}

export function listRunMetadata(filters?: {
  modelType?: 'ppo' | 'hybrid';
  scenario?: string;
}): RunListItem[] {
  return getAvailableRuns()
    .filter((run) => !filters?.modelType || run.modelType === filters.modelType)
    .filter((run) => !filters?.scenario || run.config.scenarioId === filters.scenario)
    .map((run) => ({
      runId: run.runId,
      modelType: run.modelType,
      seed: run.seed,
      timestamp: run.timestamp,
      totalSteps: run.summary.totalSteps,
      scenarioId: run.config.scenarioId,
      totalBurnedArea: run.summary.totalBurnedArea,
      totalWaterUsed: run.summary.totalWaterUsed,
      containmentTime: run.summary.containmentTime,
      successRate: run.summary.successRate,
      avgReturnPerStep: run.summary.avgReturnPerStep,
    }));
}

export function getComparisonRuns(filters?: {
  scenario?: string;
  seed?: number;
}): { ppo: SimulationRun; hybrid: SimulationRun } | null {
  const runs = loadPersistedRuns();
  const ppoRuns = runs.filter((run) => run.modelType === 'ppo');
  const hybridRuns = runs.filter((run) => run.modelType === 'hybrid');

  if (ppoRuns.length === 0 || hybridRuns.length === 0) {
    return null;
  }

  const hasFilters = Boolean(filters?.scenario || filters?.seed !== undefined);

  if (hasFilters) {
    const matchingPpoRuns = ppoRuns.filter((run) => {
      if (filters?.scenario && run.config.scenarioId !== filters.scenario) {
        return false;
      }
      if (filters?.seed !== undefined && run.seed !== filters.seed) {
        return false;
      }
      return true;
    });

    const matchingHybridRuns = hybridRuns.filter((run) => {
      if (filters?.scenario && run.config.scenarioId !== filters.scenario) {
        return false;
      }
      if (filters?.seed !== undefined && run.seed !== filters.seed) {
        return false;
      }
      return true;
    });

    for (const ppo of matchingPpoRuns) {
      const hybrid = matchingHybridRuns.find((run) => {
        if (filters?.scenario && run.config.scenarioId !== ppo.config.scenarioId) {
          return false;
        }
        if (filters?.seed !== undefined) {
          return run.seed === filters.seed && ppo.seed === filters.seed;
        }
        return run.seed === ppo.seed || run.config.scenarioId === ppo.config.scenarioId;
      });

      if (hybrid) {
        return { ppo, hybrid };
      }
    }

    return null;
  }

  for (const ppo of ppoRuns) {
    const hybrid = hybridRuns.find((run) => {
      if (run.seed === ppo.seed && run.config.scenarioId === ppo.config.scenarioId) {
        return true;
      }

      if (run.seed === ppo.seed) {
        return true;
      }

      return run.config.scenarioId === ppo.config.scenarioId;
    });

    if (hybrid) {
      return { ppo, hybrid };
    }
  }

  return null;
}

export function buildRunMetricsPayload(runId?: string): RunMetricsItem | RunMetricsItem[] {
  if (runId) {
    const run = getRunById(runId);
    if (!run) {
      throw new Error(`Run not found: ${runId}`);
    }

    return toRunMetricsItem(run);
  }

  return getAvailableRuns().map((run) => toRunMetricsItem(run));
}

export function buildTrainingMetricsPayload(): TrainingMetricsPayload {
  const runs = getAvailableRuns();
  const ppoRuns = runs.filter((run) => run.modelType === 'ppo');
  const hybridRuns = runs.filter((run) => run.modelType === 'hybrid');

  const latestPpoRun = [...ppoRuns].sort(sortRunsByTimestampDesc)[0];
  const latestHybridRun = [...hybridRuns].sort(sortRunsByTimestampDesc)[0];

  const episodeCounts = runs.map((run) => getRunEpisodeCount(run));
  const uniqueScenarios = new Set(
    runs.map((run) => run.config.scenarioId).filter((value): value is string => Boolean(value)),
  );

  return {
    training: {
      total_timesteps: runs.reduce((sum, run) => sum + run.summary.totalSteps, 0),
      episodes_completed: episodeCounts.reduce((sum, count) => sum + count, 0),
      fire_scenarios_trained: uniqueScenarios.size,
      data_source: 'InterAgency Fire Perimeter History (1308-2024)',
      weather_source: 'NOAA National Weather Service API',
    },
    model_performance: {
      ppo: buildModelPerformance(ppoRuns),
      hybrid: buildModelPerformance(hybridRuns),
    },
    training_trend: buildTrainingTrendFromRuns(latestPpoRun, latestHybridRun),
    experiment_runs: [...runs]
      .sort(sortRunsByTimestampDesc)
      .map((run) => toExperimentRunSummary(run))
      .slice(0, 12),
    last_updated: new Date().toISOString(),
  };
}

function toRunMetricsItem(run: SimulationRun): RunMetricsItem {
  const artifactMetrics = (run as LoadedRun).artifacts?.metrics ?? [];
  const runMetadata = (run as LoadedRun).artifacts?.runMetadata;
  const experimentEpisodeReturns = artifactMetrics
    .map((metric) => metric.episode_return)
    .filter((value): value is number => typeof value === 'number' && Number.isFinite(value));
  const experimentAverageReturn = experimentEpisodeReturns.length > 0
    ? experimentEpisodeReturns.reduce((sum, value) => sum + value, 0) / experimentEpisodeReturns.length
    : undefined;
  const experimentFinalReturn = runMetadata?.summary?.final_return ?? runMetadata?.summary?.best_return;

  if (runMetadata) {
    const modelName =
      run.modelType === 'hybrid'
        ? 'Hybrid Experiment'
        : 'PPO Experiment';

    return {
      id: run.runId,
      timestamp: run.timestamp,
      model_type: run.modelType,
      model_name: modelName,
      episode_return: experimentFinalReturn ?? experimentAverageReturn ?? 0,
      mean_return: experimentAverageReturn ?? experimentFinalReturn ?? 0,
      episodes: runMetadata.total_steps ?? artifactMetrics.length,
      improvement_percent: 0,
      ...(run.modelType === 'hybrid' && {
        llm_model: 'Experiment artifact',
        llm_guidance_frequency: runMetadata.episodes_per_iteration,
      }),
    };
  }

  const finalReturn = run.summary.avgReturnPerStep * run.summary.totalSteps;
  const meanReturn = run.summary.avgReturnPerStep;
  const isHybrid = run.modelType === 'hybrid';

  return {
    id: run.runId,
    timestamp: run.timestamp,
    model_type: run.modelType,
    model_name: isHybrid ? 'Hybrid Simulation Run' : 'PPO Simulation Run',
    episode_return: finalReturn,
    mean_return: meanReturn,
    episodes: run.summary.totalSteps,
    improvement_percent: 0,
    ...(isHybrid && {
      llm_model: 'Hybrid controller',
      llm_guidance_frequency: run.config.llmCadence ?? 0,
    }),
  };
}

function sortRunsByTimestampDesc(a: SimulationRun, b: SimulationRun): number {
  return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
}

function getArtifactMetrics(run: SimulationRun): ExperimentMetricRecord[] {
  return (run as LoadedRun).artifacts?.metrics ?? [];
}

function getRunMetadata(run: SimulationRun): ExperimentRunMetadata | undefined {
  return (run as LoadedRun).artifacts?.runMetadata;
}

function getRunEpisodeCount(run: SimulationRun): number {
  const metadata = getRunMetadata(run);
  const metrics = getArtifactMetrics(run);
  return asNumber(metadata?.total_steps) ?? metrics.length ?? run.summary.totalSteps;
}

function getRunFinalReturn(run: SimulationRun): number {
  const metadata = getRunMetadata(run);
  const summary = metadata?.summary;
  const fromMetadata =
    asNumber(summary?.final_return) ??
    asNumber(summary?.best_return);

  if (fromMetadata !== undefined) {
    return fromMetadata;
  }

  const metrics = getArtifactMetrics(run);
  const lastMetric = [...metrics]
    .reverse()
    .find((metric) => asNumber(metric.episode_return) !== undefined);

  if (lastMetric?.episode_return !== undefined) {
    return lastMetric.episode_return;
  }

  return run.summary.avgReturnPerStep * run.summary.totalSteps;
}

function getRunCompletionRate(run: SimulationRun): number {
  const metadata = getRunMetadata(run);
  const summary = metadata?.summary;
  const fromMetadata =
    asNumber(summary?.final_completion_rate) ??
    asNumber(summary?.best_completion_rate);

  if (fromMetadata !== undefined) {
    return fromMetadata;
  }

  const metrics = getArtifactMetrics(run);
  const lastMetric = [...metrics]
    .reverse()
    .find((metric) => asNumber(metric.completion_rate) !== undefined);

  if (lastMetric?.completion_rate !== undefined) {
    return lastMetric.completion_rate;
  }

  return run.summary.successRate;
}

function getRunAverageLatency(run: SimulationRun): number {
  const values = getArtifactMetrics(run)
    .map((metric) => metric.llm_latency_ms)
    .filter((value): value is number => typeof value === 'number' && Number.isFinite(value));

  return mean(values);
}

function getRunElapsedSeconds(run: SimulationRun): number {
  const metadata = getRunMetadata(run);
  if (asNumber(metadata?.elapsed_seconds) !== undefined) {
    return metadata!.elapsed_seconds as number;
  }

  if (metadata?.start_time && metadata?.end_time) {
    return (
      new Date(metadata.end_time).getTime() - new Date(metadata.start_time).getTime()
    ) / 1000;
  }

  return 0;
}

function mean(values: number[]): number {
  if (values.length === 0) {
    return 0;
  }

  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function stddev(values: number[]): number {
  if (values.length <= 1) {
    return 0;
  }

  const average = mean(values);
  const variance = mean(values.map((value) => (value - average) ** 2));
  return Math.sqrt(variance);
}

function buildModelPerformance(runs: SimulationRun[]): ModelPerformance {
  const finalReturns = runs.map((run) => getRunFinalReturn(run));
  const completionRates = runs.map((run) => getRunCompletionRate(run) * 100);
  const latencies = runs.map((run) => getRunAverageLatency(run)).filter((value) => value > 0);
  const durations = runs.map((run) => getRunElapsedSeconds(run) / 3600).filter((value) => value > 0);
  const episodes = runs.map((run) => getRunEpisodeCount(run));

  return {
    avg_episode_return: mean(finalReturns),
    std_return: stddev(finalReturns),
    success_rate_percent: mean(completionRates),
    avg_decision_latency_ms: mean(latencies),
    training_time_hours: mean(durations),
    num_episodes: episodes.reduce((sum, count) => sum + count, 0),
    runs: runs.length,
  };
}

function buildTrainingTrendFromRuns(
  ppo?: SimulationRun,
  hybrid?: SimulationRun,
): TrainingTrendPoint[] {
  const ppoMetrics = getArtifactMetrics(ppo ?? ({} as SimulationRun));
  const hybridMetrics = getArtifactMetrics(hybrid ?? ({} as SimulationRun));
  const maxLength = Math.max(ppoMetrics.length, hybridMetrics.length);

  const trend: TrainingTrendPoint[] = [];
  for (let index = 0; index < maxLength; index += 1) {
    const ppoMetric = ppoMetrics[index];
    const hybridMetric = hybridMetrics[index];

    trend.push({
      step:
        asNumber(hybridMetric?.step) ??
        asNumber(ppoMetric?.step) ??
        index + 1,
      ...(asNumber(ppoMetric?.episode_return) !== undefined && {
        ppo_return: ppoMetric!.episode_return,
      }),
      ...(asNumber(hybridMetric?.episode_return) !== undefined && {
        hybrid_return: hybridMetric!.episode_return,
      }),
      ...(asNumber(ppoMetric?.completion_rate) !== undefined && {
        ppo_completion: (ppoMetric!.completion_rate ?? 0) * 100,
      }),
      ...(asNumber(hybridMetric?.completion_rate) !== undefined && {
        hybrid_completion: (hybridMetric!.completion_rate ?? 0) * 100,
      }),
      timestamp:
        asString(hybridMetric?.timestamp) ??
        asString(ppoMetric?.timestamp) ??
        new Date().toISOString(),
    });
  }

  return trend;
}

function toExperimentRunSummary(run: SimulationRun): ExperimentRunSummary {
  const metadata = getRunMetadata(run);

  return {
    id: run.runId,
    model: run.modelType,
    phase: asString(metadata?.phase) ?? 'recorded',
    status: asString(metadata?.status) ?? 'recorded',
    timestamp: run.timestamp,
    elapsed_seconds: getRunElapsedSeconds(run),
    final_return: getRunFinalReturn(run),
    completion_rate: getRunCompletionRate(run),
    avg_latency_ms: getRunAverageLatency(run),
    episodes: getRunEpisodeCount(run),
    scenario: run.config.scenarioId ?? null,
  };
}
