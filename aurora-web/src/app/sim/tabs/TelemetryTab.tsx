"use client";

import { useSimulationStore } from "@/shared/store";

export function TelemetryTab() {
  const ticks = useSimulationStore((state) => state.ticks);
  const latestTick = ticks[ticks.length - 1];

  if (!latestTick) {
    return (
      <div className="p-6 text-gray-400 text-center">
        No telemetry data available
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Drones */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="font-semibold text-white mb-3">Drones</h3>
        <div className="space-y-3">
          {latestTick.drones.map((drone) => (
            <div key={drone.id} className="bg-gray-900 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-white">
                  Drone {drone.id}
                </span>
                <span
                  className="text-xs px-2 py-1 rounded"
                  style={{ backgroundColor: getDroneColor(drone.action) }}
                >
                  {drone.action}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-400">Battery:</span>
                  <span className="text-white ml-1">
                    {Math.round(drone.battery * 100)}%
                  </span>
                </div>
                <div>
                  <span className="text-gray-400">Water:</span>
                  <span className="text-white ml-1">
                    {Math.round(drone.water * 100)}%
                  </span>
                </div>
                <div className="col-span-2">
                  <span className="text-gray-400">Position:</span>
                  <span className="text-white ml-1 font-mono">
                    ({drone.lat.toFixed(4)}, {drone.lng.toFixed(4)})
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Events */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="font-semibold text-white mb-3">Recent Events</h3>
        <div className="space-y-2">
          {latestTick.events.length === 0 ? (
            <div className="text-sm text-gray-400">No events</div>
          ) : (
            latestTick.events.slice(-10).map((event, i) => (
              <div key={i} className="text-sm">
                <span className="text-gray-400">[{event.type}]</span>
                <span className="text-white ml-2">
                  {event.message || `${event.agent} at (${event.x}, ${event.y})`}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Weather */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="font-semibold text-white mb-3">Current Weather</h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">Temperature</span>
            <span className="text-white">
              {latestTick.weather.temp.toFixed(1)}°C
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Wind Speed</span>
            <span className="text-white">
              {latestTick.weather.windSpeed.toFixed(1)} m/s
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Wind Direction</span>
            <span className="text-white">{latestTick.weather.windDir}°</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Humidity</span>
            <span className="text-white">
              {Math.round(latestTick.weather.humidity * 100)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function getDroneColor(action: string): string {
  switch (action) {
    case "drop":
      return "#06b6d4";
    case "scout":
      return "#a855f7";
    case "recharge":
      return "#eab308";
    case "refill":
      return "#3b82f6";
    default:
      return "#60a5fa";
  }
}
