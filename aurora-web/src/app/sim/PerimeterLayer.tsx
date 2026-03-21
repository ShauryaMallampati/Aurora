"use client";

import { Circle, Polygon } from "@react-google-maps/api";
import { useSimulationStore } from "@/shared/store";

export function PerimeterLayer() {
  const tick = useSimulationStore((state) => state.currentTick);
  if (!tick) return null;
  const perimeterEvent = ((tick.events as any[]) || []).find(
    (event: any) => !!event.perimeterGeoJSON
  ) as { perimeterGeoJSON: string } | undefined;
  if (!perimeterEvent?.perimeterGeoJSON) return null;

  try {
    const geojson = JSON.parse(perimeterEvent.perimeterGeoJSON);
    const coordinates = geojson.coordinates[0]; // Assume Polygon

    const path = coordinates.map((coord: [number, number]) => ({
      lat: coord[1],
      lng: coord[0],
    }));

    return (
      <Polygon
        paths={path}
        options={{
          fillColor: "#fb7185",
          fillOpacity: 0.08,
          strokeColor: "#dc2626",
          strokeOpacity: 0.95,
          strokeWeight: 3,
        }}
      />
    );
  } catch (e) {
    // Fall back to a derived circular perimeter below.
  }

  const radiusMeters = Math.max(45, (tick.metrics.firePerimeter * 1000) / (2 * Math.PI));
  if (radiusMeters <= 45 && tick.metrics.burnedArea <= 0) {
    return null;
  }

  return (
    <Circle
      center={tick.fireOrigin}
      radius={radiusMeters}
      options={{
        fillColor: "#f97316",
        fillOpacity: 0.06,
        strokeColor: "#dc2626",
        strokeOpacity: 0.95,
        strokeWeight: 3,
        clickable: false,
      }}
    />
  );
}
