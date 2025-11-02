"use client";

import Link from "next/link";
import { useState } from "react";
import { Play, Activity, Zap, TrendingUp, Globe, Shield, Award, Code2, Cpu, ExternalLink, Flame } from "lucide-react";
import { DroneHeroScene } from "@/components/ui/drone-hero";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState("overview");

  const tabs = [
    { id: "overview", label: "🚀 Overview", icon: Activity },
    { id: "results", label: "📊 Results", icon: TrendingUp },
    { id: "architecture", label: "🧠 Architecture", icon: Code2 },
    { id: "data", label: "🌍 Data", icon: Globe },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-900 via-slate-800 to-black text-white">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between h-20">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl flex items-center justify-center">
              <Flame className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">AURORA</h1>
              <p className="text-xs text-orange-400">Hybrid AI Wildfire Response</p>
            </div>
          </Link>
          <nav className="hidden md:flex items-center gap-6">
            <Link href="/sim" className="text-sm text-gray-300 hover:text-orange-400 transition">Mission Control</Link>
            <Link href="/scenarios" className="text-sm text-gray-300 hover:text-orange-400 transition">Scenarios</Link>
            <Link href="/lab" className="text-sm text-gray-300 hover:text-orange-400 transition">Lab</Link>
            <Link href="/runs" className="text-sm text-gray-300 hover:text-orange-400 transition">History</Link>
            <Link href="/sources" className="text-sm text-gray-300 hover:text-orange-400 transition">Data</Link>
          </nav>
          <div className="px-3 py-1.5 bg-yellow-600/20 border border-yellow-600/50 rounded-lg">
            <span className="text-xs font-bold text-yellow-400">ISEF 2025</span>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
            {/* Tab Navigation */}
      <div className="border-b border-slate-700/50 bg-slate-900/50 sticky top-[73px] z-30">
        <div className="max-w-7xl mx-auto px-4 flex overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-4 border-b-2 transition whitespace-nowrap ${ activeTab === tab.id
                ? 'border-orange-500 text-orange-400'
                : 'border-transparent text-gray-400 hover:text-orange-400'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 px-4 py-12">
        <div className="max-w-7xl mx-auto">
          {activeTab === "overview" && (
            <div className="space-y-12">
              {/* Hero */}
              <div className="text-center space-y-6">
                <h2 className="text-5xl md:text-7xl font-bold text-white leading-tight">
                  Autonomous Wildfire<br />
                  <span className="bg-gradient-to-r from-orange-400 to-red-500 text-transparent bg-clip-text">
                    Response with Hybrid AI
                  </span>
                </h2>
                <p className="text-lg text-gray-300 max-w-3xl mx-auto">
                  Combines <span className="text-blue-400 font-semibold">PPO Reinforcement Learning</span> with <span className="text-purple-400 font-semibold">LLM Strategic Guidance</span> for intelligent drone coordination on <span className="text-green-400 font-semibold">116K+ real historical fires</span>
                </p>
              </div>

              {/* Interactive 3D Drone Scene */}
              <DroneHeroScene />

              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { value: "23%", label: "More Area Saved", color: "orange" },
                  { value: "18%", label: "Faster Containment", color: "blue" },
                  { value: "92%", label: "Success Rate", color: "purple" },
                  { value: "116K+", label: "Fire Scenarios", color: "green" }
                ].map((stat, index) => (
                  <div key={index} className="bg-slate-800 border border-slate-700 rounded-lg p-6 text-center hover:border-slate-600 transition">
                    <div className={`text-3xl md:text-4xl font-bold text-${stat.color}-400 mb-2`}>{stat.value}</div>
                    <div className="text-sm text-gray-400">{stat.label}</div>
                  </div>
                ))}
              </div>

              {/* Feature Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-blue-600/50 transition">
                  <Zap className="w-8 h-8 text-blue-400 mb-3" />
                  <h3 className="font-semibold text-white mb-2">Hybrid AI</h3>
                  <p className="text-sm text-gray-400">PPO handles reactive control while LLM provides strategic guidance</p>
                </div>

                <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-green-600/50 transition">
                  <Globe className="w-8 h-8 text-green-400 mb-3" />
                  <h3 className="font-semibold text-white mb-2">Real Data</h3>
                  <p className="text-sm text-gray-400">116K+ historical fires + NOAA weather + USGS elevation</p>
                </div>

                <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-purple-600/50 transition">
                  <Activity className="w-8 h-8 text-purple-400 mb-3" />
                  <h3 className="font-semibold text-white mb-2">Explainable</h3>
                  <p className="text-sm text-gray-400">Click drones for reasoning, see feature attributions, read LLM strategy</p>
                </div>

                <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-yellow-600/50 transition">
                  <TrendingUp className="w-8 h-8 text-yellow-400 mb-3" />
                  <h3 className="font-semibold text-white mb-2">Reproducible</h3>
                  <p className="text-sm text-gray-400">Frozen test set, checksummed sources, seed tracking</p>
                </div>
              </div>

              {/* CTA */}
              <div className="flex flex-col md:flex-row gap-4 justify-center pt-8">
                <Link href="/sim" className="px-8 py-3 bg-gradient-to-r from-orange-500 to-red-600 text-white rounded-lg font-semibold hover:shadow-lg hover:shadow-orange-500/50 transition flex items-center justify-center gap-2">
                  <Play className="w-5 h-5" />
                  Launch Mission Control
                </Link>
                <Link href="/scenarios" className="px-8 py-3 bg-slate-700 text-white rounded-lg font-semibold hover:bg-slate-600 transition">
                  Explore Scenarios
                </Link>
              </div>
            </div>
          )}

          {activeTab === "results" && (
            <div className="space-y-8">
              <h2 className="text-4xl font-bold text-white">Performance Gains</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[
                  { 
                    icon: TrendingUp, 
                    value: "+23.4%", 
                    label: "More Area Saved", 
                    color: "green",
                    description: "Strategically prioritizes high-risk zones, saving significantly more terrain from fire damage"
                  },
                  { 
                    icon: Zap, 
                    value: "-18.2%", 
                    label: "Faster Containment", 
                    color: "blue",
                    description: "Reduces time to full fire containment, preventing spread to populated areas"
                  },
                  { 
                    icon: Shield, 
                    value: "+15.7%", 
                    label: "Water Efficiency", 
                    color: "purple",
                    description: "Optimizes suppression resources, achieving superior containment with less water"
                  },
                  { 
                    icon: Award, 
                    value: "92%", 
                    label: "Success Rate", 
                    color: "yellow",
                    description: "Achieves successful containment in 92% of diverse scenarios"
                  }
                ].map((result, index) => {
                  const Icon = result.icon;
                  return (
                    <div key={index} className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition">
                      <div className="flex items-center gap-4 mb-4">
                        <Icon className={`w-8 h-8 text-${result.color}-400`} />
                        <div>
                          <div className={`text-3xl font-bold text-${result.color}-400`}>{result.value}</div>
                          <div className="text-sm text-gray-300">{result.label}</div>
                        </div>
                      </div>
                      <p className="text-gray-400 text-sm">{result.description}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {activeTab === "architecture" && (
            <div className="space-y-8">
              <h2 className="text-4xl font-bold text-white">System Architecture</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[
                  {
                    icon: Cpu,
                    title: "PPO Agent",
                    color: "blue",
                    features: [
                      "Low-level motor control & tactics",
                      "2,048 step rollout buffers",
                      "Real-time decision making",
                      "Trained on 116K+ scenarios"
                    ]
                  },
                  {
                    icon: Code2,
                    title: "LLM Strategy (Qwen2.5)",
                    color: "purple",
                    features: [
                      "High-level strategic guidance",
                      "Called every 50 steps",
                      "Analyzes global fire state",
                      "Generates interpretable advice"
                    ]
                  }
                ].map((agent, index) => {
                  const Icon = agent.icon;
                  return (
                    <div key={index} className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition">
                      <div className="flex items-center gap-3 mb-4">
                        <Icon className={`w-8 h-8 text-${agent.color}-400`} />
                        <h3 className={`text-xl font-semibold text-${agent.color}-400`}>{agent.title}</h3>
                      </div>
                      <ul className="space-y-2">
                        {agent.features.map((feature, i) => (
                          <li key={i} className="text-sm text-gray-400 flex gap-2">
                            <span className="text-slate-500">•</span> {feature}
                          </li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
              </div>

              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-orange-400 mb-3">Integration & Evaluation</h3>
                <p className="text-gray-300 text-sm mb-4">LLM guidance is encoded into PPO observation space as priority channels. Results in 23% improvement with full explainability.</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-slate-700 rounded p-3">
                    <div className="font-semibold text-cyan-400 text-sm mb-1">5 Test Fires</div>
                    <p className="text-xs text-gray-400">Camp Fire CA, Riverside OR, East Troublesome CO, Okanogan WA, Lolo Peak MT</p>
                  </div>
                  <div className="bg-slate-700 rounded p-3">
                    <div className="font-semibold text-green-400 text-sm mb-1">25 Evaluation Episodes</div>
                    <p className="text-xs text-gray-400">5 fires × 5 random seeds for reproducible test set</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "data" && (
            <div className="space-y-8">
              <h2 className="text-4xl font-bold text-white">Data Provenance</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                  {
                    value: "116,337",
                    title: "Fire Perimeters",
                    description: "InterAgency Fire Perimeter History (1878-2024) with cryptographic checksums",
                    color: "orange"
                  },
                  {
                    value: "2,847",
                    title: "Weather Records",
                    description: "NOAA historical data: temperature, humidity, wind speed, precipitation",
                    color: "green"
                  },
                  {
                    value: "1M+",
                    title: "Terrain Points",
                    description: "USGS 3DEP elevation data (30m resolution) for slope and terrain analysis",
                    color: "blue"
                  }
                ].map((data, index) => (
                  <div key={index} className="bg-slate-800 border border-slate-700 rounded-lg p-6 hover:border-slate-600 transition">
                    <div className={`text-3xl font-bold text-${data.color}-400 mb-2`}>{data.value}</div>
                    <h3 className="font-semibold text-white mb-2">{data.title}</h3>
                    <p className="text-sm text-gray-400">{data.description}</p>
                  </div>
                ))}
              </div>

              <Link href="/sources" className="block bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg p-6 text-center font-semibold hover:from-blue-700 hover:to-purple-700 transition">
                View All Data Sources with SHA-256 Checksums
                <ExternalLink className="w-4 h-4 inline ml-2" />
              </Link>
            </div>
          )}
        </div>
      </main>

      {/* Quick Links */}
      <section className="border-t border-slate-700 bg-slate-800/50 py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <p className="text-center text-sm text-gray-400 mb-8 font-semibold">FOR JUDGES & EVALUATORS</p>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {[
              { href: "/scenarios", emoji: "📍", title: "Scenarios", desc: "Real fires" },
              { href: "/lab", emoji: "⚗️", title: "Lab", desc: "Run tests" },
              { href: "/runs", emoji: "📊", title: "History", desc: "Audit trail" },
              { href: "/sources", emoji: "🔐", title: "Data", desc: "Checksums" },
              { href: "/sim", emoji: "🚀", title: "Control", desc: "Live sim", special: true }
            ].map((item, index) => (
              <Link 
                key={index}
                href={item.href} 
                className={`p-4 rounded-lg text-center transition hover:scale-105 ${item.special ? 'bg-orange-600/20 border border-orange-500/50 hover:border-orange-400' : 'bg-slate-700 border border-slate-600 hover:border-slate-500'}`}
              >
                <div className="text-2xl mb-2">{item.emoji}</div>
                <div className="font-semibold text-sm text-white">{item.title}</div>
                <div className="text-xs text-gray-400">{item.desc}</div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-700/50 py-8 px-4 bg-slate-900/50 relative z-20">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-sm text-gray-400 mb-2">
            <span className="font-bold text-orange-400">AURORA</span> - Autonomous Unified Response Orchestration for Real-world Actions
          </p>
          <p className="text-xs text-gray-500">
            Shaurya Mallampati & Ankit Mohanty | ISEF 2025 | Built with Next.js, PyTorch, Qwen2.5
          </p>
        </div>
      </footer>
    </div>
  );
}
