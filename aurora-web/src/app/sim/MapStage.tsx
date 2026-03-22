"use client";

import { useEffect, useRef, useState } from "react";
import { GoogleMap, useJsApiLoader } from "@react-google-maps/api";
import { publicEnv } from "@/lib/env";
import { useSimulationStore } from "@/shared/store";
import { DroneLayer } from "./DroneLayer";
import { FireLayerCanvas } from "./FireLayerCanvas";
import { PerimeterLayer } from "./PerimeterLayer";

const GOOGLE_MAPS_API_KEY = publicEnv.googleMapsApiKey;
const hasGoogleMapsKey = Boolean(GOOGLE_MAPS_API_KEY.trim());
const LIBRARIES: ("visualization" | "geometry")[] = ["visualization", "geometry"];

const DEFAULT_CENTER = {
  lat: publicEnv.mapDefaults.lat,
  lng: publicEnv.mapDefaults.lng,
};
const DEFAULT_ZOOM = publicEnv.mapDefaults.zoom;

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
    stylers: [{ color: "#dde5ec" }],
  },
  {
    featureType: "water",
    elementType: "geometry",
    stylers: [{ color: "#aebfd3" }],
  },
  {
    featureType: "road",
    elementType: "geometry",
    stylers: [{ color: "#c7d2de" }],
  },
  {
    featureType: "poi",
    elementType: "geometry",
    stylers: [{ color: "#c7d9c7" }],
  },
  {
    featureType: "administrative",
    elementType: "geometry.stroke",
    stylers: [{ color: "#94a3b8" }, { weight: 0.6 }],
  },
];

