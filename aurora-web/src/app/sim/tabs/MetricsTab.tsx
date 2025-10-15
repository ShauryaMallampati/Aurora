"use client";

import { useSimulationStore } from "@/shared/store";
import { Flame, Wind, Droplets, Battery, MapPin } from "lucide-react";

export function MetricsTab() {
  const ticks = useSimulationStore((state) => state.ticks);
  const latestTick = ticks[ticks.length - 1];

  if (!latestTick) {
    return (
      <div className="p-6 text-gray-400 text-center">
        No telemetry data available
      </div>
    );
  }

  const metrics = latestTick.metrics;

  return (
    <div className="p-4 space-y-4">
      {/* Fire Metrics */}
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <Flame className="w-5 h-5 text-orange-500" />
          <h3 className="font-semibold text-white">Fire Status</h3>
        </div>
        <div className="space-y-2">
          <MetricRow
            label="Burned Area"
            value={metrics.burnedArea.toFixed(1)}
            unit="acres"
          />
          <MetricRow
            label="Fire Perimeter"
            value={metrics.firePerimeter.toFixed(1)}
            unit="km"
          />
          <MetricRow
            label="Containment"
            value={Math.round(metrics.containment * 100)}
            unit="%"
            highlight={metrics.containment > 0.5}
          />
          <MetricRow
            label="Intensity (avg)"
            value={metrics.avgIntensity.toFixed(2)}
            unit=""
          />
        </div>
      </div>

      {/* Drone Fleet */}
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <MapPin className="w-5 h-5 text-blue-500" />
          <h3 className="font-semibold text-white">Drone Fleet</h3>
        </div>
        <div className="space-y-2">
          <MetricRow
            label="Active Drones"
            value={latestTick.drones.length}
            unit="drones"
          />
          <MetricRow
            label="Avg Battery"
            value={Math.round(
              latestTick.drones.reduce((sum, d) => sum + d.battery, 0) /
                latestTick.drones.length *
                100
            )}
            unit="%"
          />
          <MetricRow
            label="Avg Water"
            value={Math.round(
              latestTick.drones.reduce((sum, d) => sum + d.water, 0) /
                latestTick.drones.length *
                100
            )}
            unit="%"
          />
          <MetricRow
            label="Water Dropped"
            value={metrics.waterDropped.toFixed(1)}
            unit="L"
          />
        </div>
      </div>

      {/* Weather */}
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <Wind className="w-5 h-5 text-cyan-500" />
          <h3 className="font-semibold text-white">Weather Conditions</h3>
        </div>
        <div className="space-y-2">
          <MetricRow
            label="Wind Speed"
            value={latestTick.weather.windSpeed.toFixed(1)}
            unit="m/s"
          />
          <MetricRow
            label="Wind Direction"
            value={latestTick.weather.windDir}
            unit="°"
          />
          <MetricRow
            label="Temperature"
            value={latestTick.weather.temp.toFixed(1)}
            unit="°C"
          />
          <MetricRow
            label="Humidity"
            value={Math.round(latestTick.weather.humidity * 100)}
            unit="%"
          />
        </div>
      </div>

      {/* Simulation Info */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="font-semibold text-white mb-3">Simulation Info</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Timestep</span>
            <span className="text-white font-mono">{latestTick.t}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Time Elapsed</span>
            <span className="text-white font-mono">
              {formatElapsedTime(ticks[0]?.timestamp, latestTick.timestamp)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Total Ticks</span>
            <span className="text-white font-mono">{ticks.length}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricRow({
  label,
  value,
  unit,
  highlight = false,
}: {
  label: string;
  value: string | number;
  unit: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-gray-400">{label}</span>
      <span
        className={`text-sm font-mono ${
          highlight ? "text-green-400 font-semibold" : "text-white"
        }`}
      >
        {value} {unit}
      </span>
    </div>
  );
}

function formatElapsedTime(start: string | undefined, end: string): string {
  if (!start) return "0s";
  const ms = new Date(end).getTime() - new Date(start).getTime();
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}
