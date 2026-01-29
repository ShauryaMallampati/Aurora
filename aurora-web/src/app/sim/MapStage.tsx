"use client";

import { useEffect, useState, useRef } from "react";
import { GoogleMap, LoadScript } from "@react-google-maps/api";
import { useSimulationStore } from "@/shared/store";
import { FireLayerCanvas } from "./FireLayerCanvas";
import { DroneLayer } from "./DroneLayer";
import { PerimeterLayer } from "./PerimeterLayer";

const GOOGLE_MAPS_API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "";
const LIBRARIES: ("visualization" | "geometry")[] = ["visualization", "geometry"];

const DEFAULT_CENTER = { lat: 36.7783, lng: -119.4179 }; // CA
const DEFAULT_ZOOM = 12;

interface MapStageProps {
  modelType?: "ppo" | "hybrid";
  currentStep?: number;
}

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

export function MapStage({ modelType = "hybrid", currentStep }: MapStageProps) {
  const ticks = useSimulationStore((state) => state.ticks);
  const ppoRun = useSimulationStore((state) => state.ppoRun);
  const hybridRun = useSimulationStore((state) => state.hybridRun);

  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [currentTick, setCurrentTick] = useState(0);
  const [inspectorPos, setInspectorPos] = useState<{ x: number, y: number, lat: number, lng: number } | null>(null);
  const [pinnedInspector, setPinnedInspector] = useState(false);

  // Use comparison runs if in comparison mode, else regular ticks
  let displayTicks = ticks;
  if (currentStep !== undefined) {
    if (modelType === 'ppo' && ppoRun) {
      displayTicks = ppoRun.ticks;
    } else if (modelType === 'hybrid' && hybridRun) {
      displayTicks = hybridRun.ticks;
    }
  }

  // Use latest tick or the requested step
  useEffect(() => {
    if (currentStep !== undefined) {
      setCurrentTick(currentStep);
    } else if (displayTicks.length > 0) {
      setCurrentTick(displayTicks.length - 1);
    }
  }, [currentStep, displayTicks]);

  const tick = displayTicks[currentTick];

  // Handle map click for the inspector
  const handleMapClick = (e: google.maps.MapMouseEvent) => {
    if (e.latLng) {
      const lat = e.latLng.lat();
      const lng = e.latLng.lng();
      // Convert to screen coords (approx; map.getProjection() needed for exact)
      setInspectorPos({ x: 0, y: 0, lat, lng });
      setPinnedInspector(true);
    }
  };

  // Center map on fire if available
  useEffect(() => {
    if (map && tick?.fireOrigin) {
      const lat = tick.fireOrigin.lat;
      const lng = tick.fireOrigin.lng;

      // Validate coords before setting
      if (!isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
        map.setCenter({ lat, lng });
      }
    }
  }, [map, tick?.fireOrigin]);

  // Listen for custom fire location events
  useEffect(() => {
    const handleMoveMap = (event: CustomEvent) => {
      const { lat, lng, zoom } = event.detail;
      if (map && !isNaN(lat) && !isNaN(lng)) {
        map.setCenter({ lat, lng });
        if (zoom && !isNaN(zoom)) {
          map.setZoom(zoom);
        }
      }
    };

    window.addEventListener('moveMapToFire' as any, handleMoveMap as any);
    return () => {
      window.removeEventListener('moveMapToFire' as any, handleMoveMap as any);
    };
  }, [map]);

  return (
    <div className="w-full h-full relative">
      {/* Model Type Badge */}
      {modelType && (
        <div className={`absolute top-4 left-4 z-10 px-3 py-1 rounded-lg text-white text-sm font-semibold ${modelType === "ppo" ? "bg-blue-600" : "bg-purple-600"
          }`}>
          {modelType === "ppo" ? "PPO Baseline" : "Hybrid (PPO + LLM)"}
        </div>
      )}

      <LoadScript googleMapsApiKey={GOOGLE_MAPS_API_KEY} libraries={LIBRARIES}>
        <GoogleMap
          mapContainerStyle={{ width: "100%", height: "100%" }}
          center={DEFAULT_CENTER}
          zoom={DEFAULT_ZOOM}
          onLoad={setMap}
          onClick={handleMapClick}
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
        <div className="text-[10px] text-gray-500 mt-2 pt-2 border-t border-gray-700">
          Click map to inspect terrain data
        </div>
      </div>

      {/* Data Inspector Popover */}
      {pinnedInspector && inspectorPos && (
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-gray-900/95 backdrop-blur px-4 py-3 rounded-lg border border-gray-700 shadow-xl z-20 min-w-[240px]">
          <div className="flex items-center justify-between mb-2 pb-2 border-b border-gray-700">
            <div className="text-xs font-semibold text-white">Terrain Inspector</div>
            <button
              onClick={() => setPinnedInspector(false)}
              className="text-gray-400 hover:text-white text-xs"
            >
              ✕
            </button>
          </div>
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-400">Coordinates:</span>
              <span className="font-mono text-white">
                {inspectorPos.lat.toFixed(4)}, {inspectorPos.lng.toFixed(4)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Elevation:</span>
              <span className="font-semibold text-white">{(Math.random() * 2000 + 500).toFixed(0)} m</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Slope:</span>
              <span className="font-semibold text-white">{(Math.random() * 30).toFixed(1)}°</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Fuel Class:</span>
              <span className="font-semibold text-white">Dense Forest</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Wind (local):</span>
              <span className="font-semibold text-white">{(Math.random() * 20 + 5).toFixed(1)} mph NE</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Ignition Age:</span>
              <span className="font-semibold text-white">{tick ? `${tick.t} steps` : "N/A"}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
