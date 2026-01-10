import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/shared/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Core Bitcoin DeFi Palette
        background: "#030304",
        surface: "#0F1115",
        foreground: "#FFFFFF",
        muted: "#94A3B8",
        
        // Bitcoin Fire Energy
        bitcoin: {
          orange: "#F7931A",
          burnt: "#EA580C",
          gold: "#FFD600",
        },
        
        // Legacy fire/drone colors for backward compatibility
        fire: {
          burning: "#ff4444",
          burnt: "#333333",
          cool: "#ff8800",
        },
        drone: {
          active: "#ffeb3b",
          inactive: "#888888",
          suppressing: "#4facfe",
          scanning: "#8bc34a",
        },
      },
      fontFamily: {
        heading: ["Space Grotesk", "system-ui", "sans-serif"],
        body: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        float: "float 8s ease-in-out infinite",
        "orbital-spin": "orbital-spin 10s linear infinite",
        "orbital-spin-reverse": "orbital-spin-reverse 15s linear infinite",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
        "bounce-slow": "bounce-slow 3s ease-in-out infinite",
      },
      keyframes: {
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-20px)" },
        },
        "orbital-spin": {
          from: { transform: "rotate(0deg)" },
          to: { transform: "rotate(360deg)" },
        },
        "orbital-spin-reverse": {
          from: { transform: "rotate(360deg)" },
          to: { transform: "rotate(0deg)" },
        },
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 20px -5px rgba(247, 147, 26, 0.4)" },
          "50%": { boxShadow: "0 0 30px -5px rgba(247, 147, 26, 0.7)" },
        },
        "bounce-slow": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-10px)" },
        },
      },
      boxShadow: {
        "glow-orange": "0 0 20px -5px rgba(234, 88, 12, 0.5)",
        "glow-orange-intense": "0 0 30px -5px rgba(247, 147, 26, 0.6)",
        "glow-gold": "0 0 20px rgba(255, 214, 0, 0.3)",
        "glow-subtle": "0 0 50px -10px rgba(247, 147, 26, 0.1)",
      },
      borderRadius: {
        "2xl": "16px",
        "3xl": "24px",
      },
    },
  },
  plugins: [],
};

export default config;
