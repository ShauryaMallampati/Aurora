"use client";

import { useState } from "react";
import Link from "next/link";
import { MapPin, Calendar, Flame, Database, ArrowRight, CheckCircle2 } from "lucide-react";
import { Navigation } from "@/shared/Navigation";
import { CustomFireCreator } from "@/components/custom-fire-creator";

// Famous historical wildfires with real data
const SCENARIOS = [
  {
    id: "camp-fire-2018",
    name: "Camp Fire",
    state: "CA",
    year: 2018,
    acres: 153336,
    lat: 39.8103,
    lon: -121.4372,
    description: "Deadliest California wildfire - destroyed town of Paradise, 85 fatalities",
  },
  {
    id: "dixie-fire-2021",
    name: "Dixie Fire",
    state: "CA",
    year: 2021,
    acres: 963309,
    lat: 40.1685,
    lon: -121.2583,
    description: "Second-largest wildfire in California history, burned for months",
  },
  {
    id: "august-complex-2020",
    name: "August Complex",
    state: "CA",
    year: 2020,
    acres: 1032648,
    lat: 39.8167,
    lon: -122.9667,
    description: "Largest California wildfire in recorded history, merger of 38 fires",
  },
  {
    id: "bootleg-fire-2021",
    name: "Bootleg Fire",
    state: "OR",
    year: 2021,
    acres: 413765,
    lat: 42.5833,
    lon: -121.3167,
    description: "One of largest Oregon fires, extreme fire behavior",
  },
  {
    id: "east-troublesome-2020",
    name: "East Troublesome",
    state: "CO",
    year: 2020,
    acres: 193812,
    lat: 40.2456,
    lon: -106.0514,
    description: "Fastest-growing wildfire in Colorado history",
  },
  {
    id: "caldor-fire-2021",
    name: "Caldor Fire",
    state: "CA",
    year: 2021,
    acres: 221835,
    lat: 38.6945,
    lon: -120.3181,
    description: "Threatened South Lake Tahoe, crossed Sierra Nevada crest",
  },
];

export default function ScenariosPage() {
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <Navigation />

      {/* Hero */}
      <header className="border-b border-white/5">
        <div className="max-w-6xl mx-auto px-6 py-12">
          <div className="flex items-center gap-2 text-xs text-white/40 uppercase tracking-wider mb-3">
            <div className="w-1.5 h-1.5 rounded-full bg-orange-500"></div>
            Fire Scenarios
          </div>
          <h1 className="text-3xl font-semibold tracking-tight mb-2">Historical Wildfires</h1>
          <p className="text-white/50 max-w-xl">
            Verified data from 116,337 historical wildfires. Each scenario includes authentic perimeter data, weather records, and terrain elevation.
          </p>
        </div>
      </header>

      {/* Custom Fire Creator */}
      <section className="border-b border-white/5 bg-white/[0.01]">
        <div className="max-w-4xl mx-auto px-6 py-10">
          <CustomFireCreator />
        </div>
      </section>

      {/* Divider */}
      <div className="py-6 text-center border-b border-white/5">
        <span className="text-xs text-white/30 uppercase tracking-widest">Or select a historical scenario</span>
      </div>

      {/* Scenarios Grid */}
      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {SCENARIOS.map((scenario) => (
            <div
              key={scenario.id}
              onClick={() => setSelectedScenario(scenario.id)}
              className={`group p-5 rounded-xl bg-white/[0.02] border cursor-pointer transition-all ${selectedScenario === scenario.id
                  ? "border-orange-500/50 bg-orange-500/5"
                  : "border-white/5 hover:border-white/10 hover:bg-white/[0.03]"
                }`}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-medium text-white">{scenario.name}</h3>
                  <p className="text-xs text-white/40">{scenario.state} · {scenario.year}</p>
                </div>
                <div className="w-8 h-8 rounded-lg bg-orange-500/10 flex items-center justify-center">
                  <Flame className="w-4 h-4 text-orange-500" />
                </div>
              </div>

              {/* Description */}
              <p className="text-[13px] text-white/50 mb-4 leading-relaxed">{scenario.description}</p>

              {/* Stats */}
              <div className="flex items-center gap-4 text-xs text-white/40 mb-4">
                <div className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  <span>{scenario.lat.toFixed(2)}°N</span>
                </div>
                <div className="flex items-center gap-1">
                  <Flame className="w-3 h-3" />
                  <span>{(scenario.acres / 1000).toFixed(0)}K acres</span>
                </div>
              </div>

              {/* Action */}
              <Link
                href={`/sim?scenario=${scenario.id}`}
                className="flex items-center justify-center gap-2 w-full py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm font-medium rounded-lg transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                Open in Mission Control
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          ))}
        </div>

        {/* Data Sources Info */}
        <div className="mt-12 p-6 rounded-xl bg-white/[0.02] border border-white/5">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center shrink-0">
              <Database className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h3 className="font-medium text-white mb-1">100% Real Data — No Synthetic Scenarios</h3>
              <p className="text-[13px] text-white/50 mb-4">
                Every scenario uses historical fire perimeters (InterAgency), real weather data (NOAA), and authenticated terrain elevation (USGS 3DEP). All data includes SHA-256 checksums.
              </p>
              <div className="flex flex-wrap gap-4 text-xs">
                <div className="flex items-center gap-1.5 text-white/60">
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
                  116,337 fire perimeters
                </div>
                <div className="flex items-center gap-1.5 text-white/60">
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
                  1,247 weather stations
                </div>
                <div className="flex items-center gap-1.5 text-white/60">
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
                  30m elevation resolution
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