export function MapStage({ modelType = "hybrid", currentStep }: MapStageProps) {
  const ticks = useSimulationStore((state) => state.ticks);
  const ppoRun = useSimulationStore((state) => state.ppoRun);
  const hybridRun = useSimulationStore((state) => state.hybridRun);
  const runId = useSimulationStore((state) => state.runId);
  const config = useSimulationStore((state) => state.config);

  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [currentTick, setCurrentTick] = useState(0);
  const [inspectorPos, setInspectorPos] = useState<{ lat: number; lng: number } | null>(null);
  const focusedRunRef = useRef<string | null>(null);
  const { isLoaded: isMapLoaded, loadError } = useJsApiLoader({
    id: "aurora-google-maps",
    googleMapsApiKey: GOOGLE_MAPS_API_KEY,
    libraries: LIBRARIES,
  });

  let displayTicks = ticks;
  if (currentStep !== undefined) {
    if (modelType === "ppo" && ppoRun) {
      displayTicks = ppoRun.ticks;
    } else if (modelType === "hybrid" && hybridRun) {
      displayTicks = hybridRun.ticks;
    }
  }

  useEffect(() => {
    if (currentStep !== undefined) {
      setCurrentTick(currentStep);
    } else if (displayTicks.length > 0) {
      setCurrentTick(displayTicks.length - 1);
    }
  }, [currentStep, displayTicks]);

  const tick = displayTicks[currentTick];
  const containmentPercent = tick ? Math.round(tick.metrics.containment * 100) : 0;
  const activeFireLabel = tick
    ? containmentPercent >= 100
      ? "Contained"
      : containmentPercent >= 70
        ? "Contained edge"
        : "Active fire"
    : "Waiting";
  const overlayPanelClass =
    "rounded-md border border-slate-700/90 bg-slate-950 px-4 py-3 text-white shadow-[0_14px_34px_rgba(15,23,42,0.48)]";

  useEffect(() => {
    if (!map || !tick?.fireOrigin) {
      return;
    }

    const { lat, lng } = tick.fireOrigin;
    if (!Number.isNaN(lat) && !Number.isNaN(lng)) {
      const shouldRefocus =
        (runId && focusedRunRef.current !== runId) ||
        (!runId && tick.t === 0 && focusedRunRef.current !== "__tick0__");

      if (shouldRefocus) {
        map.panTo({ lat, lng });
        map.setZoom(getFireZoom(config));
        focusedRunRef.current = runId ?? "__tick0__";
        return;
      }

      if (tick.t <= 2) {
        map.panTo({ lat, lng });
      }
    }
  }, [config, map, runId, tick]);

  useEffect(() => {
    const handleMoveMap = (event: Event) => {
      const customEvent = event as CustomEvent<{ lat: number; lng: number; zoom?: number }>;
      const { lat, lng, zoom } = customEvent.detail;

      if (!map || Number.isNaN(lat) || Number.isNaN(lng)) {
        return;
      }

      map.setCenter({ lat, lng });
      if (zoom !== undefined && !Number.isNaN(zoom)) {
        map.setZoom(zoom);
      }
    };

    window.addEventListener("moveMapToFire", handleMoveMap as EventListener);
    return () => {
      window.removeEventListener("moveMapToFire", handleMoveMap as EventListener);
    };
  }, [map]);

  const handleMapClick = (event: google.maps.MapMouseEvent) => {
    if (!event.latLng) {
      return;
    }

    const lat = event.latLng.lat();
    const lng = event.latLng.lng();

    setInspectorPos({ lat, lng });
    window.dispatchEvent(
      new CustomEvent("setCustomFireLocation", {
        detail: { lat, lng },
      }),
    );
  };

  return (
    <div className="relative h-full w-full bg-slate-200">
      {!hasGoogleMapsKey ? (
        <div className="flex h-full items-center justify-center p-6">
          <div className="max-w-xl rounded-md border border-slate-300 bg-white p-6 text-center">
            <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
              Map unavailable
            </p>
            <h2 className="mt-3 text-2xl font-semibold text-slate-900">
              Google Maps requires `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`
            </h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">
              The simulator can still stream logs and telemetry locally, but the map overlay is disabled
              until the public key is present.
            </p>
            {tick ? (
              <div className="mt-6 rounded-md border border-slate-300 bg-slate-50 p-4 text-left">
                <p className="text-xs uppercase tracking-[0.08em] text-slate-500">Current step</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">{tick.t}</p>
                <p className="mt-1 text-sm text-slate-600">
                  {new Date(tick.timestamp).toLocaleTimeString()}
                </p>
              </div>
            ) : (
              <p className="mt-6 text-sm text-slate-500">No telemetry has been streamed yet.</p>
            )}
          </div>
        </div>
      ) : loadError ? (
        <div className="flex h-full items-center justify-center p-6">
          <div className="max-w-xl rounded-md border border-slate-300 bg-white p-6 text-center">
            <p className="text-xs font-medium uppercase tracking-[0.08em] text-slate-500">
              Map unavailable
            </p>
            <h2 className="mt-3 text-2xl font-semibold text-slate-900">
              Google Maps failed to load
            </h2>
            <p className="mt-3 text-sm leading-7 text-slate-600">
              The simulator is running, but the map script could not be initialized in this browser session.
            </p>
          </div>
        </div>
      ) : !isMapLoaded ? (
        <div className="flex h-full items-center justify-center bg-slate-200">
          <div className="rounded-md border border-slate-300 bg-white px-4 py-3 text-sm text-slate-700">
            Loading map…
          </div>
        </div>
      ) : (
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
          {tick ? <FireLayerCanvas tick={tick} map={map} /> : null}
          {tick ? <PerimeterLayer /> : null}
          {tick ? <DroneLayer tick={tick} /> : null}
        </GoogleMap>
      )}

      <div className="absolute left-4 top-4 z-10 flex max-w-sm flex-col gap-3">
        <div className={overlayPanelClass}>
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-300">Model</p>
          <p className="mt-1 text-sm font-semibold text-white">
            {modelType === "ppo" ? "PPO baseline" : "Hybrid controller"}
          </p>
        </div>

        {tick ? (
          <div className={overlayPanelClass}>
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-300">Telemetry</p>
            <div className="mt-2 grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-slate-200">Step</p>
                <p className="font-mono text-white">{tick.t}</p>
              </div>
              <div>
                <p className="text-slate-200">Containment</p>
                <p className="font-mono text-white">{(tick.metrics.containment * 100).toFixed(0)}%</p>
              </div>
              <div>
                <p className="text-slate-200">Burned area</p>
                <p className="font-mono text-white">{tick.metrics.burnedArea.toFixed(1)} acres</p>
              </div>
              <div>
                <p className="text-slate-200">Water dropped</p>
                <p className="font-mono text-white">{tick.metrics.waterDropped.toFixed(1)} L</p>
              </div>
            </div>
            <p className="mt-3 text-xs text-slate-300">
              {new Date(tick.timestamp).toLocaleTimeString()}
            </p>
          </div>
        ) : null}
      </div>

      {tick ? (
        <div className={`absolute right-4 top-4 z-10 text-sm ${overlayPanelClass}`}>
          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-300">Fire state</p>
          <p className="mt-1 font-semibold text-white">{activeFireLabel}</p>
          <p className="mt-2 text-xs text-slate-200">
            {containmentPercent}% contained · {tick.metrics.burnedArea.toFixed(1)} acres burning
          </p>
        </div>
      ) : null}

      <div className={`absolute bottom-4 left-4 z-10 text-sm ${overlayPanelClass}`}>
        <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-300">Legend</p>
        <div className="mt-3 space-y-2">
          <LegendRow swatchClassName="bg-orange-500" label="Fire intensity raster" />
          <LegendRow swatchClassName="bg-sky-500" label="Drone marker" />
          <LegendRow swatchClassName="bg-cyan-400" label="Water-drop radius" />
          <LegendRow swatchClassName="bg-purple-500" label="Scout radius" />
          <LegendRow swatchClassName="border-2 border-red-500" label="Perimeter" />
        </div>
      </div>

      {inspectorPos ? (
        <div className={`absolute bottom-4 right-4 z-20 min-w-[260px] text-sm ${overlayPanelClass}`}>
          <div className="flex items-center justify-between gap-4 border-b border-slate-800 pb-2">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-slate-300">
              Point inspector
            </p>
            <button
              onClick={() => setInspectorPos(null)}
              className="text-xs text-slate-300 transition hover:text-white"
            >
              Close
            </button>
          </div>

          <div className="mt-3 space-y-2">
            <InspectorRow
              label="Coordinates"
              value={`${inspectorPos.lat.toFixed(4)}, ${inspectorPos.lng.toFixed(4)}`}
            />
            <InspectorRow
              label="Wind"
              value={
                tick
                  ? `${tick.weather.windSpeed.toFixed(1)} m/s @ ${Math.round(tick.weather.windDir)}°`
                  : "N/A"
              }
            />
            <InspectorRow
              label="Temperature"
              value={tick ? `${tick.weather.temp.toFixed(1)}°C` : "N/A"}
            />
            <InspectorRow
              label="Humidity"
              value={tick ? `${(tick.weather.humidity * 100).toFixed(0)}%` : "N/A"}
            />
            <InspectorRow
              label="Burned area"
              value={tick ? `${tick.metrics.burnedArea.toFixed(1)} acres` : "N/A"}
            />
            <InspectorRow
              label="Elapsed steps"
              value={tick ? String(tick.t) : "N/A"}
            />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function getFireZoom(config: ReturnType<typeof useSimulationStore.getState>["config"]) {
  if (config?.scenarioId === "custom") {
    switch (config.customScenario?.fireSize) {
      case "small":
        return 13;
      case "medium":
        return 12;
      case "large":
        return 11;
      case "extreme":
        return 10;
      default:
        return 12;
    }
  }

  return 11;
}

function LegendRow({
  swatchClassName,
  label,
}: {
  swatchClassName: string;
  label: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <div className={`h-3 w-3 rounded-sm ${swatchClassName}`} />
      <span className="text-xs text-slate-100">{label}</span>
    </div>
  );
}

function InspectorRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <span className="text-slate-200">{label}</span>
      <span className="text-right font-mono text-white">{value}</span>
    </div>
  );
}
