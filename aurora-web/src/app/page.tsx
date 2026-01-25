"use client";

import Link from "next/link";
import { useState } from "react";
import { Play, Activity, Zap, TrendingUp, Globe, Shield, Award, Code2, Cpu, ExternalLink, Flame, ChevronRight, ArrowRight, CheckCircle2 } from "lucide-react";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState("overview");

  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "results", label: "Results" },
    { id: "architecture", label: "Architecture" },
    { id: "data", label: "Data" },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-[#0a0a0b] text-white">
      {/* Subtle gradient background with fire effects */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#0a0a0b] via-[#0d0d0f] to-[#0a0a0b]"></div>
        {/* Fire glow at top */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[700px] bg-gradient-radial from-orange-600/8 via-orange-500/3 to-transparent blur-[100px] rounded-full"></div>
        {/* Secondary glow */}
        <div className="absolute top-1/3 right-0 w-[500px] h-[500px] bg-orange-500/5 blur-[120px] rounded-full"></div>
        {/* Floating ember particles */}
        <div className="absolute bottom-0 left-0 right-0 h-full">
          <div className="ember"></div>
          <div className="ember"></div>
          <div className="ember"></div>
          <div className="ember"></div>
          <div className="ember"></div>
          <div className="ember"></div>
          <div className="ember"></div>
          <div className="ember"></div>
          <div className="ember"></div>
        </div>
      </div>

      {/* Header */}
      <header className="border-b border-white/5 bg-[#0a0a0b]/90 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg flex items-center justify-center">
              <Flame className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-semibold tracking-tight">AURORA</span>
          </Link>
          <nav className="hidden md:flex items-center gap-8">
            <Link href="/sim" className="text-[13px] text-white/60 hover:text-white transition-colors">Mission Control</Link>
            <Link href="/scenarios" className="text-[13px] text-white/60 hover:text-white transition-colors">Scenarios</Link>
            <Link href="/lab" className="text-[13px] text-white/60 hover:text-white transition-colors">Lab</Link>
            <Link href="/runs" className="text-[13px] text-white/60 hover:text-white transition-colors">History</Link>
          </nav>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-orange-500/10 border border-orange-500/20 rounded-full">
            <div className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse"></div>
            <span className="text-xs font-medium text-orange-400">ISEF 2025</span>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="border-b border-white/5 bg-[#0a0a0b]/80 backdrop-blur-sm sticky top-16 z-40">
        <div className="max-w-6xl mx-auto px-6 flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-[13px] font-medium transition-colors relative ${activeTab === tab.id
                ? 'text-white'
                : 'text-white/40 hover:text-white/70'
                }`}
            >
              {tab.label}
              {activeTab === tab.id && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-orange-500"></div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 relative z-10">
        {activeTab === "overview" && (
          <div>
            {/* Hero Section */}
            <section className="py-20 px-6">
              <div className="max-w-6xl mx-auto">
                <div className="grid lg:grid-cols-2 gap-16 items-center">
                  {/* Left: Text */}
                  <div className="space-y-8">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[11px] text-white/60 uppercase tracking-wider">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                      Research Project
                    </div>

                    <h1 className="text-4xl md:text-5xl lg:text-[56px] font-semibold leading-[1.1] tracking-tight">
                      Autonomous Wildfire Response with{" "}
                      <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-orange-500">
                        Hybrid AI
                      </span>
                    </h1>

                    <p className="text-lg text-white/50 leading-relaxed max-w-lg">
                      A novel approach combining PPO reinforcement learning with LLM strategic guidance for intelligent multi-drone wildfire suppression, trained on 116K+ real historical fire scenarios.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-3 pt-2">
                      <Link
                        href="/sim"
                        className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-orange-500 hover:bg-orange-600 text-white text-sm font-medium rounded-lg transition-colors"
                      >
                        <Play className="w-4 h-4" />
                        Launch Demo
                      </Link>
                      <Link
                        href="/scenarios"
                        className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white text-sm font-medium rounded-lg transition-colors"
                      >
                        View Scenarios
                        <ArrowRight className="w-4 h-4" />
                      </Link>
                    </div>
                  </div>

                  {/* Right: Drone Visualization */}
                  <div className="relative">
                    <div className="aspect-square max-w-lg mx-auto relative">
                      {/* Animated outer rings */}
                      <div className="absolute inset-0 rounded-full border border-white/[0.03] animate-[spin_60s_linear_infinite]"></div>
                      <div className="absolute inset-6 rounded-full border border-white/[0.05] animate-[spin_45s_linear_infinite_reverse]"></div>
                      <div className="absolute inset-12 rounded-full border border-orange-500/10 animate-[spin_30s_linear_infinite]"></div>
                      <div className="absolute inset-16 rounded-full border border-white/[0.08]"></div>

                      {/* Decorative radial lines */}
                      <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 400">
                        <defs>
                          <radialGradient id="fadeGradient" cx="50%" cy="50%" r="50%">
                            <stop offset="0%" stopColor="white" stopOpacity="0" />
                            <stop offset="70%" stopColor="white" stopOpacity="0.03" />
                            <stop offset="100%" stopColor="white" stopOpacity="0" />
                          </radialGradient>
                        </defs>
                        {/* Cross lines */}
                        <line x1="200" y1="0" x2="200" y2="400" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
                        <line x1="0" y1="200" x2="400" y2="200" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
                        <line x1="60" y1="60" x2="340" y2="340" stroke="rgba(255,255,255,0.02)" strokeWidth="1" />
                        <line x1="340" y1="60" x2="60" y2="340" stroke="rgba(255,255,255,0.02)" strokeWidth="1" />

                        {/* Corner data points */}
                        <circle cx="85" cy="85" r="3" fill="rgba(234,88,12,0.4)" />
                        <circle cx="315" cy="85" r="3" fill="rgba(234,88,12,0.4)" />
                        <circle cx="85" cy="315" r="3" fill="rgba(234,88,12,0.4)" />
                        <circle cx="315" cy="315" r="3" fill="rgba(234,88,12,0.4)" />
                      </svg>

                      {/* Center drone visualization */}
                      <div className="absolute inset-0 flex items-center justify-center">
                        <svg width="280" height="280" viewBox="0 0 280 280" className="drop-shadow-lg">
                          <defs>
                            <linearGradient id="bodyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                              <stop offset="0%" stopColor="#2a2a2a" />
                              <stop offset="100%" stopColor="#1a1a1a" />
                            </linearGradient>
                            <linearGradient id="glowGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                              <stop offset="0%" stopColor="#ea580c" stopOpacity="0.8" />
                              <stop offset="100%" stopColor="#f97316" stopOpacity="0.4" />
                            </linearGradient>
                            <filter id="glow">
                              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                              <feMerge>
                                <feMergeNode in="coloredBlur" />
                                <feMergeNode in="SourceGraphic" />
                              </feMerge>
                            </filter>
                          </defs>

                          {/* Main body - sleek hexagonal shape */}
                          <polygon points="140,90 170,110 170,150 140,170 110,150 110,110" fill="url(#bodyGrad)" stroke="#333" strokeWidth="1" />

                          {/* Central core/camera */}
                          <circle cx="140" cy="130" r="20" fill="#111" stroke="#333" strokeWidth="1" />
                          <circle cx="140" cy="130" r="12" fill="#1a1a1a" />
                          <circle cx="140" cy="130" r="6" fill="url(#glowGrad)" filter="url(#glow)" />

                          {/* Arms - diagonal sleek design */}
                          <line x1="115" y1="115" x2="55" y2="55" stroke="#2a2a2a" strokeWidth="6" strokeLinecap="round" />
                          <line x1="165" y1="115" x2="225" y2="55" stroke="#2a2a2a" strokeWidth="6" strokeLinecap="round" />
                          <line x1="115" y1="145" x2="55" y2="205" stroke="#2a2a2a" strokeWidth="6" strokeLinecap="round" />
                          <line x1="165" y1="145" x2="225" y2="205" stroke="#2a2a2a" strokeWidth="6" strokeLinecap="round" />

                          {/* Motors - minimalist rings */}
                          <circle cx="55" cy="55" r="16" fill="#1a1a1a" stroke="#333" strokeWidth="1" />
                          <circle cx="225" cy="55" r="16" fill="#1a1a1a" stroke="#333" strokeWidth="1" />
                          <circle cx="55" cy="205" r="16" fill="#1a1a1a" stroke="#333" strokeWidth="1" />
                          <circle cx="225" cy="205" r="16" fill="#1a1a1a" stroke="#333" strokeWidth="1" />

                          {/* Motor inner cores */}
                          <circle cx="55" cy="55" r="8" fill="#111" />
                          <circle cx="225" cy="55" r="8" fill="#111" />
                          <circle cx="55" cy="205" r="8" fill="#111" />
                          <circle cx="225" cy="205" r="8" fill="#111" />

                          {/* Propeller rings - subtle animated effect */}
                          <circle cx="55" cy="55" r="32" fill="none" stroke="rgba(234,88,12,0.15)" strokeWidth="2" strokeDasharray="8 4" className="animate-[spin_3s_linear_infinite]" style={{ transformOrigin: '55px 55px' }} />
                          <circle cx="225" cy="55" r="32" fill="none" stroke="rgba(234,88,12,0.15)" strokeWidth="2" strokeDasharray="8 4" className="animate-[spin_3s_linear_infinite_reverse]" style={{ transformOrigin: '225px 55px' }} />
                          <circle cx="55" cy="205" r="32" fill="none" stroke="rgba(234,88,12,0.15)" strokeWidth="2" strokeDasharray="8 4" className="animate-[spin_3s_linear_infinite_reverse]" style={{ transformOrigin: '55px 205px' }} />
                          <circle cx="225" cy="205" r="32" fill="none" stroke="rgba(234,88,12,0.15)" strokeWidth="2" strokeDasharray="8 4" className="animate-[spin_3s_linear_infinite]" style={{ transformOrigin: '225px 205px' }} />

                          {/* Data connection lines */}
                          <line x1="140" y1="130" x2="55" y2="55" stroke="rgba(234,88,12,0.2)" strokeWidth="1" strokeDasharray="4 6" />
                          <line x1="140" y1="130" x2="225" y2="55" stroke="rgba(234,88,12,0.2)" strokeWidth="1" strokeDasharray="4 6" />
                          <line x1="140" y1="130" x2="55" y2="205" stroke="rgba(234,88,12,0.2)" strokeWidth="1" strokeDasharray="4 6" />
                          <line x1="140" y1="130" x2="225" y2="205" stroke="rgba(234,88,12,0.2)" strokeWidth="1" strokeDasharray="4 6" />

                          {/* Status indicators */}
                          <circle cx="128" cy="155" r="3" fill="#22c55e" />
                          <circle cx="140" cy="155" r="3" fill="#ea580c" />
                          <circle cx="152" cy="155" r="3" fill="#3b82f6" />
                        </svg>
                      </div>

                      {/* Floating tech labels */}
                      <div className="absolute top-12 right-4 flex flex-col gap-2 items-end">
                        <div className="px-2.5 py-1 bg-[#111]/90 backdrop-blur-sm border border-white/10 rounded text-[10px] text-white/60 font-mono flex items-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-blue-400"></div>
                          PPO-v2
                        </div>
                        <div className="px-2.5 py-1 bg-[#111]/90 backdrop-blur-sm border border-white/10 rounded text-[10px] text-white/60 font-mono flex items-center gap-2">
                          <div className="w-1.5 h-1.5 rounded-full bg-purple-400"></div>
                          Qwen2.5
                        </div>
                      </div>

                      <div className="absolute bottom-12 left-4 flex flex-col gap-2">
                        <div className="px-2.5 py-1 bg-orange-500/20 border border-orange-500/30 rounded text-[10px] text-orange-400 font-mono">
                          Real-time Control
                        </div>
                        <div className="px-2.5 py-1 bg-[#111]/90 backdrop-blur-sm border border-white/10 rounded text-[10px] text-white/60 font-mono">
                          116K+ Scenarios
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Stats Bar */}
            <section className="border-y border-white/5 bg-white/[0.02]">
              <div className="max-w-6xl mx-auto px-6 py-8">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                  {[
                    { value: "+21%", label: "Return Improvement", sublabel: "Qwen 3B hybrid" },
                    { value: "53K", label: "Training Episodes", sublabel: "across 4 seeds" },
                    { value: "+50%", label: "Hard Scenario Gain", sublabel: "where PPO struggles" },
                    { value: "116K", label: "Real Fire Scenarios", sublabel: "historical data" }
                  ].map((stat, i) => (
                    <div key={i} className="text-center md:text-left">
                      <div className="text-2xl md:text-3xl font-semibold text-white tracking-tight">{stat.value}</div>
                      <div className="text-sm text-white/70 mt-0.5">{stat.label}</div>
                      <div className="text-xs text-white/40">{stat.sublabel}</div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* Key Features */}
            <section className="py-20 px-6">
              <div className="max-w-6xl mx-auto">
                <div className="text-center mb-12">
                  <h2 className="text-2xl md:text-3xl font-semibold tracking-tight">Research Contributions</h2>
                  <p className="text-white/50 mt-2">Novel approaches to autonomous wildfire response</p>
                </div>

                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {[
                    {
                      icon: Zap,
                      title: "Hybrid AI Architecture",
                      description: "PPO for reactive control, LLM for strategic reasoning"
                    },
                    {
                      icon: Globe,
                      title: "Real-World Data",
                      description: "Trained on 116K+ historical fires with weather & terrain"
                    },
                    {
                      icon: Code2,
                      title: "Explainable Decisions",
                      description: "Transparent reasoning for every drone action"
                    },
                    {
                      icon: Shield,
                      title: "Reproducible Results",
                      description: "Frozen test set with cryptographic verification"
                    }
                  ].map((feature, i) => (
                    <div
                      key={i}
                      className="group p-5 rounded-xl bg-white/[0.02] border border-white/5 hover:border-white/10 hover:bg-white/[0.04] transition-all"
                    >
                      <feature.icon className="w-5 h-5 text-orange-500 mb-3" />
                      <h3 className="text-sm font-medium text-white mb-1">{feature.title}</h3>
                      <p className="text-[13px] text-white/50 leading-relaxed">{feature.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* CTA Section */}
            <section className="py-12 px-6 border-t border-white/5">
              <div className="max-w-6xl mx-auto">
                <div className="flex flex-col md:flex-row items-center justify-between gap-6 p-6 rounded-xl bg-gradient-to-r from-orange-500/10 to-transparent border border-orange-500/10">
                  <div>
                    <h3 className="text-lg font-medium">Ready to explore?</h3>
                    <p className="text-sm text-white/50 mt-1">Launch the interactive demo to see AURORA in action</p>
                  </div>
                  <Link
                    href="/sim"
                    className="inline-flex items-center gap-2 px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white text-sm font-medium rounded-lg transition-colors shrink-0"
                  >
                    Launch Mission Control
                    <ChevronRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            </section>
          </div>
        )}

        {activeTab === "results" && (
          <section className="py-16 px-6">
            <div className="max-w-6xl mx-auto space-y-12">
              <div className="max-w-2xl">
                <h2 className="text-3xl font-semibold tracking-tight">Performance Results</h2>
                <p className="text-white/50 mt-2">Real metrics from 53,055 training episodes across 3 models and 4 random seeds.</p>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                {[
                  {
                    icon: TrendingUp,
                    value: "+21.0%",
                    label: "Episode Return Improvement",
                    description: "Hybrid model achieves 41.84 vs 34.57 baseline return, trained on 116,337 historical fires"
                  },
                  {
                    icon: Zap,
                    value: "+49.9%",
                    label: "Hard Scenario Improvement",
                    description: "LLM guidance shows strongest gains on difficult fire configurations where PPO alone struggles"
                  },
                  {
                    icon: Shield,
                    value: "53,055",
                    label: "Training Episodes",
                    description: "Validated across 4 random seeds with PPO baseline, Qwen 3B, and Qwen 7B hybrid models"
                  },
                  {
                    icon: Award,
                    value: "116K",
                    label: "Historical Fires",
                    description: "Trained exclusively on real InterAgency Fire Perimeter data from 1308-2024"
                  }
                ].map((result, i) => (
                  <div key={i} className="p-6 rounded-xl bg-white/[0.02] border border-white/5">
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center shrink-0">
                        <result.icon className="w-5 h-5 text-orange-500" />
                      </div>
                      <div>
                        <div className="text-2xl font-semibold text-white">{result.value}</div>
                        <div className="text-sm text-white/70">{result.label}</div>
                        <p className="text-[13px] text-white/40 mt-2 leading-relaxed">{result.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {activeTab === "architecture" && (
          <section className="py-16 px-6">
            <div className="max-w-6xl mx-auto space-y-12">
              <div className="max-w-2xl">
                <h2 className="text-3xl font-semibold tracking-tight">System Architecture</h2>
                <p className="text-white/50 mt-2">Dual-agent hybrid system combining reactive learning with strategic reasoning.</p>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                <div className="p-6 rounded-xl bg-white/[0.02] border border-white/5">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                      <Cpu className="w-5 h-5 text-blue-400" />
                    </div>
                    <h3 className="text-lg font-medium">PPO Agent</h3>
                  </div>
                  <ul className="space-y-2">
                    {[
                      "Low-level motor control & tactics",
                      "2,048 step rollout buffers",
                      "Real-time decision making",
                      "Trained on 116K+ scenarios"
                    ].map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-[13px] text-white/60">
                        <CheckCircle2 className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="p-6 rounded-xl bg-white/[0.02] border border-white/5">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
                      <Code2 className="w-5 h-5 text-purple-400" />
                    </div>
                    <h3 className="text-lg font-medium">LLM Strategy (Qwen2.5)</h3>
                  </div>
                  <ul className="space-y-2">
                    {[
                      "High-level strategic guidance",
                      "Called every 50 steps",
                      "Analyzes global fire state",
                      "Generates interpretable advice"
                    ].map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-[13px] text-white/60">
                        <CheckCircle2 className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="p-6 rounded-xl bg-white/[0.02] border border-white/5">
                <h3 className="text-lg font-medium mb-4">Evaluation Protocol</h3>
                <p className="text-[13px] text-white/50 mb-4">LLM guidance encoded into PPO observation space as priority channels. Results in 21% improvement with +50% gains on hard scenarios.</p>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-white/[0.02]">
                    <div className="text-sm font-medium text-orange-400 mb-1">53,055 Episodes</div>
                    <p className="text-xs text-white/40">3 models × 4 seeds: PPO baseline, Qwen 3B hybrid, Qwen 7B hybrid</p>
                  </div>
                  <div className="p-4 rounded-lg bg-white/[0.02]">
                    <div className="text-sm font-medium text-orange-400 mb-1">Real Historical Data</div>
                    <p className="text-xs text-white/40">116,337 fires from InterAgency + NOAA weather + USGS terrain</p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {activeTab === "data" && (
          <section className="py-16 px-6">
            <div className="max-w-6xl mx-auto space-y-12">
              <div className="max-w-2xl">
                <h2 className="text-3xl font-semibold tracking-tight">Data Provenance</h2>
                <p className="text-white/50 mt-2">All data sources are publicly available with cryptographic verification for reproducibility.</p>
              </div>

              {/* Real Firefighting Cost Statistics */}
              <div className="p-6 rounded-xl bg-gradient-to-br from-red-500/10 to-orange-500/5 border border-orange-500/20">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Flame className="w-5 h-5 text-orange-500" />
                  Federal Firefighting Costs (NIFC 2023)
                </h3>
                <div className="grid md:grid-cols-4 gap-4 mb-4">
                  <div className="p-4 rounded-lg bg-black/20">
                    <div className="text-2xl font-bold text-orange-400">$3.17B</div>
                    <div className="text-xs text-white/50">Total Federal Suppression (2023)</div>
                  </div>
                  <div className="p-4 rounded-lg bg-black/20">
                    <div className="text-2xl font-bold text-orange-400">$2.99B</div>
                    <div className="text-xs text-white/50">5-Year Average (2019-2023)</div>
                  </div>
                  <div className="p-4 rounded-lg bg-black/20">
                    <div className="text-2xl font-bold text-orange-400">~$1,175</div>
                    <div className="text-xs text-white/50">Avg Cost per Acre (2023)</div>
                  </div>
                  <div className="p-4 rounded-lg bg-black/20">
                    <div className="text-2xl font-bold text-orange-400">2.69M</div>
                    <div className="text-xs text-white/50">Acres Burned (2023)</div>
                  </div>
                </div>
                <p className="text-xs text-white/40">
                  Source: National Interagency Fire Center (NIFC) Federal Firefighting Costs Statistics. 
                  The Camp Fire (2018) alone cost $10B in damages. Early detection and rapid response can reduce costs by 60-80%.
                </p>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                {[
                  {
                    value: "116,337",
                    title: "Fire Perimeters",
                    description: "InterAgency Fire Perimeter History (1308-2024) with SHA-256 checksums"
                  },
                  {
                    value: "2,847",
                    title: "Weather Records",
                    description: "NOAA historical data: temperature, humidity, wind speed, precipitation"
                  },
                  {
                    value: "1M+",
                    title: "Terrain Points",
                    description: "USGS 3DEP elevation data (30m resolution) for slope and terrain analysis"
                  }
                ].map((data, i) => (
                  <div key={i} className="p-6 rounded-xl bg-white/[0.02] border border-white/5">
                    <div className="text-3xl font-semibold text-white mb-1">{data.value}</div>
                    <div className="text-sm font-medium text-white/70 mb-2">{data.title}</div>
                    <p className="text-[13px] text-white/40 leading-relaxed">{data.description}</p>
                  </div>
                ))}
              </div>

              {/* Additional cost context */}
              <div className="p-6 rounded-xl bg-white/[0.02] border border-white/5">
                <h3 className="text-lg font-medium mb-4">Traditional Firefighting Resources</h3>
                <div className="grid md:grid-cols-2 gap-6 text-sm text-white/60">
                  <div>
                    <h4 className="text-white font-medium mb-2">Response Times & Resources</h4>
                    <ul className="space-y-1 text-[13px]">
                      <li>• Average response time: 5-8 minutes (structure fires)</li>
                      <li>• Wildfire initial attack: 10-30 minutes (varies by terrain)</li>
                      <li>• Single fire hose flow rate: 150-250 gallons/minute</li>
                      <li>• Average house fire requires: ~3,000 gallons to extinguish</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-white font-medium mb-2">Top 10 Costliest Wildfires (Insurance Claims)</h4>
                    <ul className="space-y-1 text-[13px]">
                      <li>• Camp Fire (2018): $12.5B adjusted</li>
                      <li>• Tubbs Fire (2017): $11.1B adjusted</li>
                      <li>• Woolsey Fire (2018): $5.3B adjusted</li>
                      <li>• Maui Wildfire (2023): $4.4B</li>
                    </ul>
                  </div>
                </div>
                <p className="text-xs text-white/40 mt-4">
                  Sources: NIFC Suppression Costs, Insurance Information Institute (iii.org), NOAA NCEI
                </p>
              </div>
            </div>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 px-6 mt-auto">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-gradient-to-br from-orange-500 to-orange-600 rounded flex items-center justify-center">
              <Flame className="w-3 h-3 text-white" />
            </div>
            <span className="text-sm font-medium">AURORA</span>
            <span className="text-xs text-white/30 ml-2">Autonomous Unified Response Orchestration</span>
          </div>
          <div className="text-xs text-white/40">
            Shaurya Mallampati & Ankit Mohanty · ISEF 2025
          </div>
        </div>
      </footer>
    </div>
  );
}
