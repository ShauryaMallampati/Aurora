import { NextRequest } from 'next/server';

import { buildGuidance, buildTick, deleteSession, getSession, updateSession } from '../../session-store';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

function formatEvent(event: string, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ runId: string }> },
) {
  const { runId } = await params;
  const session = getSession(runId);
  if (!session) {
    return new Response('Simulation session not found', { status: 404 });
  }

  const encoder = new TextEncoder();
  const maxSteps = session.config.maxSteps ?? 150;
  const guidanceCadence = Math.max(1, session.config.llmCadence ?? 50);

  let cleanupStream: (() => void) | null = null;
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      let intervalHandle: ReturnType<typeof setTimeout> | null = null;
      let heartbeatHandle: ReturnType<typeof setInterval> | null = null;
      let closed = false;

      const cleanup = () => {
        closed = true;
        if (intervalHandle) {
          clearTimeout(intervalHandle);
          intervalHandle = null;
        }
        if (heartbeatHandle) {
          clearInterval(heartbeatHandle);
          heartbeatHandle = null;
        }
      };
      cleanupStream = cleanup;

      const closeStream = () => {
        cleanup();
        try {
          controller.close();
        } catch {
          // Ignore close-after-close errors when the client disconnects first.
        }
      };

      const scheduleNextTick = (delayMs: number) => {
        intervalHandle = setTimeout(pump, delayMs);
      };

      const pump = () => {
        if (closed) {
          return;
        }

        const current = getSession(runId);
        if (!current) {
          closeStream();
          return;
        }

        if (current.currentStep >= maxSteps) {
          updateSession(runId, { status: 'completed', paused: true, stepBudget: 0 });
          controller.enqueue(encoder.encode(formatEvent('complete', { runId })));
          deleteSession(runId);
          closeStream();
          return;
        }

        const shouldEmitManualStep = current.paused && current.stepBudget > 0;
        if (!current.paused || shouldEmitManualStep) {
          const tick = buildTick(current, current.currentStep);
          controller.enqueue(encoder.encode(formatEvent('tick', tick)));

          if (
            current.config.model === 'hybrid' &&
            current.currentStep > 0 &&
            current.currentStep % guidanceCadence === 0
          ) {
            controller.enqueue(encoder.encode(formatEvent('guidance', buildGuidance(current, current.currentStep))));
          }

          updateSession(runId, {
            currentStep: current.currentStep + 1,
            status: current.paused ? 'paused' : 'running',
            stepBudget: shouldEmitManualStep ? Math.max(0, current.stepBudget - 1) : current.stepBudget,
          });
        }

        const latest = getSession(runId);
        if (!latest) {
          closeStream();
          return;
        }

        scheduleNextTick(Math.max(120, 600 / Math.max(0.25, latest.speed)));
      };

      updateSession(runId, { status: 'running', paused: false });
      controller.enqueue(encoder.encode(': connected\n\n'));
      scheduleNextTick(Math.max(120, 600 / Math.max(0.25, session.speed)));

      heartbeatHandle = setInterval(() => {
        if (!closed) {
          controller.enqueue(encoder.encode(': keep-alive\n\n'));
        }
      }, 15000);
    },
    cancel() {
      cleanupStream?.();
      const current = getSession(runId);
      if (current) {
        updateSession(runId, { paused: true, status: 'paused' });
      }
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
    },
  });
}
