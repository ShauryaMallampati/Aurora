'use client'

import { Spotlight } from "@/components/ui/spotlight"

export function DroneHeroScene() {
  return (
    <div className="w-full bg-[#0F1115] relative overflow-hidden rounded-2xl border border-white/10 hover:border-[#F7931A]/30 transition-all duration-500">
      {/* Grid pattern background */}
      <div className="absolute inset-0 bg-grid-pattern-subtle opacity-30"></div>

      <Spotlight
        className="-top-40 -left-32 md:-left-96 md:-top-20"
        fill="#F7931A"
      />

      <div className="flex flex-col md:flex-row h-auto md:h-[500px]">
        {/* Left content */}
        <div className="flex-1 p-8 md:p-10 relative z-10 flex flex-col justify-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F7931A]/10 border border-[#F7931A]/30 text-xs font-mono text-[#F7931A] mb-4 w-fit tracking-wider">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#F7931A] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-[#F7931A]"></span>
            </span>
            INTERACTIVE
          </div>
          <h2 className="text-3xl md:text-4xl font-bold font-heading text-white mb-4 leading-tight">
            Autonomous Drone{" "}
            <span className="bg-gradient-to-r from-[#F7931A] to-[#FFD600] bg-clip-text text-transparent">System</span>
          </h2>
          <p className="text-sm md:text-base text-[#94A3B8] max-w-sm leading-relaxed mb-6">
            Explore the hybrid AI architecture in 3D. Our autonomous drone system combines PPO learning with LLM strategy for real-time wildfire suppression.
          </p>
          <div className="flex gap-2 flex-wrap">
            <span className="px-3 py-1.5 rounded-full text-xs font-mono bg-[#EA580C]/20 text-[#F7931A] border border-[#EA580C]/30 tracking-wide">PPO AGENT</span>
            <span className="px-3 py-1.5 rounded-full text-xs font-mono bg-[#FFD600]/10 text-[#FFD600] border border-[#FFD600]/30 tracking-wide">LLM STRATEGY</span>
            <span className="px-3 py-1.5 rounded-full text-xs font-mono bg-white/5 text-white border border-white/20 tracking-wide">REAL-TIME</span>
          </div>
        </div>

        {/* Right 3D drone visualization */}
        <div className="flex-1 relative bg-gradient-to-br from-[#030304] via-[#0F1115] to-[#030304] flex items-center justify-center overflow-hidden min-h-[350px] md:min-h-0">
          {/* Background grid */}
          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" x="0" y="0" width="50" height="50" patternUnits="userSpaceOnUse">
                <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#F7931A" strokeWidth="0.5" opacity="0.1" />
              </pattern>
              <radialGradient id="gridFade" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="white" stopOpacity="1" />
                <stop offset="100%" stopColor="white" stopOpacity="0" />
              </radialGradient>
              <mask id="gridMask">
                <rect x="0" y="0" width="500" height="500" fill="url(#gridFade)" />
              </mask>
            </defs>
            <rect x="0" y="0" width="500" height="500" fill="url(#grid)" mask="url(#gridMask)" />
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
                <feGaussianBlur stdDeviation="3" result="coloredBlur" />
                <feMerge>
                  <feMergeNode in="coloredBlur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
              <filter id="orangeGlow">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feFlood floodColor="#F7931A" floodOpacity="0.6" />
                <feComposite in2="blur" operator="in" />
                <feMerge>
                  <feMergeNode />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
              <filter id="shadowFilter">
                <feDropShadow dx="0" dy="8" stdDeviation="4" floodOpacity="0.3" />
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
                @keyframes orbitalPulse {
                  0%, 100% { opacity: 0.3; }
                  50% { opacity: 0.6; }
                }
                .propeller-spin { animation: propellerSpin 1.2s linear infinite; }
                .drone-bob { animation: droneBob 3.5s ease-in-out infinite; }
                .camera-tilt { animation: cameraTilt 2s ease-in-out infinite; }
                .orbital-pulse { animation: orbitalPulse 3s ease-in-out infinite; }
              `}</style>
            </defs>

            <g className="drone-bob" style={{ transformStyle: 'preserve-3d' }}>
              {/* Main body - sleek drone chassis */}
              <ellipse cx="250" cy="240" rx="45" ry="60" fill="url(#bodyGradient)" filter="url(#shadowFilter)" />

              {/* Front canopy/dome */}
              <ellipse cx="250" cy="210" rx="35" ry="28" fill="#f5f5f5" opacity="0.8" />
              <ellipse cx="250" cy="208" rx="32" ry="24" fill="#e4e4e7" opacity="0.6" />

              {/* Camera lens - orange accent for Bitcoin DeFi */}
              <ellipse cx="250" cy="210" rx="12" ry="10" fill="#2d2d2d" />
              <ellipse cx="250" cy="210" rx="10" ry="8" fill="#F7931A" opacity="0.9" filter="url(#orangeGlow)" />

              {/* Status lights - orange themed */}
              <circle cx="230" cy="225" r="3" fill="#F7931A" opacity="0.9" />
              <circle cx="270" cy="225" r="3" fill="#FFD600" opacity="0.9" />

              {/* Gimbal/stabilizer mount */}
              <rect x="240" y="265" width="20" height="15" rx="2" fill="#a1a1aa" opacity="0.7" />

              {/* Landing gear struts - thin and minimal */}
              <line x1="220" y1="295" x2="210" y2="330" stroke="#71717a" strokeWidth="3" />
              <line x1="280" y1="295" x2="290" y2="330" stroke="#71717a" strokeWidth="3" />

              {/* Landing gear pads */}
              <rect x="205" y="328" width="10" height="4" rx="2" fill="#52525b" />
              <rect x="285" y="328" width="10" height="4" rx="2" fill="#52525b" />
            </g>

            {/* Arms - folding design */}
            <g filter="url(#shadowFilter)">
              {/* Top-left arm */}
              <path d="M 215 215 Q 150 180 90 130" stroke="url(#armGradient)" strokeWidth="16" fill="none" strokeLinecap="round" />

              {/* Top-right arm */}
              <path d="M 285 215 Q 350 180 410 130" stroke="url(#armGradient)" strokeWidth="16" fill="none" strokeLinecap="round" />

              {/* Bottom-left arm */}
              <path d="M 215 265 Q 150 300 90 350" stroke="url(#armGradient)" strokeWidth="16" fill="none" strokeLinecap="round" opacity="0.9" />

              {/* Bottom-right arm */}
              <path d="M 285 265 Q 350 300 410 350" stroke="url(#armGradient)" strokeWidth="16" fill="none" strokeLinecap="round" opacity="0.9" />
            </g>

            {/* Motor arms with connectors */}
            <g>
              {/* Top-left motor connector */}
              <rect x="85" y="125" width="20" height="12" rx="4" fill="#71717a" />

              {/* Top-right motor connector */}
              <rect x="395" y="125" width="20" height="12" rx="4" fill="#71717a" />

              {/* Bottom-left motor connector */}
              <rect x="85" y="343" width="20" height="12" rx="4" fill="#52525b" opacity="0.85" />

              {/* Bottom-right motor connector */}
              <rect x="395" y="343" width="20" height="12" rx="4" fill="#52525b" opacity="0.85" />
            </g>

            {/* Motors - DJI style cylindrical motors */}
            <g>
              {/* Top-left motor */}
              <circle cx="95" cy="131" r="14" fill="#1a1a1a" stroke="#52525b" strokeWidth="2" />
              <circle cx="95" cy="131" r="11" fill="#27272a" />

              {/* Top-right motor */}
              <circle cx="405" cy="131" r="14" fill="#1a1a1a" stroke="#52525b" strokeWidth="2" />
              <circle cx="405" cy="131" r="11" fill="#27272a" />

              {/* Bottom-left motor */}
              <circle cx="95" cy="349" r="14" fill="#1a1a1a" stroke="#52525b" strokeWidth="2" opacity="0.85" />
              <circle cx="95" cy="349" r="11" fill="#27272a" opacity="0.85" />

              {/* Bottom-right motor */}
              <circle cx="405" cy="349" r="14" fill="#1a1a1a" stroke="#52525b" strokeWidth="2" opacity="0.85" />
              <circle cx="405" cy="349" r="11" fill="#27272a" opacity="0.85" />
            </g>

            {/* Propellers - carbon fiber look */}
            <g>
              {/* Top-left propeller */}
              <g className="propeller-spin" style={{ transformOrigin: '95px 131px' }}>
                <ellipse cx="95" cy="131" rx="48" ry="10" fill="url(#propGradient)" />
                <ellipse cx="95" cy="131" rx="48" ry="10" fill="url(#propGradient)" transform="rotate(90 95 131)" />
                {/* Propeller shine */}
                <ellipse cx="95" cy="131" rx="45" ry="8" fill="#f5f5f5" opacity="0.15" />
              </g>

              {/* Top-right propeller */}
              <g className="propeller-spin" style={{ transformOrigin: '405px 131px' }}>
                <ellipse cx="405" cy="131" rx="48" ry="10" fill="url(#propGradient)" />
                <ellipse cx="405" cy="131" rx="48" ry="10" fill="url(#propGradient)" transform="rotate(90 405 131)" />
                <ellipse cx="405" cy="131" rx="45" ry="8" fill="#f5f5f5" opacity="0.15" />
              </g>

              {/* Bottom-left propeller */}
              <g className="propeller-spin" style={{ transformOrigin: '95px 349px' }}>
                <ellipse cx="95" cy="349" rx="48" ry="10" fill="url(#propGradient)" opacity="0.85" />
                <ellipse cx="95" cy="349" rx="48" ry="10" fill="url(#propGradient)" transform="rotate(90 95 349)" opacity="0.85" />
                <ellipse cx="95" cy="349" rx="45" ry="8" fill="#f5f5f5" opacity="0.12" />
              </g>

              {/* Bottom-right propeller */}
              <g className="propeller-spin" style={{ transformOrigin: '405px 349px' }}>
                <ellipse cx="405" cy="349" rx="48" ry="10" fill="url(#propGradient)" opacity="0.85" />
                <ellipse cx="405" cy="349" rx="48" ry="10" fill="url(#propGradient)" transform="rotate(90 405 349)" opacity="0.85" />
                <ellipse cx="405" cy="349" rx="45" ry="8" fill="#f5f5f5" opacity="0.12" />
              </g>
            </g>

            {/* AI/Tech indicators - Bitcoin orange theme */}
            <g className="orbital-pulse" stroke="#F7931A" strokeWidth="1.5" fill="none">
              <circle cx="250" cy="240" r="100" opacity="0.4" />
              <circle cx="250" cy="240" r="130" opacity="0.25" />
              {/* Connection lines to motors */}
              <line x1="250" y1="240" x2="95" y2="131" opacity="0.2" />
              <line x1="250" y1="240" x2="405" y2="131" opacity="0.2" />
              <line x1="250" y1="240" x2="95" y2="349" opacity="0.2" />
              <line x1="250" y1="240" x2="405" y2="349" opacity="0.2" />
            </g>

            {/* Outer glow rings */}
            <circle cx="250" cy="240" r="180" fill="none" stroke="#F7931A" strokeWidth="1.5" opacity="0.1" />
            <circle cx="250" cy="240" r="200" fill="none" stroke="#FFD600" strokeWidth="0.5" opacity="0.05" />
          </svg>

          {/* Ambient glow */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-64 h-64 bg-[#F7931A]/10 rounded-full blur-[80px]"></div>
            <div className="absolute w-48 h-48 bg-[#FFD600]/5 rounded-full blur-[60px]"></div>
          </div>
        </div>
      </div>
    </div>
  )
}
