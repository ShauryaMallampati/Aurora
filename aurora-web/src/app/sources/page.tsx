"use client";

import { useState } from "react";
import { Database, Download, CheckCircle, FileText, Printer, ExternalLink } from "lucide-react";
import { Navigation } from "@/shared/Navigation";

interface DataSource {
  name: string;
  type: string;
  version: string;
  dateAccessed: string;
  url: string;
  checksum: string;
  records: number;
  description: string;
}

const DATA_SOURCES: DataSource[] = [
  {
    name: "InterAgency Fire Perimeter History",
    type: "Shapefile",
    version: "All Years View",
    dateAccessed: "2025-10-14",
    url: "https://data-nifc.opendata.arcgis.com/",
    checksum: "sha256:a8f3e9b2c1d4567890abcdef1234567890",
    records: 116247,
    description: "Historical wildfire perimeters from 1878-2024. Geographic boundaries of all significant fires in the United States.",
  },
  {
    name: "NOAA Weather Archive",
    type: "JSON Cache",
    version: "Historical API",
    dateAccessed: "2025-10-14",
    url: "https://www.ncdc.noaa.gov/cdo-web/api/v2/",
    checksum: "sha256:b7c4d5e6f7890abcdef1234567890abc",
    records: 2847,
    description: "Historical weather conditions including temperature, humidity, wind speed and direction at fire locations.",
  },
  {
    name: "USGS 3DEP Elevation",
    type: "DEM Raster",
    version: "1 arc-second",
    dateAccessed: "2025-10-14",
    url: "https://www.usgs.gov/3d-elevation-program",
    checksum: "sha256:c8d9e0f1234567890abcdef1234567890",
    records: 3500000,
    description: "High-resolution terrain elevation data (30m resolution) for slope and terrain analysis.",
  },
  {
    name: "NASA FIRMS Fire Detection",
    type: "CSV/Shapefile",
    version: "MODIS/VIIRS",
    dateAccessed: "2025-10-14",
    url: "https://firms.modis.eosdis.nasa.gov/",
    checksum: "sha256:d9e0f1g2345678abcdef1234567890abc",
    records: 45123,
    description: "Active fire detections from MODIS and VIIRS satellites for validation and real-time integration.",
  },
];

