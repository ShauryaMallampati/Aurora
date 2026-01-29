"use client";

import { Marker, InfoWindow } from "@react-google-maps/api";
import { useState } from "react";
import type { TelemetryTick, Drone } from "@/shared/types";
import { Wind, Mountain, Droplets, Flame, TrendingUp, Brain } from "lucide-react";
import { DroneActionPopover, generateMockDroneActions } from "@/components/ui/drone-action-popover";

interface DroneLayerProps {
  tick: TelemetryTick;
}

export function DroneLayer({ tick }: DroneLayerProps) {
  const [selectedDrone, setSelectedDrone] = useState<number | null>(null);
  const [hoveredDrone, setHoveredDrone] = useState<number | null>(null);

  // Group drones by proximity for big swarms (avoid overlap)
  const droneGroups = tick.drones.length > 20 ? groupDronesByProximity(tick.drones) : null;
  
  const dronesToRender = droneGroups ? Object.values(droneGroups).map(group => group[0]) : tick.drones;

  // Mock local conditions (swap in real obs later)
  const getLocalConditions = (drone: Drone) => {
    return {
      windSpeed: 12.5 + Math.random() * 5,
      windDirection: "NE",
      slope: 15 + Math.random() * 10,
      fuelDensity: 0.7 + Math.random() * 0.2,
      nearbyFire: Math.random() > 0.5,
      fireIntensity: Math.random() * 100,
    };
  };

  // Mock action reasoning (swap in LLM/model attribution later)
  const getActionReasoning = (drone: Drone) => {
    const reasons: Record<string, string> = {
      drop: "High fire intensity detected nearby. Water deployment prioritized.",
      scout: "No active fires in vicinity. Scouting for new ignition points.",
      recharge: "Battery below 20% threshold. Returning to base for recharge.",
      refill: "Water reserves depleted. Refilling from nearest water source.",
      move: "Repositioning to high-priority zone based on wind direction.",
    };
    return reasons[drone.action] || "Executing optimal action based on policy.";
  };

  // Mock feature attributions (swap in SHAP/attention later)
  const getFeatureAttributions = (drone: Drone) => {
    const features = [
      { name: "Nearby Fire Intensity", value: 0.42, positive: true },
      { name: "Wind Direction (NE)", value: 0.28, positive: true },
      { name: "Water Remaining", value: -0.21, positive: false },
      { name: "Distance to Base", value: -0.15, positive: false },
      { name: "Slope Gradient", value: 0.12, positive: true },
    ];
    return features.slice(0, 3); // top 3
  };

  return (
    <>
      {dronesToRender.map((drone) => {
        const conditions = getLocalConditions(drone);
        const reasoning = getActionReasoning(drone);
        const features = getFeatureAttributions(drone);
        
        // Find nearby drones if grouped
        const nearbyDrones = droneGroups ? droneGroups[`${drone.lat.toFixed(4)}_${drone.lng.toFixed(4)}`] : [drone];
        const count = nearbyDrones?.length || 1;

        return (
          <div key={drone.id}>
            {/* Popover Container - Outside Marker */}
            <DroneActionPopover
              droneId={String(drone.id)}
              lat={drone.lat}
              lng={drone.lng}
              actions={generateMockDroneActions(String(drone.id))}
              isOpen={hoveredDrone === drone.id}
              onHover={(isOpen) => setHoveredDrone(isOpen ? drone.id : null)}
            />
            
            {/* Marker */}
            <Marker
              key={`marker_${drone.id}`}
              position={{ lat: drone.lat, lng: drone.lng }}
              icon={{
                path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
                fillColor: getDroneColor(drone.action),
                fillOpacity: 0.9,
                strokeColor: hoveredDrone === drone.id ? "#ffeb3b" : "#ffffff",
                strokeWeight: count > 1 ? 3 : 2,
                scale: count > 1 ? 8 : 6,
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
                        <span className="text-gray-600">Fuel:</span>
                        <span className="font-semibold">{(conditions.fuelDensity * 100).toFixed(0)}%</span>
                      </div>
                      {conditions.nearbyFire && (
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
          </div>
        );
      })}
    </>
  );
}

function getDroneColor(action: string): string {
  switch (action) {
    case "drop":
      return "#06b6d4"; // cyan
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
