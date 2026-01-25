'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

interface DroneAction {
  step: number;
  action: 'suppress' | 'scout' | 'move' | 'idle';
  reason: string;
  confidence: number; // 0-1
  location: { x: number; y: number };
}

interface DroneActionPopoverProps {
  droneId: string;
  lat: number;
  lng: number;
  actions: DroneAction[];
  isOpen: boolean;
  onHover: (isOpen: boolean) => void;
}

/**
 * DroneActionPopover Component
 * 
 * Displays last 3 drone actions with LLM rationales when drone is hovered.
 * Color-coded by action type:
 * - 🔴 Red: suppress (high fire intensity)
 * - 🟡 Yellow: scout (exploring, gathering info)
 * - 🟢 Green: move (repositioning)
 * - 🔵 Blue: idle (waiting)
 */
export function DroneActionPopover({
  droneId,
  lat,
  lng,
  actions,
  isOpen,
  onHover,
}: DroneActionPopoverProps) {
  const recentActions = actions.slice(-3).reverse();

  const getActionColor = (action: string) => {
    switch (action) {
      case 'suppress':
        return { bg: 'bg-red-500/20', border: 'border-red-500', text: 'text-red-400', icon: '🔴' };
      case 'scout':
        return { bg: 'bg-yellow-500/20', border: 'border-yellow-500', text: 'text-yellow-400', icon: '🟡' };
      case 'move':
        return { bg: 'bg-green-500/20', border: 'border-green-500', text: 'text-green-400', icon: '🟢' };
      case 'idle':
        return { bg: 'bg-blue-500/20', border: 'border-blue-500', text: 'text-blue-400', icon: '🔵' };
      default:
        return { bg: 'bg-gray-500/20', border: 'border-gray-500', text: 'text-gray-400', icon: '⚪' };
    }
  };

  const getActionLabel = (action: string) => {
    return action.charAt(0).toUpperCase() + action.slice(1);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-emerald-400';
    if (confidence >= 0.6) return 'text-yellow-400';
    return 'text-orange-400';
  };

  return (
    <div
      className="relative"
      onMouseEnter={() => onHover(true)}
      onMouseLeave={() => onHover(false)}
    >
      {/* Popover Content */}
      <div
        className={`absolute -top-2 -left-32 w-64 bg-slate-900 border-2 border-slate-700 rounded-lg shadow-2xl p-3 z-50 transition-all duration-200 pointer-events-auto ${
          isOpen
            ? 'opacity-100 visible translate-y-0'
            : 'opacity-0 invisible translate-y-2'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-700">
          <h4 className="font-bold text-sm text-white flex items-center gap-2">
            <span className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></span>
            Drone {droneId}
          </h4>
          <span className="text-xs text-gray-400">
            {lat.toFixed(2)}°, {lng.toFixed(2)}°
          </span>
        </div>

        {/* Recent Actions */}
        <div className="space-y-2">
          {recentActions.length === 0 ? (
            <div className="text-xs text-gray-500 text-center py-2">No actions recorded</div>
          ) : (
            recentActions.map((action, index) => {
              const colors = getActionColor(action.action);
              return (
                <div
                  key={`${action.step}_${index}`}
                  className={`${colors.bg} border ${colors.border} rounded p-2 text-xs transition-colors hover:bg-opacity-30`}
                >
                  {/* Action type and confidence */}
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold flex items-center gap-1.5">
                      <span>{colors.icon}</span>
                      <span className={colors.text}>{getActionLabel(action.action)}</span>
                    </span>
                    <span className={`${getConfidenceColor(action.confidence)} font-bold`}>
                      {Math.round(action.confidence * 100)}%
                    </span>
                  </div>

                  {/* Reason / Rationale */}
                  <p className="text-gray-300 leading-tight mb-1">{action.reason}</p>

                  {/* Metadata */}
                  <div className="flex justify-between text-gray-500 text-xs">
                    <span>Step {action.step}</span>
                    <span>
                      ({action.location.x}, {action.location.y})
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer - Confidence Indicator */}
        <div className="mt-2 pt-2 border-t border-slate-700 text-xs text-gray-400 flex items-center gap-1">
          <ChevronDown className="w-3 h-3" />
          Last {recentActions.length} action(s) shown
        </div>

        {/* Pointer Arrow */}
        <div className="absolute right-4 top-full w-0 h-0 border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-slate-900"></div>
      </div>

      {/* Hover Target (invisible, positioned on drone) */}
      <div className="w-full h-full" />
    </div>
  );
}

/**
 * Generate sample drone actions for display (when there's no real data)
 */
export function generateMockDroneActions(droneId: string): DroneAction[] {
  const actions: DroneAction[] = [
    {
      step: 145,
      action: 'suppress',
      reason: 'Fire intensity 0.85 at bearing 45°. Wind shift predicted NE in 3 steps.',
      confidence: 0.92,
      location: { x: 128, y: 95 },
    },
    {
      step: 140,
      action: 'move',
      reason: 'Repositioning to flank approaching fire. Battery at 42%.',
      confidence: 0.78,
      location: { x: 110, y: 88 },
    },
    {
      step: 135,
      action: 'scout',
      reason: 'Gathering weather data and fire perimeter info for LLM strategy update.',
      confidence: 0.65,
      location: { x: 95, y: 82 },
    },
    {
      step: 130,
      action: 'suppress',
      reason: 'Critical fire growth detected. 15 hectares burned in last 2 steps.',
      confidence: 0.88,
      location: { x: 120, y: 100 },
    },
    {
      step: 125,
      action: 'idle',
      reason: 'Waiting for LLM strategic guidance. No critical threats in vicinity.',
      confidence: 0.71,
      location: { x: 115, y: 98 },
    },
  ];

  return actions;
}
