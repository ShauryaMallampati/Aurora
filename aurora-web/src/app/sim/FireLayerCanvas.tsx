"use client";

import { useEffect, useRef } from "react";
import type { TelemetryTick } from "@/shared/types";

interface FireLayerCanvasProps {
  tick: TelemetryTick;
  map: google.maps.Map | null;
}

export function FireLayerCanvas({ tick, map }: FireLayerCanvasProps) {
  const overlayRef = useRef<google.maps.OverlayView | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (!map) {
      return;
    }

    const gridData = parseFireGrid(tick.fireGrid);
    if (!gridData) {
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = 512;
    canvas.height = 512;
    canvas.style.opacity = "0.7";
    canvas.style.pointerEvents = "none";
    canvasRef.current = canvas;

    class FireOverlay extends google.maps.OverlayView {
      private canvasElement: HTMLCanvasElement;
      private bounds: google.maps.LatLngBounds;

      constructor(canvasElement: HTMLCanvasElement, bounds: google.maps.LatLngBounds) {
        super();
        this.canvasElement = canvasElement;
        this.bounds = bounds;
      }

      onAdd() {
        const panes = this.getPanes();
        if (panes && !this.canvasElement.parentNode) {
          panes.overlayLayer.appendChild(this.canvasElement);
        }
      }

      draw() {
        const projection = this.getProjection();
        if (!projection) {
          return;
        }

        const sw = projection.fromLatLngToDivPixel(this.bounds.getSouthWest());
        const ne = projection.fromLatLngToDivPixel(this.bounds.getNorthEast());

        if (!sw || !ne) {
          return;
        }

        this.canvasElement.style.position = "absolute";
        this.canvasElement.style.left = `${sw.x}px`;
        this.canvasElement.style.top = `${ne.y}px`;
        this.canvasElement.style.width = `${ne.x - sw.x}px`;
        this.canvasElement.style.height = `${sw.y - ne.y}px`;
      }

      onRemove() {
        if (this.canvasElement.parentNode?.contains(this.canvasElement)) {
          this.canvasElement.parentNode.removeChild(this.canvasElement);
        }
      }
    }

    const center = new google.maps.LatLng(tick.fireOrigin.lat, tick.fireOrigin.lng);
    const latOffset = 0.045;
    const lngOffset = 0.045;
    const bounds = new google.maps.LatLngBounds(
      new google.maps.LatLng(center.lat() - latOffset, center.lng() - lngOffset),
      new google.maps.LatLng(center.lat() + latOffset, center.lng() + lngOffset),
    );

    renderFireGrid(canvas, gridData);

    const overlay = new FireOverlay(canvas, bounds);
    overlay.setMap(map);
    overlayRef.current = overlay;

    return () => {
      overlayRef.current?.setMap(null);
      overlayRef.current = null;
      canvasRef.current = null;
    };
  }, [map, tick]);

  return null;
}

function parseFireGrid(base64: string): number[][] | null {
  try {
    const json = atob(base64);
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function renderFireGrid(canvas: HTMLCanvasElement, grid: number[][]) {
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return;
  }

  const height = grid.length;
  const width = grid[0]?.length || 0;
  if (!height || !width) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    return;
  }

  const cellWidth = canvas.width / width;
  const cellHeight = canvas.height / height;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.filter = "blur(2px)";
  for (let i = 0; i < height; i += 1) {
    for (let j = 0; j < width; j += 1) {
      const intensity = grid[i][j];
      if (intensity > 0.3) {
        ctx.fillStyle = getFireColor(Math.min(1, intensity + 0.2));
        ctx.globalAlpha = 0.5;
        ctx.fillRect(j * cellWidth, i * cellHeight, cellWidth, cellHeight);
      }
    }
  }

  ctx.filter = "none";
  ctx.globalAlpha = 1;

  for (let i = 0; i < height; i += 1) {
    for (let j = 0; j < width; j += 1) {
      const intensity = grid[i][j];
      if (intensity > 0) {
        ctx.fillStyle = getFireColor(intensity);
        ctx.fillRect(j * cellWidth, i * cellHeight, cellWidth, cellHeight);

        if (intensity > 0.8) {
          ctx.fillStyle = "rgba(255, 255, 100, 0.6)";
          const spotSize = cellWidth * 0.6;
          ctx.fillRect(
            j * cellWidth + (cellWidth - spotSize) / 2,
            i * cellHeight + (cellHeight - spotSize) / 2,
            spotSize,
            spotSize,
          );
        }
      }
    }
  }
}

function getFireColor(intensity: number): string {
  const clamped = Math.max(0, Math.min(1, intensity));

  if (clamped < 0.2) {
    const t = clamped / 0.2;
    return `rgb(255, ${Math.floor(200 + (100 - 200) * t)}, 0)`;
  }

  if (clamped < 0.5) {
    const t = (clamped - 0.2) / 0.3;
    return `rgb(255, ${Math.floor(100 + (80 - 100) * t)}, 0)`;
  }

  if (clamped < 0.75) {
    const t = (clamped - 0.5) / 0.25;
    return `rgb(255, ${Math.floor(80 - 80 * t)}, 0)`;
  }

  const t = (clamped - 0.75) / 0.25;
  return `rgb(${Math.floor(255 - 100 * t)}, 0, 0)`;
}
