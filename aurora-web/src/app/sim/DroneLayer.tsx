"use client";

import { Circle, InfoWindow, Marker } from "@react-google-maps/api";
import { Fragment, useState } from "react";
import type { TelemetryTick, Drone } from "@/shared/types";
import { Wind, Mountain, Droplets, Flame, TrendingUp, Brain } from "lucide-react";
import type { DroneAction } from "@/components/ui/drone-action-popover";

interface DroneLayerProps {
  tick: TelemetryTick;
}

export function DroneLayer({ tick }: DroneLayerProps) {
  const [selectedDrone, setSelectedDrone] = useState<number | null>(null);
  const [hoveredDrone, setHoveredDrone] = useState<number | null>(null);

  // Group drones by proximity for big swarms (avoid overlap)
  const droneGroups = tick.drones.length > 20 ? groupDronesByProximity(tick.drones) : null;
  
  const dronesToRender = droneGroups ? Object.values(droneGroups).map(group => group[0]) : tick.drones;

  return (
    <>
      {dronesToRender.map((drone) => {
        const conditions = getDerivedConditions(drone, tick);
        const reasoning = getActionReasoning(drone, tick);
        const features = getFeatureSignals(drone, tick);

        // Find nearby drones if grouped
        const nearbyDrones = droneGroups ? droneGroups[`${drone.lat.toFixed(4)}_${drone.lng.toFixed(4)}`] : [drone];
        const count = nearbyDrones?.length || 1;

        return (
          <Fragment key={drone.id}>
            {drone.action === "drop" ? (
              <Circle
                center={{ lat: drone.lat, lng: drone.lng }}
                radius={190 + (count - 1) * 45}
                options={{
                  fillColor: "#22d3ee",
                  fillOpacity: hoveredDrone === drone.id ? 0.28 : 0.18,
                  strokeColor: "#0891b2",
                  strokeOpacity: 0.85,
                  strokeWeight: 1.5,
                  clickable: false,
                }}
              />
            ) : null}

            {drone.action === "scout" ? (
              <Circle
                center={{ lat: drone.lat, lng: drone.lng }}
                radius={125 + (count - 1) * 35}
                options={{
                  fillColor: "#c084fc",
                  fillOpacity: hoveredDrone === drone.id ? 0.18 : 0.1,
                  strokeColor: "#9333ea",
                  strokeOpacity: 0.72,
                  strokeWeight: 1.2,
                  clickable: false,
                }}
              />
            ) : null}

            <Marker
              key={`marker_${drone.id}`}
              position={{ lat: drone.lat, lng: drone.lng }}
              icon={{
                path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
                fillColor: getDroneColor(drone.action),
                fillOpacity: 1,
                strokeColor: hoveredDrone === drone.id ? "#f8fafc" : "#0f172a",
                strokeWeight: hoveredDrone === drone.id ? 3 : count > 1 ? 2.5 : 2,
                scale: hoveredDrone === drone.id ? 9 : count > 1 ? 8 : 7,
                rotation: drone.heading,
              }}
              label={count > 1 ? {
                text: `${count}`,
                color: '#fff',
                fontSize: '12px',
                fontWeight: 'bold'
              } : undefined}
              onMouseOver={() => setHoveredDrone(drone.id)}
              onMouseOut={() => setHoveredDrone(null)}
              onClick={() => setSelectedDrone(drone.id)}
            >
            {selectedDrone === drone.id && (
              <InfoWindow onCloseClick={() => setSelectedDrone(null)}>
                <div className="text-gray-900 p-3 min-w-[280px]">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-300">
                    <div className="font-bold text-lg">Drone {drone.id}</div>
                    <div className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded font-semibold">
                      {drone.action.toUpperCase()}
                    </div>
                  </div>

                  {/* Status */}
                  <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
                    <div>
                      <span className="text-gray-600">Battery:</span>{" "}
                      <span className="font-semibold">{Math.round(drone.battery * 100)}%</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Water:</span>{" "}
                      <span className="font-semibold">{Math.round(drone.water * 100)}%</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Heading:</span>{" "}
                      <span className="font-semibold">{Math.round(drone.heading)}°</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Position:</span>{" "}
                      <span className="font-mono text-[10px]">
                        {drone.lat.toFixed(2)}, {drone.lng.toFixed(2)}
                      </span>
                    </div>
                  </div>

                  {/* Local Conditions */}
                  <div className="mb-3 pb-3 border-b border-gray-200">
                    <div className="font-semibold text-xs text-gray-700 mb-2 flex items-center gap-1">
                      <Mountain className="w-3 h-3" />
                      Local Conditions
                    </div>
                    <div className="space-y-1 text-xs">
                      <div className="flex items-center gap-2">
                        <Wind className="w-3 h-3 text-blue-600" />
                        <span className="text-gray-600">Wind:</span>
                        <span className="font-semibold">
                          {conditions.windSpeed.toFixed(1)} mph {conditions.windDirection}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Mountain className="w-3 h-3 text-green-600" />
                        <span className="text-gray-600">Slope:</span>
                        <span className="font-semibold">{conditions.slope.toFixed(1)}°</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Droplets className="w-3 h-3 text-cyan-600" />
                        <span className="text-gray-600">Humidity:</span>
                        <span className="font-semibold">{(conditions.humidity * 100).toFixed(0)}%</span>
                      </div>
                      {conditions.fireIntensity > 0 && (
                        <div className="flex items-center gap-2">
                          <Flame className="w-3 h-3 text-red-600" />
                          <span className="text-gray-600">Fire Intensity:</span>
                          <span className="font-semibold text-red-600">
                            {conditions.fireIntensity.toFixed(0)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Action Reasoning */}
                  <div className="mb-3 pb-3 border-b border-gray-200">
                    <div className="font-semibold text-xs text-gray-700 mb-1 flex items-center gap-1">
                      <Brain className="w-3 h-3" />
                      Why This Action?
                    </div>
                    <p className="text-xs text-gray-700 leading-relaxed">{reasoning}</p>
                    <p className="mt-2 text-[11px] text-gray-500">
                      Derived from the current live tick. The stream does not emit per-feature model attribution yet.
                    </p>
                  </div>

                  {/* Feature Attributions */}
                  <div>
                    <div className="font-semibold text-xs text-gray-700 mb-2 flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" />
                      Top Decision Factors
                    </div>
                    <div className="space-y-1.5">
                      {features.map((feature, idx) => (
                        <div key={idx} className="text-xs">
                          <div className="flex items-center justify-between mb-0.5">
                            <span className="text-gray-600">{feature.name}</span>
                            <span
                              className={`font-semibold ${
                                feature.positive ? "text-green-600" : "text-red-600"
                              }`}
                            >
                              {feature.positive ? "+" : ""}
                              {feature.value.toFixed(2)}
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-1.5">
                            <div
                              className={`h-1.5 rounded-full ${
                                feature.positive ? "bg-green-500" : "bg-red-500"
                              }`}
                              style={{ width: `${Math.abs(feature.value) * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </InfoWindow>
            )}
            </Marker>
          </Fragment>
        );
      })}
    </>
  );
}

function getDroneColor(action: string): string {
  switch (action) {
    case "drop":
      return "#0ea5e9"; // bright blue
    case "scout":
      return "#a855f7"; // purple
    case "recharge":
      return "#eab308"; // yellow
    case "refill":
      return "#3b82f6"; // blue
    default:
      return "#60a5fa"; // light blue
  }
}

function getDerivedConditions(drone: Drone, tick: TelemetryTick) {
  return {
    windSpeed: tick.weather.windSpeed,
    windDirection: formatWindDirection(tick.weather.windDir),
    slope: Math.abs(Math.sin((drone.lat + drone.lng) * 12)) * 24,
    humidity: tick.weather.humidity,
    fireIntensity: tick.metrics.avgIntensity * 100,
  };
}

function getActionReasoning(drone: Drone, tick: TelemetryTick): string {
  switch (drone.action) {
    case "drop":
      return `Suppression is active because containment is ${(tick.metrics.containment * 100).toFixed(0)}% and the live feed still reports ${tick.metrics.burnedArea.toFixed(1)} acres burning.`;
    case "scout":
      return `The drone is scouting while wind is ${tick.weather.windSpeed.toFixed(1)} m/s from ${formatWindDirection(tick.weather.windDir)}, improving perimeter awareness before the next suppression pass.`;
    case "recharge":
      return `Battery reserves are low, so the drone is returning to recover before another assignment.`;
    case "refill":
      return `Water reserves are low, so the drone is refilling before resuming suppression.`;
    case "move":
      return `The controller is repositioning this drone toward the active perimeter as containment advances.`;
    default:
      return "The controller is holding position while the next live telemetry update arrives.";
  }
}

function getFeatureSignals(drone: Drone, tick: TelemetryTick) {
  return [
    {
      name: "Containment progress",
      value: tick.metrics.containment,
      positive: true,
    },
    {
      name: "Battery reserve",
      value: drone.battery - 0.5,
      positive: drone.battery >= 0.5,
    },
    {
      name: "Water reserve",
      value: drone.water - 0.5,
      positive: drone.water >= 0.5,
    },
  ];
}

function buildDerivedActions(drone: Drone, tick: TelemetryTick): DroneAction[] {
  const primaryAction = mapDroneAction(drone.action);
  const location = {
    x: Math.round(((drone.lng + 180) / 360) * 256),
    y: Math.round(((90 - drone.lat) / 180) * 256),
  };

  return [
    {
      step: tick.t,
      action: primaryAction,
      reason: getActionReasoning(drone, tick),
      confidence: Math.max(0.55, Math.min(0.98, 0.45 + drone.battery * 0.25 + drone.water * 0.2)),
      location,
    },
  ];
}

function mapDroneAction(action: string): DroneAction["action"] {
  switch (action) {
    case "drop":
      return "suppress";
    case "scout":
      return "scout";
    case "move":
    case "recharge":
    case "refill":
      return "move";
    default:
      return "idle";
  }
}

function formatWindDirection(degrees: number): string {
  const directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  return directions[Math.round((((degrees % 360) + 360) % 360) / 45) % directions.length];
}

function groupDronesByProximity(drones: Drone[]): Record<string, Drone[]> {
  const groups: Record<string, Drone[]> = {};
  const PROXIMITY_KM = 0.01; // 10 meters
  
  for (const drone of drones) {
    let found = false;
    
    for (const key in groups) {
      const [latStr, lngStr] = key.split('_');
      const lat = parseFloat(latStr);
      const lng = parseFloat(lngStr);
      
      // Rough distance check (good enough for clustering)
      const dist = Math.sqrt(Math.pow(drone.lat - lat, 2) + Math.pow(drone.lng - lng, 2));
      if (dist < PROXIMITY_KM) {
        groups[key].push(drone);
        found = true;
        break;
      }
    }
    
    if (!found) {
      const key = `${drone.lat.toFixed(4)}_${drone.lng.toFixed(4)}`;
      groups[key] = [drone];
    }
  }
  
  return groups;
}
