"use client";

import { Marker, InfoWindow } from "@react-google-maps/api";
import { useState } from "react";
import type { TelemetryTick, Drone } from "@/shared/types";

interface DroneLayerProps {
  tick: TelemetryTick;
}

export function DroneLayer({ tick }: DroneLayerProps) {
  const [selectedDrone, setSelectedDrone] = useState<number | null>(null);

  return (
    <>
      {tick.drones.map((drone) => (
        <Marker
          key={drone.id}
          position={{ lat: drone.lat, lng: drone.lng }}
          icon={{
            path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
            fillColor: getDroneColor(drone.action),
            fillOpacity: 0.9,
            strokeColor: "#ffffff",
            strokeWeight: 2,
            scale: 6,
            rotation: drone.heading,
          }}
          onClick={() => setSelectedDrone(drone.id)}
        >
          {selectedDrone === drone.id && (
            <InfoWindow onCloseClick={() => setSelectedDrone(null)}>
              <div className="text-gray-900 p-2">
                <div className="font-bold mb-1">Drone {drone.id}</div>
                <div className="text-sm space-y-1">
                  <div>Action: {drone.action}</div>
                  <div>Battery: {Math.round(drone.battery * 100)}%</div>
                  <div>Water: {Math.round(drone.water * 100)}%</div>
                  <div>Heading: {Math.round(drone.heading)}°</div>
                  <div className="text-xs text-gray-600 mt-2">
                    ({drone.lat.toFixed(4)}, {drone.lng.toFixed(4)})
                  </div>
                </div>
              </div>
            </InfoWindow>
          )}
        </Marker>
      ))}
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
