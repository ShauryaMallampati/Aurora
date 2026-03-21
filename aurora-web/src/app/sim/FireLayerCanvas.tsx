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

    const activeBounds = getActiveFireBounds(gridData);
    if (!activeBounds) {
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = 512;
    canvas.height = 512;
    canvas.style.opacity = "0.9";
    canvas.style.pointerEvents = "none";
    canvas.style.mixBlendMode = "multiply";
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
    const latSpan = 0.09;
    const lngSpan = 0.09;
    const latPerCell = latSpan / gridData.length;
    const lngPerCell = lngSpan / (gridData[0]?.length || 1);
    const north = center.lat() + latSpan / 2 - activeBounds.minY * latPerCell;
    const south = center.lat() + latSpan / 2 - (activeBounds.maxY + 1) * latPerCell;
    const west = center.lng() - lngSpan / 2 + activeBounds.minX * lngPerCell;
    const east = center.lng() - lngSpan / 2 + (activeBounds.maxX + 1) * lngPerCell;
    const bounds = new google.maps.LatLngBounds(
      new google.maps.LatLng(south, west),
      new google.maps.LatLng(north, east),
    );

    renderFireGrid(canvas, gridData, activeBounds);

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

function renderFireGrid(
  canvas: HTMLCanvasElement,
  grid: number[][],
  bounds: { minX: number; maxX: number; minY: number; maxY: number },
) {
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return;
  }

  const height = bounds.maxY - bounds.minY + 1;
  const width = bounds.maxX - bounds.minX + 1;
  if (!height || !width) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    return;
  }

  const cellWidth = canvas.width / width;
  const cellHeight = canvas.height / height;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.filter = "blur(3px)";
  for (let i = bounds.minY; i <= bounds.maxY; i += 1) {
    for (let j = bounds.minX; j <= bounds.maxX; j += 1) {
      const intensity = grid[i][j];
      if (intensity > 0.08) {
        const localX = j - bounds.minX;
        const localY = i - bounds.minY;
        ctx.fillStyle = getFireColor(Math.min(1, intensity + 0.25));
        ctx.globalAlpha = 0.58;
        ctx.fillRect(localX * cellWidth, localY * cellHeight, cellWidth, cellHeight);
      }
    }
  }

  ctx.filter = "none";
  ctx.globalAlpha = 1;

  for (let i = bounds.minY; i <= bounds.maxY; i += 1) {
    for (let j = bounds.minX; j <= bounds.maxX; j += 1) {
      const intensity = grid[i][j];
      if (intensity > 0.05) {
        const localX = j - bounds.minX;
        const localY = i - bounds.minY;
        ctx.fillStyle = getFireColor(intensity);
        ctx.fillRect(localX * cellWidth, localY * cellHeight, cellWidth, cellHeight);

        if (intensity > 0.8) {
          ctx.fillStyle = "rgba(255, 247, 153, 0.75)";
          const spotSize = cellWidth * 0.6;
          ctx.fillRect(
            localX * cellWidth + (cellWidth - spotSize) / 2,
            localY * cellHeight + (cellHeight - spotSize) / 2,
            spotSize,
            spotSize,
          );
        }
      }
    }
  }
}

function getActiveFireBounds(grid: number[][]): { minX: number; maxX: number; minY: number; maxY: number } | null {
  const height = grid.length;
  const width = grid[0]?.length || 0;
  if (!height || !width) {
    return null;
  }

  let minX = width;
  let minY = height;
  let maxX = -1;
  let maxY = -1;

  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      if (grid[y][x] > 0.08) {
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x);
        maxY = Math.max(maxY, y);
      }
    }
  }

  if (maxX < 0 || maxY < 0) {
    return null;
  }

  const padding = 2;
  return {
    minX: Math.max(0, minX - padding),
    minY: Math.max(0, minY - padding),
    maxX: Math.min(width - 1, maxX + padding),
    maxY: Math.min(height - 1, maxY + padding),
  };
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
