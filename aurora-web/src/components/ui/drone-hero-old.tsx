'use client'

import { Spotlight } from "@/components/ui/spotlight"

export function DroneHeroScene() {
  return (
    <div className="w-full bg-gradient-to-b from-slate-900 via-slate-800 to-black relative overflow-hidden rounded-2xl border border-slate-700/50">
      <Spotlight
        className="-top-40 -left-32 md:-left-96 md:-top-20"
        fill="orange"
      />
      
      <div className="flex h-[500px]">
        {/* Left content */}
        <div className="flex-1 p-8 relative z-10 flex flex-col justify-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-3">
            Interactive Drone
          </h2>
          <p className="text-sm md:text-base text-gray-300 max-w-sm leading-relaxed">
            Explore the hybrid AI architecture in 3D. Our autonomous drone system combines PPO learning with LLM strategy for real-time wildfire suppression.
          </p>
          <div className="mt-6 flex gap-2 flex-wrap">
            <span className="px-3 py-1 rounded-full text-xs bg-orange-500/20 text-orange-300 border border-orange-500/30">PPO Agent</span>
            <span className="px-3 py-1 rounded-full text-xs bg-purple-500/20 text-purple-300 border border-purple-500/30">LLM Strategy</span>
            <span className="px-3 py-1 rounded-full text-xs bg-blue-500/20 text-blue-300 border border-blue-500/30">Real-time Control</span>
          </div>
        </div>

        {/* Right 3D drone visualization */}
        <div className="flex-1 relative bg-gradient-to-br from-slate-950 via-blue-950/20 to-slate-900 flex items-center justify-center overflow-hidden">
          {/* Background grid */}
          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#0369a1" strokeWidth="0.5" opacity="0.1"/>
              </pattern>
            </defs>
            <rect x="0" y="0" width="400" height="400" fill="url(#grid)" />
          </svg>

          {/* Main drone SVG - DJI Mavic style */}
          <svg
            className="w-full h-full max-w-md relative z-10"
            viewBox="0 0 500 500"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              {/* Gradients for professional metallic look */}
              <linearGradient id="bodyGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style={{ stopColor: '#f5f5f5', stopOpacity: 1 }} />
                <stop offset="50%" style={{ stopColor: '#d4d4d8', stopOpacity: 1 }} />
                <stop offset="100%" style={{ stopColor: '#a1a1aa', stopOpacity: 1 }} />
              </linearGradient>
              <linearGradient id="armGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style={{ stopColor: '#e4e4e7', stopOpacity: 1 }} />
                <stop offset="100%" style={{ stopColor: '#71717a', stopOpacity: 1 }} />
              </linearGradient>
              <linearGradient id="propGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style={{ stopColor: '#18181b', stopOpacity: 0.9 }} />
                <stop offset="100%" style={{ stopColor: '#3f3f46', stopOpacity: 0.9 }} />
              </linearGradient>
              <filter id="droneGlow">
                <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
              <filter id="shadowFilter">
                <feDropShadow dx="0" dy="8" stdDeviation="4" floodOpacity="0.3"/>
              </filter>
              <style>{`
                @keyframes propellerSpin {
                  from { transform: rotate(0deg); }
                  to { transform: rotate(360deg); }
                }
                @keyframes droneBob {
                  0%, 100% { transform: translateY(0px) rotateZ(0deg); }
                  50% { transform: translateY(-20px) rotateZ(1deg); }
                }
                @keyframes cameraTilt {
                  0%, 100% { transform: rotateX(15deg); }
                  50% { transform: rotateX(20deg); }
                }
                .propeller-spin { animation: propellerSpin 1.2s linear infinite; }
                .drone-bob { animation: droneBob 3.5s ease-in-out infinite; }
                .camera-tilt { animation: cameraTilt 2s ease-in-out infinite; }
              `}</style>
            </defs>

            <g className="drone-3d" style={{ transformStyle: 'preserve-3d' }}>
              {/* Main futuristic body - 3D box perspective */}
              {/* Top face */}
              <polygon points="150,120 250,120 260,100 160,100" fill="url(#bodyTop)" filter="url(#shadow)" />
              
              {/* Front face */}
              <polygon points="150,120 250,120 250,180 150,180" fill="url(#bodyTop)" opacity="0.95" />
              
              {/* Right side face */}
              <polygon points="250,120 260,100 260,160 250,180" fill="url(#bodySide)" opacity="0.85" />
              
              {/* Left side face */}
              <polygon points="150,120 160,100 160,160 150,180" fill="url(#bodySide)" opacity="0.85" />
              
              {/* Bottom face (subtle) */}
              <polygon points="150,180 250,180 260,160 160,160" fill="#0f3460" opacity="0.4" />

              {/* Front camera - glowing blue */}
              <rect x="190" y="135" width="20" height="20" rx="4" fill="#1e293b" />
              <circle cx="200" cy="145" r="6" fill="#06b6d4" filter="url(#glow2)" opacity="0.9" />
              <circle cx="200" cy="145" r="8" fill="none" stroke="#06b6d4" strokeWidth="1" opacity="0.5" className="glow-pulse" />
              
              {/* Status indicators - LED panel */}
              <circle cx="170" cy="150" r="2.5" fill="#10b981" filter="url(#glow2)" />
              <circle cx="230" cy="150" r="2.5" fill="#10b981" filter="url(#glow2)" />
              
              {/* Battery indicator */}
              <rect x="185" y="160" width="30" height="6" rx="2" fill="#1e293b" stroke="#334155" strokeWidth="0.5" />
              <rect x="187" y="162" width="20" height="2" fill="#f97316" />
            </g>

            {/* Arms extending outward - 3D with proper perspective */}
            <g>
              {/* Top-left arm - 3D curved */}
              <defs>
                <linearGradient id="armTopLeft" x1="200" y1="150" x2="60" y2="70" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" style={{ stopColor: '#334155', stopOpacity: 1 }} />
                  <stop offset="100%" style={{ stopColor: '#0f172a', stopOpacity: 1 }} />
                </linearGradient>
              </defs>
              <path d="M 160 120 Q 110 95 60 70" stroke="url(#armTopLeft)" strokeWidth="14" fill="none" strokeLinecap="round" filter="url(#shadow)" />
              {/* Top-left arm top side */}
              <path d="M 160 115 Q 110 90 60 65" stroke="#475569" strokeWidth="3" fill="none" strokeLinecap="round" opacity="0.6" />
              
              {/* Top-right arm - 3D curved */}
              <defs>
                <linearGradient id="armTopRight" x1="200" y1="150" x2="340" y2="70" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" style={{ stopColor: '#334155', stopOpacity: 1 }} />
                  <stop offset="100%" style={{ stopColor: '#0f172a', stopOpacity: 1 }} />
                </linearGradient>
              </defs>
              <path d="M 240 120 Q 290 95 340 70" stroke="url(#armTopRight)" strokeWidth="14" fill="none" strokeLinecap="round" filter="url(#shadow)" />
              {/* Top-right arm top side */}
              <path d="M 240 115 Q 290 90 340 65" stroke="#475569" strokeWidth="3" fill="none" strokeLinecap="round" opacity="0.6" />
              
              {/* Bottom-left arm - 3D curved with transparency */}
              <defs>
                <linearGradient id="armBottomLeft" x1="200" y1="150" x2="60" y2="330" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" style={{ stopColor: '#334155', stopOpacity: 0.8 }} />
                  <stop offset="100%" style={{ stopColor: '#0f172a', stopOpacity: 0.8 }} />
                </linearGradient>
              </defs>
              <path d="M 160 180 Q 110 205 60 330" stroke="url(#armBottomLeft)" strokeWidth="14" fill="none" strokeLinecap="round" filter="url(#shadow)" opacity="0.8" />
              
              {/* Bottom-right arm - 3D curved with transparency */}
              <defs>
                <linearGradient id="armBottomRight" x1="200" y1="150" x2="340" y2="330" gradientUnits="userSpaceOnUse">
                  <stop offset="0%" style={{ stopColor: '#334155', stopOpacity: 0.8 }} />
                  <stop offset="100%" style={{ stopColor: '#0f172a', stopOpacity: 0.8 }} />
                </linearGradient>
              </defs>
              <path d="M 240 180 Q 290 205 340 330" stroke="url(#armBottomRight)" strokeWidth="14" fill="none" strokeLinecap="round" filter="url(#shadow)" opacity="0.8" />
            </g>

            {/* Motors and propellers */}
            <g>
              {/* Top-left motor assembly */}
              <circle cx="60" cy="70" r="12" fill="#0f172a" stroke="#334155" strokeWidth="2" filter="url(#shadow)" />
              <circle cx="60" cy="70" r="14" fill="none" stroke="#f97316" strokeWidth="1.5" opacity="0.5" />
              <g className="propeller" style={{ transformOrigin: '60px 70px' }}>
                <ellipse cx="60" cy="70" rx="32" ry="8" fill="#1e293b" opacity="0.8" />
                <ellipse cx="60" cy="70" rx="32" ry="8" fill="#1e293b" opacity="0.8" transform="rotate(90 60 70)" />
                <ellipse cx="60" cy="70" rx="30" ry="6" fill="#334155" opacity="0.5" />
              </g>

              {/* Top-right motor assembly */}
              <circle cx="340" cy="70" r="12" fill="#0f172a" stroke="#334155" strokeWidth="2" filter="url(#shadow)" />
              <circle cx="340" cy="70" r="14" fill="none" stroke="#f97316" strokeWidth="1.5" opacity="0.5" />
              <g className="propeller" style={{ transformOrigin: '340px 70px' }}>
                <ellipse cx="340" cy="70" rx="32" ry="8" fill="#1e293b" opacity="0.8" />
                <ellipse cx="340" cy="70" rx="32" ry="8" fill="#1e293b" opacity="0.8" transform="rotate(90 340 70)" />
                <ellipse cx="340" cy="70" rx="30" ry="6" fill="#334155" opacity="0.5" />
              </g>

              {/* Bottom-left motor assembly */}
              <circle cx="60" cy="330" r="12" fill="#0f172a" stroke="#334155" strokeWidth="2" filter="url(#shadow)" opacity="0.85" />
              <circle cx="60" cy="330" r="14" fill="none" stroke="#f97316" strokeWidth="1.5" opacity="0.3" />
              <g className="propeller" style={{ transformOrigin: '60px 330px' }}>
                <ellipse cx="60" cy="330" rx="32" ry="8" fill="#1e293b" opacity="0.7" />
                <ellipse cx="60" cy="330" rx="32" ry="8" fill="#1e293b" opacity="0.7" transform="rotate(90 60 330)" />
                <ellipse cx="60" cy="330" rx="30" ry="6" fill="#334155" opacity="0.4" />
              </g>

              {/* Bottom-right motor assembly */}
              <circle cx="340" cy="330" r="12" fill="#0f172a" stroke="#334155" strokeWidth="2" filter="url(#shadow)" opacity="0.85" />
              <circle cx="340" cy="330" r="14" fill="none" stroke="#f97316" strokeWidth="1.5" opacity="0.3" />
              <g className="propeller" style={{ transformOrigin: '340px 330px' }}>
                <ellipse cx="340" cy="330" rx="32" ry="8" fill="#1e293b" opacity="0.7" />
                <ellipse cx="340" cy="330" rx="32" ry="8" fill="#1e293b" opacity="0.7" transform="rotate(90 340 330)" />
                <ellipse cx="340" cy="330" rx="30" ry="6" fill="#334155" opacity="0.4" />
              </g>
            </g>

            {/* Advanced tech indicators - Neural network visualization */}
            <g opacity="0.3" stroke="#06b6d4" strokeWidth="1" fill="none">
              <circle cx="200" cy="200" r="60" />
              <circle cx="200" cy="200" r="100" />
              
              {/* Connection lines */}
              <line x1="200" y1="200" x2="60" y2="70" stroke="#06b6d4" opacity="0.3" />
              <line x1="200" y1="200" x2="340" y2="70" stroke="#06b6d4" opacity="0.3" />
              <line x1="200" y1="200" x2="60" y2="330" stroke="#06b6d4" opacity="0.3" />
              <line x1="200" y1="200" x2="340" y2="330" stroke="#06b6d4" opacity="0.3" />
            </g>

            {/* Energy aura */}
            <circle cx="200" cy="200" r="160" fill="none" stroke="#f97316" strokeWidth="2" opacity="0.2" className="glow-pulse" />
          </svg>

          {/* Ambient glow */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-56 h-56 bg-orange-500/5 rounded-full blur-3xl"></div>
            <div className="absolute w-48 h-48 bg-cyan-500/5 rounded-full blur-3xl"></div>
          </div>
        </div>
      </div>
    </div>
  )
}
