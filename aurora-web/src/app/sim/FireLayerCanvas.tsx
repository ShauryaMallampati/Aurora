"use client";

import { useEffect, useRef } from "react";
import type { TelemetryTick } from "@/shared/types";

interface FireLayerCanvasProps {
  tick: TelemetryTick;
  map: google.maps.Map | null;
}

export function FireLayerCanvas({ tick, map }: FireLayerCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const overlayRef = useRef<google.maps.OverlayView | null>(null);

  useEffect(() => {
    if (!map || !canvasRef.current) return;

    // Parse fire grid
    const gridData = parseFireGrid(tick.fireGrid);
    if (!gridData) return;

    // Create custom overlay
    class FireOverlay extends google.maps.OverlayView {
      private canvas: HTMLCanvasElement;
      private bounds: google.maps.LatLngBounds;

      constructor(canvas: HTMLCanvasElement, bounds: google.maps.LatLngBounds) {
        super();
        this.canvas = canvas;
        this.bounds = bounds;
      }

      onAdd() {
        const panes = this.getPanes();
        if (panes) {
          panes.overlayLayer.appendChild(this.canvas);
        }
      }

      draw() {
        const overlayProjection = this.getProjection();
        if (!overlayProjection) return;

        const sw = overlayProjection.fromLatLngToDivPixel(this.bounds.getSouthWest()!);
        const ne = overlayProjection.fromLatLngToDivPixel(this.bounds.getNorthEast()!);

        if (sw && ne) {
          this.canvas.style.left = sw.x + "px";
          this.canvas.style.top = ne.y + "px";
          this.canvas.style.width = ne.x - sw.x + "px";
          this.canvas.style.height = sw.y - ne.y + "px";
          this.canvas.style.position = "absolute";
        }
      }

      onRemove() {
        if (this.canvas.parentNode) {
          this.canvas.parentNode.removeChild(this.canvas);
        }
      }
    }

    // Calculate bounds (10km x 10km around fire origin)
    const center = new google.maps.LatLng(tick.fireOrigin.lat, tick.fireOrigin.lng);
    const latOffset = 0.045; // ~5km
    const lngOffset = 0.045;
    const bounds = new google.maps.LatLngBounds(
      new google.maps.LatLng(center.lat() - latOffset, center.lng() - lngOffset),
      new google.maps.LatLng(center.lat() + latOffset, center.lng() + lngOffset)
    );

    // Render fire to canvas
    renderFireGrid(canvasRef.current, gridData);

    // Create and add overlay
    const overlay = new FireOverlay(canvasRef.current, bounds);
    overlay.setMap(map);
    overlayRef.current = overlay;

    return () => {
      if (overlayRef.current) {
        overlayRef.current.setMap(null);
      }
    };
  }, [tick, map]);

  return (
    <canvas
      ref={canvasRef}
      width={512}
      height={512}
      style={{ opacity: 0.7, pointerEvents: "none" }}
    />
  );
}

function parseFireGrid(base64: string): number[][] | null {
  try {
    const json = atob(base64);
    const grid = JSON.parse(json);
    return grid;
  } catch {
    return null;
  }
}

function renderFireGrid(canvas: HTMLCanvasElement, grid: number[][]) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const height = grid.length;
  const width = grid[0]?.length || 0;
  
  const cellWidth = canvas.width / width;
  const cellHeight = canvas.height / height;

  // Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Render each cell
  for (let i = 0; i < height; i++) {
    for (let j = 0; j < width; j++) {
      const intensity = grid[i][j];
      if (intensity > 0) {
        const color = getFireColor(intensity);
        ctx.fillStyle = color;
        ctx.fillRect(j * cellWidth, i * cellHeight, cellWidth, cellHeight);
      }
    }
  }
}

function getFireColor(intensity: number): string {
  // Intensity: 0 (none) to 1 (max)
  const clamped = Math.max(0, Math.min(1, intensity));
  
  if (clamped < 0.33) {
    // Orange
    const r = 255;
    const g = Math.floor(165 + (255 - 165) * (clamped / 0.33));
    return `rgb(${r}, ${g}, 0)`;
  } else if (clamped < 0.66) {
    // Orange to red
    const t = (clamped - 0.33) / 0.33;
    const r = 255;
    const g = Math.floor(165 * (1 - t));
    return `rgb(${r}, ${g}, 0)`;
  } else {
    // Red to dark red
    const t = (clamped - 0.66) / 0.34;
    const r = Math.floor(255 - 100 * t);
    return `rgb(${r}, 0, 0)`;
  }
}
