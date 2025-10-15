"use client";

import Link from "next/link";
import { Play, Activity, FileText, Info } from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-600 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">AURORA</h1>
              <p className="text-xs text-gray-400">AI Wildfire Response System</p>
            </div>
          </div>
          <nav className="flex items-center gap-6">
            <Link href="/sim" className="text-sm text-gray-300 hover:text-white transition">
              Simulation
            </Link>
            <Link href="/runs" className="text-sm text-gray-300 hover:text-white transition">
              Runs
            </Link>
            <Link href="/about" className="text-sm text-gray-300 hover:text-white transition">
              About
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1 flex items-center justify-center px-4">
        <div className="max-w-4xl text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-orange-500/10 border border-orange-500/20 rounded-full text-orange-400 text-sm mb-8">
            <Activity className="w-4 h-4" />
            <span>ISEF 2025 Competition</span>
          </div>

          <h2 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
            Real-Time Wildfire Response
            <br />
            <span className="bg-gradient-to-r from-orange-400 to-red-500 text-transparent bg-clip-text">
              with Hybrid AI
            </span>
          </h2>

          <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto">
            Combining Proximal Policy Optimization with Large Language Model strategic guidance
            for intelligent multi-agent drone coordination in wildfire suppression scenarios.
          </p>

          <div className="flex items-center justify-center gap-4">
            <Link
              href="/sim"
              className="px-8 py-4 bg-gradient-to-r from-orange-500 to-red-600 text-white rounded-lg font-semibold flex items-center gap-2 hover:shadow-lg hover:shadow-orange-500/50 transition transform hover:scale-105"
            >
              <Play className="w-5 h-5" />
              Start Simulation
            </Link>
            <Link
              href="/about"
              className="px-8 py-4 bg-gray-800 text-white rounded-lg font-semibold flex items-center gap-2 hover:bg-gray-700 transition"
            >
              <Info className="w-5 h-5" />
              Learn More
            </Link>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20">
            <div className="p-6 bg-gray-900/50 border border-gray-800 rounded-xl">
              <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center mb-4">
                <Activity className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Hybrid AI Architecture</h3>
              <p className="text-sm text-gray-400">
                PPO for low-level control, LLM for high-level strategy. Best of both worlds.
              </p>
            </div>

            <div className="p-6 bg-gray-900/50 border border-gray-800 rounded-xl">
              <div className="w-12 h-12 bg-green-500/10 rounded-lg flex items-center justify-center mb-4">
                <FileText className="w-6 h-6 text-green-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Real Fire Data</h3>
              <p className="text-sm text-gray-400">
                Trained on 116,337 historical fire perimeters with NOAA weather integration.
              </p>
            </div>

            <div className="p-6 bg-gray-900/50 border border-gray-800 rounded-xl">
              <div className="w-12 h-12 bg-purple-500/10 rounded-lg flex items-center justify-center mb-4">
                <Play className="w-6 h-6 text-purple-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Live Visualization</h3>
              <p className="text-sm text-gray-400">
                Real-time fire spread, drone coordination, and strategic guidance overlay.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-6">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-500">
          <p>AURORA - Shaurya Mallampati - ISEF 2025</p>
        </div>
      </footer>
    </div>
  );
}
