"use client";

import { useEffect, useState, useRef } from "react";
import { GoogleMap, LoadScript } from "@react-google-maps/api";
import { useSimulationStore } from "@/shared/store";
import { FireLayerCanvas } from "./FireLayerCanvas";
import { DroneLayer } from "./DroneLayer";
import { PerimeterLayer } from "./PerimeterLayer";

const GOOGLE_MAPS_API_KEY = "AIzaSyAso8orI4spYSUPjqqLv9TIoqMjihI3KfE";
const LIBRARIES: ("visualization" | "geometry")[] = ["visualization", "geometry"];

const DEFAULT_CENTER = { lat: 36.7783, lng: -119.4179 }; // California
const DEFAULT_ZOOM = 12;

const MAP_STYLES = [
  {
    featureType: "all",
    elementType: "labels",
    stylers: [{ visibility: "off" }],
  },
  {
    featureType: "landscape",
    elementType: "geometry",
    stylers: [{ color: "#1a1a1a" }],
  },
  {
    featureType: "water",
    elementType: "geometry",
    stylers: [{ color: "#0a0a0a" }],
  },
];

export function MapStage() {
  const ticks = useSimulationStore((state) => state.ticks);
  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [currentTick, setCurrentTick] = useState(0);

  // Get latest tick
  useEffect(() => {
    if (ticks.length > 0) {
      setCurrentTick(ticks.length - 1);
    }
  }, [ticks]);

  const tick = ticks[currentTick];

  // Center map on fire if available
  useEffect(() => {
    if (map && tick?.fireOrigin) {
      const center = {
        lat: tick.fireOrigin.lat,
        lng: tick.fireOrigin.lng,
      };
      map.setCenter(center);
    }
  }, [map, tick?.fireOrigin]);

  return (
    <div className="w-full h-full relative">
      <LoadScript googleMapsApiKey={GOOGLE_MAPS_API_KEY} libraries={LIBRARIES}>
        <GoogleMap
          mapContainerStyle={{ width: "100%", height: "100%" }}
          center={tick?.fireOrigin || DEFAULT_CENTER}
          zoom={DEFAULT_ZOOM}
          onLoad={setMap}
          options={{
            styles: MAP_STYLES,
            disableDefaultUI: true,
            zoomControl: true,
            gestureHandling: "greedy",
            mapTypeId: "terrain",
          }}
        >
          {/* Fire Heat Layer */}
          {tick && <FireLayerCanvas tick={tick} map={map} />}

          {/* Perimeter Layer */}
          {tick && <PerimeterLayer />}

          {/* Drone Markers */}
          {tick && <DroneLayer tick={tick} />}
        </GoogleMap>
      </LoadScript>

      {/* Timestep Indicator */}
      {tick && (
        <div className="absolute top-4 left-4 bg-gray-900/90 backdrop-blur px-4 py-2 rounded-lg border border-gray-800">
          <div className="text-xs text-gray-400">Timestep</div>
          <div className="text-2xl font-bold text-white">{tick.t}</div>
          <div className="text-xs text-gray-400 mt-1">
            {new Date(tick.timestamp).toLocaleTimeString()}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-gray-900/90 backdrop-blur px-4 py-3 rounded-lg border border-gray-800">
        <div className="text-xs font-semibold text-white mb-2">Legend</div>
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-gradient-to-r from-orange-500 to-red-600 rounded"></div>
            <span className="text-xs text-gray-300">Fire Intensity</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span className="text-xs text-gray-300">Drone (Idle)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-cyan-500 rounded"></div>
            <span className="text-xs text-gray-300">Drone (Drop)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-purple-500 rounded"></div>
            <span className="text-xs text-gray-300">Drone (Scout)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 border-2 border-red-500 rounded-full"></div>
            <span className="text-xs text-gray-300">Fire Perimeter</span>
          </div>
        </div>
      </div>
    </div>
  );
}
