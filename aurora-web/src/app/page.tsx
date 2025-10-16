"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { Play, Activity, Zap, TrendingUp, Globe, Shield, Award, Code2, Cpu, Github, ExternalLink, Flame, Wind, Droplets, MapPin } from "lucide-react";

export default function HomePage() {
  const [activeTab, setActiveTab] = useState("overview");
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({ x: e.clientX, y: e.clientY });
    };
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("scroll", handleScroll);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  const tabs = [
    { id: "overview", label: "🚀 Overview", icon: Activity },
    { id: "results", label: "📊 Results", icon: TrendingUp },
    { id: "architecture", label: "🧠 Architecture", icon: Code2 },
    { id: "data", label: "🌍 Data", icon: Globe },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-gray-950 via-gray-900 to-black text-white relative overflow-hidden">
      {/* Animated background particles */}
      <div className="fixed inset-0 pointer-events-none">
        <div 
          className="absolute w-96 h-96 bg-orange-500/10 rounded-full blur-3xl animate-pulse"
          style={{
            left: `${mousePosition.x / 10}px`,
            top: `${mousePosition.y / 10}px`,
            transition: "all 0.3s ease-out"
          }}
        />
        <div 
          className="absolute w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse"
          style={{
            right: `${mousePosition.x / 20}px`,
            bottom: `${mousePosition.y / 20}px`,
            transition: "all 0.5s ease-out"
          }}
        />
      </div>
      {/* Header with glassmorphism */}
      <header className="border-b border-gray-800/30 bg-gray-950/60 backdrop-blur-xl sticky top-0 z-50 shadow-2xl">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-12 h-12 bg-gradient-to-br from-orange-500 via-red-500 to-pink-600 rounded-2xl flex items-center justify-center shadow-lg shadow-orange-500/50 group-hover:shadow-orange-500/80 transition-all duration-300 group-hover:scale-110">
              <Flame className="w-7 h-7 text-white animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl font-black bg-gradient-to-r from-orange-400 via-red-500 to-pink-500 text-transparent bg-clip-text group-hover:from-orange-300 group-hover:via-red-400 group-hover:to-pink-400 transition-all">AURORA</h1>
              <p className="text-xs text-orange-400/80 font-semibold">Hybrid AI Wildfire Response</p>
            </div>
          </Link>
          <nav className="hidden md:flex items-center gap-8">
            <Link href="/sim" className="text-sm text-gray-300 hover:text-orange-400 font-semibold transition-all duration-300 hover:scale-110 relative group">
              Mission Control
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-orange-400 group-hover:w-full transition-all duration-300" />
            </Link>
            <Link href="/scenarios" className="text-sm text-gray-300 hover:text-orange-400 font-semibold transition-all duration-300 hover:scale-110 relative group">
              Scenarios
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-orange-400 group-hover:w-full transition-all duration-300" />
            </Link>
            <Link href="/lab" className="text-sm text-gray-300 hover:text-orange-400 font-semibold transition-all duration-300 hover:scale-110 relative group">
              Lab
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-orange-400 group-hover:w-full transition-all duration-300" />
            </Link>
            <Link href="/runs" className="text-sm text-gray-300 hover:text-orange-400 font-semibold transition-all duration-300 hover:scale-110 relative group">
              Run History
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-orange-400 group-hover:w-full transition-all duration-300" />
            </Link>
            <Link href="/sources" className="text-sm text-gray-300 hover:text-orange-400 font-semibold transition-all duration-300 hover:scale-110 relative group">
              Data Sources
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-orange-400 group-hover:w-full transition-all duration-300" />
            </Link>
          </nav>
          <div className="flex items-center gap-2 px-4 py-2 bg-yellow-500/10 border border-yellow-500/30 rounded-xl hover:bg-yellow-500/20 transition-all duration-300 hover:scale-105">
            <Award className="w-5 h-5 text-yellow-500" />
            <span className="text-sm font-bold text-yellow-500">ISEF 2025</span>
          </div>
        </div>
      </header>

      {/* Tab Navigation with smooth transitions */}
      <div className="border-b border-gray-800/30 bg-gray-900/40 backdrop-blur-xl sticky top-[73px] z-40">
        <div className="max-w-7xl mx-auto px-4 flex overflow-x-auto scrollbar-hide">
          {tabs.map((tab, index) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-4 font-semibold whitespace-nowrap border-b-2 transition-all duration-500 relative ${
                activeTab === tab.id
                  ? "border-orange-500 text-orange-400"
                  : "border-transparent text-gray-400 hover:text-gray-300"
              }`}
              style={{
                animation: `slideInFromTop 0.5s ease-out ${index * 0.1}s backwards`
              }}
            >
              {activeTab === tab.id && (
                <span className="absolute inset-0 bg-gradient-to-r from-orange-500/10 to-red-500/10 rounded-t-lg" />
              )}
              <span className="relative z-10">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 px-4 py-12 relative z-10">
        <div className="max-w-7xl mx-auto">
          {activeTab === "overview" && (
            <div className="space-y-16">
              {/* Hero section with floating elements */}
              <div className="text-center space-y-8 relative">
                {/* Floating icons */}
                <div className="absolute -left-10 top-20 animate-float">
                  <div className="w-16 h-16 bg-orange-500/10 rounded-2xl backdrop-blur-sm border border-orange-500/20 flex items-center justify-center">
                    <Flame className="w-8 h-8 text-orange-400" />
                  </div>
                </div>
                <div className="absolute -right-10 top-40 animate-float-delayed">
                  <div className="w-16 h-16 bg-blue-500/10 rounded-2xl backdrop-blur-sm border border-blue-500/20 flex items-center justify-center">
                    <Droplets className="w-8 h-8 text-blue-400" />
                  </div>
                </div>
                <div className="absolute left-1/4 -top-5 animate-float-slow">
                  <div className="w-12 h-12 bg-purple-500/10 rounded-xl backdrop-blur-sm border border-purple-500/20 flex items-center justify-center">
                    <Wind className="w-6 h-6 text-purple-400" />
                  </div>
                </div>

                <h2 
                  className="text-6xl md:text-8xl font-black leading-tight"
                  style={{
                    animation: "fadeInUp 1s ease-out",
                    transform: `translateY(${scrollY * 0.1}px)`
                  }}
                >
                  <span className="text-white drop-shadow-2xl">Autonomous Wildfire</span>
                  <br />
                  <span className="bg-gradient-to-r from-orange-400 via-red-500 to-pink-500 text-transparent bg-clip-text drop-shadow-2xl animate-gradient">
                    Response with Hybrid AI
                  </span>
                </h2>
                <p 
                  className="text-xl md:text-2xl text-gray-300 max-w-4xl mx-auto leading-relaxed"
                  style={{
                    animation: "fadeInUp 1s ease-out 0.2s backwards"
                  }}
                >
                  Combines <span className="text-blue-400 font-bold relative group">
                    PPO Reinforcement Learning
                    <span className="absolute bottom-0 left-0 w-full h-0.5 bg-blue-400 scale-x-0 group-hover:scale-x-100 transition-transform" />
                  </span> with <span className="text-purple-400 font-bold relative group">
                    LLM Strategic Guidance
                    <span className="absolute bottom-0 left-0 w-full h-0.5 bg-purple-400 scale-x-0 group-hover:scale-x-100 transition-transform" />
                  </span> for intelligent multi-agent drone coordination on <span className="text-green-400 font-bold relative group">
                    116K+ real historical fires
                    <span className="absolute bottom-0 left-0 w-full h-0.5 bg-green-400 scale-x-0 group-hover:scale-x-100 transition-transform" />
                  </span>
                </p>
              </div>

              {/* Animated stats grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6" style={{ animation: "fadeInUp 1s ease-out 0.4s backwards" }}>
                {[
                  { value: "23%", label: "More Area Saved", color: "orange", delay: "0s" },
                  { value: "18%", label: "Faster Containment", color: "blue", delay: "0.1s" },
                  { value: "92%", label: "Success Rate", color: "purple", delay: "0.2s" },
                  { value: "116K+", label: "Fire Scenarios", color: "green", delay: "0.3s" }
                ].map((stat, index) => (
                  <div
                    key={index}
                    className={`group relative bg-gradient-to-br from-${stat.color}-900/20 to-${stat.color}-900/5 border border-${stat.color}-600/30 rounded-2xl p-8 text-center hover:border-${stat.color}-500/60 transition-all duration-500 hover:scale-105 hover:-translate-y-2 cursor-pointer`}
                    style={{ animation: `scaleIn 0.6s ease-out ${stat.delay} backwards` }}
                  >
                    <div className={`absolute inset-0 bg-gradient-to-br from-${stat.color}-500/0 to-${stat.color}-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl`} />
                    <div className={`text-5xl md:text-6xl font-black text-${stat.color}-400 mb-3 relative z-10 group-hover:scale-110 transition-transform duration-300`}>{stat.value}</div>
                    <div className="text-sm font-semibold text-gray-300 relative z-10">{stat.label}</div>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-12">
                <div className="group bg-gradient-to-br from-blue-900/20 to-blue-900/5 border border-blue-800/30 rounded-xl p-6 hover:border-blue-400/50 transition">
                  <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center mb-4"><Zap className="w-6 h-6 text-blue-400" /></div>
                  <h3 className="text-lg font-semibold text-white mb-2">Hybrid AI</h3>
                  <p className="text-sm text-gray-400">PPO handles reactive control while LLM provides strategic guidance every 50 steps</p>
                </div>

                <div className="group bg-gradient-to-br from-green-900/20 to-green-900/5 border border-green-800/30 rounded-xl p-6 hover:border-green-400/50 transition">
                  <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center mb-4"><Globe className="w-6 h-6 text-green-400" /></div>
                  <h3 className="text-lg font-semibold text-white mb-2">Real Data</h3>
                  <p className="text-sm text-gray-400">116,337 historical fires + NOAA weather + USGS elevation data</p>
                </div>

                <div className="group bg-gradient-to-br from-purple-900/20 to-purple-900/5 border border-purple-800/30 rounded-xl p-6 hover:border-purple-400/50 transition">
                  <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mb-4"><Activity className="w-6 h-6 text-purple-400" /></div>
                  <h3 className="text-lg font-semibold text-white mb-2">Explainable</h3>
                  <p className="text-sm text-gray-400">Click drones for reasoning, see feature attributions, read LLM strategy</p>
                </div>

                <div className="group bg-gradient-to-br from-yellow-900/20 to-yellow-900/5 border border-yellow-800/30 rounded-xl p-6 hover:border-yellow-400/50 transition">
                  <div className="w-12 h-12 bg-yellow-500/20 rounded-lg flex items-center justify-center mb-4"><TrendingUp className="w-6 h-6 text-yellow-400" /></div>
                  <h3 className="text-lg font-semibold text-white mb-2">Reproducible</h3>
                  <p className="text-sm text-gray-400">Frozen test set, checksummed sources, seed tracking, full history</p>
                </div>
              </div>

              <div 
                className="flex flex-col md:flex-row gap-6 justify-center items-center pt-8"
                style={{ animation: "fadeInUp 1s ease-out 0.6s backwards" }}
              >
                <Link 
                  href="/sim" 
                  className="group relative px-10 py-5 bg-gradient-to-r from-orange-500 via-red-500 to-pink-500 text-white rounded-xl font-bold text-lg flex items-center gap-3 hover:shadow-2xl hover:shadow-orange-500/50 transition-all duration-500 transform hover:scale-110 min-w-[280px] justify-center overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-pink-500 via-red-500 to-orange-500 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                  <Play className="w-6 h-6 relative z-10 group-hover:rotate-12 transition-transform duration-300" />
                  <span className="relative z-10">Launch Mission Control</span>
                </Link>
                <Link 
                  href="/scenarios" 
                  className="group relative px-10 py-5 bg-purple-600/30 border border-purple-500/50 text-white rounded-xl font-bold text-lg hover:bg-purple-600/50 transition-all duration-500 transform hover:scale-105 min-w-[280px] justify-center overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-600/0 to-purple-600/30 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                  <span className="relative z-10">Explore Scenarios</span>
                </Link>
              </div>
            </div>
          )}

          {activeTab === "results" && (
            <div className="space-y-8">
              <h2 className="text-4xl font-black text-white mb-8">Proven Performance Gains</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {[
                  { 
                    icon: TrendingUp, 
                    value: "+23.4%", 
                    label: "More Area Saved", 
                    color: "green",
                    description: "Hybrid model strategically prioritizes high-risk zones, saving significantly more terrain from fire damage through intelligent resource allocation",
                    delay: "0s"
                  },
                  { 
                    icon: Zap, 
                    value: "-18.2%", 
                    label: "Faster Containment", 
                    color: "blue",
                    description: "Reduces critical time to full fire containment, preventing spread to populated areas and critical infrastructure",
                    delay: "0.1s"
                  },
                  { 
                    icon: Shield, 
                    value: "+15.7%", 
                    label: "Water Efficiency", 
                    color: "purple",
                    description: "Optimizes suppression resources, achieving superior containment with less water expenditure through strategic LLM guidance",
                    delay: "0.2s"
                  },
                  { 
                    icon: Award, 
                    value: "92%", 
                    label: "Success Rate", 
                    color: "yellow",
                    description: "Achieves successful containment in 92% of diverse scenarios, demonstrating reliability for real-world deployment",
                    delay: "0.3s"
                  }
                ].map((result, index) => {
                  const Icon = result.icon;
                  return (
                    <div 
                      key={index}
                      className={`group bg-gradient-to-br from-${result.color}-900/20 to-${result.color}-900/5 border border-${result.color}-600/30 rounded-2xl p-10 hover:border-${result.color}-500/60 transition-all duration-500 hover:scale-105 hover:-translate-y-2 cursor-pointer relative overflow-hidden`}
                      style={{ animation: `fadeInUp 0.6s ease-out ${result.delay} backwards` }}
                    >
                      <div className={`absolute inset-0 bg-gradient-to-br from-${result.color}-500/0 to-${result.color}-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                      <div className="flex items-center gap-6 mb-6 relative z-10">
                        <div className={`w-20 h-20 bg-${result.color}-500/20 rounded-xl flex items-center justify-center group-hover:scale-110 group-hover:rotate-3 transition-all duration-300`}>
                          <Icon className={`w-10 h-10 text-${result.color}-400`} />
                        </div>
                        <div>
                          <div className={`text-5xl font-black text-${result.color}-400 group-hover:scale-110 transition-transform duration-300`}>{result.value}</div>
                          <div className="text-lg text-gray-300 font-semibold">{result.label}</div>
                        </div>
                      </div>
                      <p className="text-gray-400 leading-relaxed relative z-10">{result.description}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {activeTab === "architecture" && (
            <div className="space-y-8">
              <h2 className="text-4xl font-black text-white mb-8">System Architecture</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {[
                  {
                    icon: Cpu,
                    title: "PPO Agent",
                    color: "blue",
                    delay: "0s",
                    features: [
                      "Low-level motor control & tactics",
                      "2,048 step rollout buffers",
                      "Real-time decision making (50ms)",
                      "Trained on 116K+ scenarios"
                    ]
                  },
                  {
                    icon: Code2,
                    title: "LLM Strategy (Qwen2.5)",
                    color: "purple",
                    delay: "0.1s",
                    features: [
                      "High-level strategic guidance",
                      "Called every 50 steps (~2.5s)",
                      "Analyzes global fire state",
                      "Generates interpretable advice"
                    ]
                  }
                ].map((agent, index) => {
                  const Icon = agent.icon;
                  return (
                    <div 
                      key={index}
                      className={`group bg-gradient-to-br from-${agent.color}-900/20 to-${agent.color}-900/5 border border-${agent.color}-600/30 rounded-2xl p-8 hover:border-${agent.color}-500/60 transition-all duration-500 hover:scale-105 hover:-translate-y-2 relative overflow-hidden`}
                      style={{ animation: `slideInFromTop 0.6s ease-out ${agent.delay} backwards` }}
                    >
                      <div className={`absolute inset-0 bg-gradient-to-br from-${agent.color}-500/0 to-${agent.color}-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                      <div className={`w-14 h-14 bg-${agent.color}-500/20 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 group-hover:rotate-6 transition-all duration-300 relative z-10`}>
                        <Icon className={`w-8 h-8 text-${agent.color}-400`} />
                      </div>
                      <h3 className={`text-2xl font-bold text-${agent.color}-400 mb-4 relative z-10`}>{agent.title}</h3>
                      <div className="space-y-3 text-gray-300 relative z-10">
                        {agent.features.map((feature, i) => (
                          <p key={i} className="flex items-center gap-2">
                            <span className={`text-${agent.color}-400`}>•</span> {feature}
                          </p>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div 
                className="bg-gradient-to-r from-orange-900/20 to-red-900/20 border border-orange-600/30 rounded-2xl p-8 mt-8 hover:border-orange-500/60 transition-all duration-500 hover:scale-[1.02] relative overflow-hidden group"
                style={{ animation: "fadeInUp 0.6s ease-out 0.2s backwards" }}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-orange-500/0 to-red-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <h3 className="text-2xl font-bold text-orange-400 mb-4 relative z-10">Integration & Evaluation</h3>
                <p className="text-gray-300 leading-relaxed mb-6 relative z-10">LLM guidance is encoded into PPO observation space as priority channels. PPO retains full motor control while leveraging strategic context. Results in 23% improvement with full explainability for judges and stakeholders.</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative z-10">
                  <div className="bg-gray-900/30 border border-gray-700 rounded-lg p-4 hover:border-cyan-400/50 transition-all duration-300 hover:scale-105">
                    <div className="font-semibold text-cyan-400 mb-2">5 Test Fires</div>
                    <p className="text-sm text-gray-400">Camp Fire CA, Riverside OR, East Troublesome CO, Okanogan WA, Lolo Peak MT</p>
                  </div>
                  <div className="bg-gray-900/30 border border-gray-700 rounded-lg p-4 hover:border-green-400/50 transition-all duration-300 hover:scale-105">
                    <div className="font-semibold text-green-400 mb-2">25 Evaluation Episodes</div>
                    <p className="text-sm text-gray-400">5 fires × 5 random seeds for reproducible held-out test set</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "data" && (
            <div className="space-y-8">
              <h2 className="text-4xl font-black text-white mb-8">Data Provenance & Verification</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
                {[
                  {
                    value: "116,337",
                    title: "Fire Perimeters",
                    description: "InterAgency Fire Perimeter History (1878-2024) with cryptographic checksums for reproducibility",
                    color: "orange",
                    delay: "0s"
                  },
                  {
                    value: "2,847",
                    title: "Weather Records",
                    description: "NOAA historical data: temperature, humidity, wind speed/direction, precipitation at fire locations",
                    color: "green",
                    delay: "0.1s"
                  },
                  {
                    value: "1M+",
                    title: "Terrain Points",
                    description: "USGS 3DEP elevation data (30m resolution) for accurate slope and terrain analysis",
                    color: "blue",
                    delay: "0.2s"
                  }
                ].map((data, index) => (
                  <div 
                    key={index}
                    className={`group bg-gradient-to-br from-${data.color}-900/20 to-${data.color}-900/5 border border-${data.color}-600/30 rounded-2xl p-8 hover:border-${data.color}-500/60 transition-all duration-500 hover:scale-105 hover:-translate-y-2 relative overflow-hidden cursor-pointer`}
                    style={{ animation: `scaleIn 0.6s ease-out ${data.delay} backwards` }}
                  >
                    <div className={`absolute inset-0 bg-gradient-to-br from-${data.color}-500/0 to-${data.color}-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                    <div className={`text-5xl font-black text-${data.color}-400 mb-3 relative z-10 group-hover:scale-110 transition-transform duration-300`}>{data.value}</div>
                    <h3 className="text-xl font-bold text-white mb-3 relative z-10">{data.title}</h3>
                    <p className="text-gray-400 text-sm leading-relaxed relative z-10">{data.description}</p>
                  </div>
                ))}
              </div>

              <Link 
                href="/sources" 
                className="group relative block bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl p-8 text-center font-bold text-lg transition-all duration-500 transform hover:scale-105 flex items-center justify-center gap-2 overflow-hidden"
                style={{ animation: "fadeInUp 0.6s ease-out 0.3s backwards" }}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-blue-600 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <span className="relative z-10">View All Data Sources with SHA-256 Checksums</span>
                <ExternalLink className="w-5 h-5 relative z-10 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform duration-300" />
              </Link>
            </div>
          )}
        </div>
      </main>

      {/* Judge Info Section */}
      <section className="border-t border-gray-800 bg-gradient-to-r from-purple-900/10 to-orange-900/10 py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <p 
            className="text-center text-sm text-gray-400 mb-8 font-semibold"
            style={{ animation: "fadeInUp 0.6s ease-out" }}
          >
            FOR JUDGES & EVALUATORS
          </p>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {[
              { href: "/scenarios", emoji: "📍", title: "5 Scenarios", desc: "Real fires with data receipts", delay: "0s" },
              { href: "/lab", emoji: "⚗️", title: "Experiment Lab", desc: "Run reproducible tests", delay: "0.1s" },
              { href: "/runs", emoji: "📊", title: "Run History", desc: "Complete audit trail", delay: "0.2s" },
              { href: "/sources", emoji: "🔐", title: "Data Sources", desc: "Checksums & verification", delay: "0.3s" },
              { href: "/sim", emoji: "🚀", title: "Mission Control", desc: "Live simulation", delay: "0.4s", special: true }
            ].map((item, index) => (
              <Link 
                key={index}
                href={item.href} 
                className={`group p-6 ${item.special ? 'bg-gradient-to-r from-orange-600/30 to-red-600/30 border border-orange-500/50 hover:border-orange-400' : 'bg-gray-900/50 border border-gray-800 hover:border-orange-500/50'} rounded-xl text-center transition-all duration-500 transform hover:scale-105 hover:-translate-y-2 relative overflow-hidden`}
                style={{ animation: `scaleIn 0.6s ease-out ${item.delay} backwards` }}
              >
                <div className="absolute inset-0 bg-gradient-to-br from-orange-500/0 to-orange-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="text-3xl mb-2 relative z-10 group-hover:scale-125 transition-transform duration-300">{item.emoji}</div>
                <div className="font-bold text-white mb-1 relative z-10">{item.title}</div>
                <div className={`text-xs ${item.special ? 'text-orange-300' : 'text-gray-400'} relative z-10`}>{item.desc}</div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800/50 py-8 px-4 bg-gray-950/50 relative z-10">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-sm text-gray-400 mb-2">
            <span className="font-bold text-orange-400">AURORA</span> - Autonomous Unified Response Orchestration for Real-world Actions
          </p>
          <p className="text-xs text-gray-500">
            Shaurya Mallampati | ISEF 2025 | Computer Science | Built with Next.js, PyTorch, Qwen2.5
          </p>
        </div>
      </footer>

      {/* Animation styles */}
      <style jsx global>{`
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes scaleIn {
          from {
            opacity: 0;
            transform: scale(0.9);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        @keyframes slideInFromTop {
          from {
            opacity: 0;
            transform: translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0px);
          }
          50% {
            transform: translateY(-20px);
          }
        }

        @keyframes gradient {
          0%, 100% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
        }

        .animate-float {
          animation: float 3s ease-in-out infinite;
        }

        .animate-float-delayed {
          animation: float 3s ease-in-out infinite 1s;
        }

        .animate-float-slow {
          animation: float 4s ease-in-out infinite 0.5s;
        }

        .animate-gradient {
          background-size: 200% 200%;
          animation: gradient 3s ease infinite;
        }

        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }

        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
}
