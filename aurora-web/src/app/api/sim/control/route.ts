import { NextRequest, NextResponse } from 'next/server';

import { deleteSession, getSession, updateSession } from '../session-store';
import type { ControlCommand } from '../../../../shared/types';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  try {
    const command: ControlCommand = await request.json();
    if (!command?.runId || !command?.action) {
      return NextResponse.json({ error: 'Invalid control command' }, { status: 400 });
    }

    const session = getSession(command.runId);

    if (!session) {
      return NextResponse.json({ error: 'Simulation session not found' }, { status: 404 });
    }

    switch (command.action) {
      case 'pause':
        updateSession(command.runId, { paused: true, status: 'paused' });
        break;
      case 'resume':
        updateSession(command.runId, { paused: false, status: 'running' });
        break;
      case 'step':
        updateSession(command.runId, {
          paused: true,
          status: 'paused',
          stepBudget: Math.max(0, session.stepBudget + Math.max(1, command.steps ?? 1)),
        });
        break;
      case 'speed':
        if (!Number.isFinite(command.speed)) {
          return NextResponse.json({ error: 'Missing speed value' }, { status: 400 });
        }
        updateSession(command.runId, {
          speed: Math.max(0.25, Math.min(8, command.speed ?? 1)),
        });
        break;
      case 'reset':
        deleteSession(command.runId);
        break;
      default:
        return NextResponse.json({ error: 'Unsupported control action' }, { status: 400 });
    }

    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error('Failed to control simulation session:', error);
    return NextResponse.json(
      { error: 'Failed to control simulation session' },
      { status: 500 },
    );
  }
}