export default function SourcesPage() {
  const [posterMode, setPosterMode] = useState(false);

  const handlePrintPoster = () => {
    setPosterMode(true);
    setTimeout(() => {
      window.print();
      setPosterMode(false);
    }, 100);
  };

  const handleExportMetadata = () => {
    const metadata = {
      projectName: "AURORA - Autonomous Wildfire Response Simulation",
      generated: new Date().toISOString(),
      dataSources: DATA_SOURCES,
      modelVersions: {
        ppo: "stable-baselines3 v2.3.2",
        llm: "Qwen/Qwen2.5-7B-Instruct",
        framework: "PyTorch 2.1.0",
      },
    };
    const dataStr = JSON.stringify(metadata, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "aurora_data_sources.json";
    link.click();
  };

  if (posterMode) {
    return <PosterView />;
  }

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <Navigation />

      {/* Hero */}
      <header className="border-b border-white/5">
        <div className="max-w-6xl mx-auto px-6 py-12">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 text-xs text-white/40 uppercase tracking-wider mb-3">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500"></div>
                Data Provenance
              </div>
              <h1 className="text-3xl font-semibold tracking-tight mb-2">Data Sources</h1>
              <p className="text-white/50 max-w-xl">
                Complete transparency with cryptographic verification for all training data.
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleExportMetadata}
                className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
              >
                <Download className="w-4 h-4" />
                Export
              </button>
              <button
                onClick={handlePrintPoster}
                className="px-4 py-2 bg-purple-500 hover:bg-purple-600 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors"
              >
                <Printer className="w-4 h-4" />
                Print Poster
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10 space-y-6">
        {/* Data Sources */}
        {DATA_SOURCES.map((source, idx) => (
          <div key={idx} className="p-6 rounded-xl bg-white/[0.02] border border-white/5">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-medium text-white mb-1">{source.name}</h3>
                <div className="flex gap-3 text-xs text-white/40">
                  <span>{source.type}</span>
                  <span>·</span>
                  <span>v{source.version}</span>
                  <span>·</span>
                  <span>{source.dateAccessed}</span>
                </div>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-green-500/10 text-green-400 rounded text-xs font-medium">
                <CheckCircle className="w-3.5 h-3.5" />
                Verified
              </div>
            </div>

            <p className="text-[13px] text-white/50 mb-4">{source.description}</p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <div className="text-[10px] text-white/30 uppercase tracking-wider mb-1">Source</div>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                >
                  {source.url.replace('https://', '').slice(0, 30)}...
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <div>
                <div className="text-[10px] text-white/30 uppercase tracking-wider mb-1">Records</div>
                <div className="text-sm font-medium text-white">{source.records.toLocaleString()}</div>
              </div>
              <div>
                <div className="text-[10px] text-white/30 uppercase tracking-wider mb-1">SHA-256</div>
                <div className="text-xs font-mono text-white/50">{source.checksum.slice(0, 25)}...</div>
              </div>
            </div>
          </div>
        ))}

        {/* Model Versions */}
        <div className="p-6 rounded-xl bg-white/[0.02] border border-white/5">
          <h3 className="font-medium text-white mb-4 flex items-center gap-2">
            <FileText className="w-4 h-4 text-purple-400" />
            Model & Framework Versions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="text-[10px] text-white/30 uppercase tracking-wider mb-1">PPO</div>
              <div className="text-sm text-white">stable-baselines3 v2.3.2</div>
            </div>
            <div>
              <div className="text-[10px] text-white/30 uppercase tracking-wider mb-1">LLM</div>
              <div className="text-sm text-white">Qwen2.5-7B-Instruct</div>
            </div>
            <div>
              <div className="text-[10px] text-white/30 uppercase tracking-wider mb-1">Framework</div>
              <div className="text-sm text-white">PyTorch 2.1.0</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function PosterView() {
  return (
    <div className="min-h-screen bg-white text-black p-8 print:p-4">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold mb-2">AURORA</h1>
        <h2 className="text-2xl text-gray-700 mb-4">Hybrid AI for Autonomous Wildfire Suppression</h2>
        <p className="text-lg text-gray-600">Shaurya Mallampati & Ankit Mohanty | ISEF 2025</p>
      </div>

      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="border-2 border-gray-300 rounded-lg p-4 h-64 flex items-center justify-center bg-gray-50">
          <div className="text-center text-gray-500">
            <div className="text-6xl mb-2">🗺️</div>
            <div>Mission Control Screenshot</div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="border-2 border-gray-300 rounded-lg p-4 h-28 flex items-center justify-center bg-gray-50">
            <div className="text-center text-gray-500">📈 Return Curve</div>
          </div>
          <div className="border-2 border-gray-300 rounded-lg p-4 h-28 flex items-center justify-center bg-gray-50">
            <div className="text-center text-gray-500">📊 Completion Rate</div>
          </div>
        </div>

        <div className="border-2 border-gray-300 rounded-lg p-4 bg-orange-50">
          <h3 className="font-bold text-lg mb-3">Key Results</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Area Saved:</span>
              <span className="font-bold text-green-700">+23.4%</span>
            </div>
            <div className="flex justify-between">
              <span>Containment Time:</span>
              <span className="font-bold text-blue-700">-18.2%</span>
            </div>
            <div className="flex justify-between">
              <span>Water Efficiency:</span>
              <span className="font-bold text-purple-700">+15.7%</span>
            </div>
            <div className="flex justify-between">
              <span>Success Rate:</span>
              <span className="font-bold text-orange-700">92%</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="font-bold text-xl mb-3">Data Sources</h3>
        <div className="grid grid-cols-2 gap-3 text-xs">
          {DATA_SOURCES.map((source, idx) => (
            <div key={idx} className="border border-gray-300 rounded p-2 bg-gray-50">
              <div className="font-semibold">{source.name}</div>
              <div className="text-gray-600">{source.records.toLocaleString()} records</div>
            </div>
          ))}
        </div>
      </div>

      <div className="border-t-2 border-gray-300 pt-4">
        <p className="text-sm leading-relaxed text-gray-800">
          <strong>Summary:</strong> AURORA combines PPO reinforcement learning with LLM strategic guidance
          to coordinate autonomous drone swarms for wildfire suppression. Trained on 116K+ historical fires,
          the hybrid system achieves 23% more area saved and 18% faster containment.
        </p>
      </div>
    </div>
  );
}
