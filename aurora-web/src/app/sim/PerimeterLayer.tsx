"use client";

import { Polygon } from "@react-google-maps/api";
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
          fillColor: "#ef4444",
          fillOpacity: 0.1,
          strokeColor: "#ef4444",
          strokeOpacity: 0.8,
          strokeWeight: 2,
        }}
      />
    );
  } catch (e) {
    // invalid geojson or unexpected structure
    return null;
  }
}
