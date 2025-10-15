# AURORA Web - Live Wildfire Simulation Dashboard

Production-ready Next.js 14 frontend for the AURORA hybrid PPO+LLM wildfire suppression system. Built for ISEF presentation and judging.

## 🚀 Features

- **Live Simulation Viewer** - Real-time telemetry streaming via SSE
- **Google Maps Integration** - Fire heat map overlays, drone markers with heading indicators
- **Strategic Guidance Display** - LLM-generated priority zones and defensive lines
- **Real-Time Metrics** - Fire containment, burned area, drone fleet status, weather
- **Interactive Charts** - Live recharts visualization of all key metrics
- **Run Management** - Browse, compare, and export past simulations
- **Dark Mode UI** - Full TailwindCSS dark theme
- **Keyboard Shortcuts** - Space (play/pause), R (reset), Arrow keys (speed)
- **Accessibility** - ARIA labels, keyboard navigation, screen reader support
- **Mock Mode** - Works offline without Python backend for demos

## 📁 Project Structure

```
aurora-web/
├── src/
│   ├── app/
│   │   ├── page.tsx                  # Home/landing page
│   │   ├── sim/
│   │   │   ├── page.tsx              # Simulation dashboard
│   │   │   ├── ControlBar.tsx        # Top control bar with play/pause/settings
│   │   │   ├── MapStage.tsx          # Google Maps with fire/drones/perimeter
│   │   │   ├── FireLayerCanvas.tsx   # Canvas overlay for heat map
│   │   │   ├── DroneLayer.tsx        # Drone markers with InfoWindows
│   │   │   ├── PerimeterLayer.tsx    # GeoJSON fire perimeter polygon
│   │   │   ├── RightPanel.tsx        # Tabbed sidebar
│   │   │   └── tabs/
│   │   │       ├── MetricsTab.tsx    # Real-time metrics
│   │   │       ├── TelemetryTab.tsx  # Drone states + events
│   │   │       ├── GuidanceTab.tsx   # LLM strategic guidance
│   │   │       ├── ChartsTab.tsx     # Recharts line/area charts
│   │   │       └── LogsTab.tsx       # Simulation logs + export
│   │   ├── runs/                     # (Future) Run browser
│   │   ├── compare/                  # (Future) Side-by-side comparison
│   │   └── about/                    # (Future) Project info
│   └── shared/
│       ├── types.ts                  # TypeScript interfaces
│       ├── api.ts                    # SSE client + mock stream
│       └── store.ts                  # Zustand global state
├── .env.local                        # API keys (not in git)
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── README.md
```

## 🛠️ Setup

### Prerequisites

- Node.js 18+ and npm
- Google Maps API key (provided in `.env.local`)

### Installation

```bash
cd aurora-web
npm install
```

### Environment Variables

Create `.env.local` (already created):

```env
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_key_here
```

### Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm start
```

## 🎮 Usage

### Running a Simulation

1. Navigate to `/sim` or click "Start Simulation" on home page
2. Configure settings (Model, Drones, LLM Cadence, Weather, Seed)
3. Click **Start** to begin simulation
4. Use **Play/Pause**, **Reset**, **Step** controls
5. Adjust playback speed (0.25x - 8x)
6. Switch between tabs: Metrics, Telemetry, Guidance, Charts, Logs

### Mock Mode (Offline Demo)

By default, the app uses a **mock SSE stream** that generates synthetic telemetry data. This allows the frontend to work standalone without the Python backend running.

To connect to a live Python backend:
1. Set `NEXT_PUBLIC_API_BASE_URL` in `.env.local`
2. Update `SimulationStream` initialization in `ControlBar.tsx` to use real endpoint instead of mock

### Keyboard Shortcuts

- **Space** - Play/Pause
- **R** - Reset simulation
- **Left/Right Arrows** - Adjust playback speed
- **1-5** - Switch between tabs

## 📊 Data Contracts

### TelemetryTick (SSE Event)

```typescript
interface TelemetryTick {
  t: number;
  timestamp: string;
  drones: Drone[];
  weather: Weather;
  metrics: Metrics;
  events: SimEvent[];
  fireGrid: string; // base64 encoded 64x64 array
  fireOrigin: { lat: number; lng: number };
}
```

### LLM Guidance (SSE Event)

```typescript
interface LLMGuidance {
  t: number;
  timestamp: string;
  strategy: {
    priorityZones?: Array<{ lat: number; lng: number; radius: number }>;
    defensiveLines?: Array<Array<{ lat: number; lng: number }>>;
    notes: string;
  };
}
```

## 🧪 Acceptance Tests

### Visual Tests

1. **Home Page**
   - [ ] Hero section loads with gradient background
   - [ ] "Start Simulation" button navigates to `/sim`
   - [ ] Features grid displays 6 cards
   - [ ] Navigation bar has correct links

2. **Simulation Dashboard**
   - [ ] Google Maps loads with dark theme
   - [ ] Fire heat map overlay renders (orange-red gradient)
   - [ ] Drone markers appear with correct heading arrows
   - [ ] InfoWindow shows drone details on click
   - [ ] Fire perimeter polygon displays

3. **Control Bar**
   - [ ] Start button initiates mock stream
   - [ ] Play/Pause toggles correctly
   - [ ] Reset clears state
   - [ ] Speed slider adjusts playback (0.25x-8x)
   - [ ] Settings panel expands with config options

4. **Right Panel Tabs**
   - [ ] **Metrics Tab**: Displays fire status, drone fleet, weather, sim info
   - [ ] **Telemetry Tab**: Shows drone cards with battery/water/position
   - [ ] **Guidance Tab**: Renders LLM guidance with priority zones/defensive lines
   - [ ] **Charts Tab**: 5 charts render (fire progression, containment, water, battery, wind)
   - [ ] **Logs Tab**: Log entries appear, export button downloads .txt

### Functional Tests

1. **State Management**
   - [ ] Zustand store persists across navigation
   - [ ] Ticks accumulate in history
   - [ ] Guidance history updates on LLM events

2. **SSE Stream**
   - [ ] Mock stream generates ~100 ticks over 60s
   - [ ] Ticks arrive at ~1 Hz
   - [ ] LLM guidance events trigger every 50 ticks
   - [ ] Stream completes at maxSteps

3. **Telemetry Processing**
   - [ ] Fire grid base64 decodes correctly
   - [ ] Drone positions update smoothly
   - [ ] Metrics calculations correct (burned area, containment)
   - [ ] Events array grows over time

4. **Map Interactions**
   - [ ] Zoom/pan works
   - [ ] Drone markers clickable
   - [ ] Fire overlay scales with map zoom
   - [ ] Legend displays correctly

### Performance Tests

1. **Rendering**
   - [ ] FPS stays above 30 during simulation
   - [ ] No memory leaks over 200+ ticks
   - [ ] Charts throttled to 10 Hz updates

2. **Data Handling**
   - [ ] 64x64 fire grid decodes in <10ms
   - [ ] Zustand state updates non-blocking
   - [ ] Canvas re-renders only on tick change

## 🔧 Troubleshooting

### Google Maps not loading
- Check `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` in `.env.local`
- Ensure API key has "Maps JavaScript API" enabled
- Check browser console for quota errors

### Mock stream not starting
- Open browser console for errors
- Verify `SimulationStream` class instantiated correctly
- Check `addLog` calls in ControlBar

### Charts not rendering
- Confirm `recharts` installed (`npm list recharts`)
- Check `chartData` array has valid numbers
- Verify `ResponsiveContainer` has non-zero height

## 🚢 Deployment

### Vercel (Recommended)

```bash
npm install -g vercel
vercel --prod
```

Add environment variables in Vercel dashboard.

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🎯 Future Enhancements

- [ ] Implement `/runs` browser with filtering/search
- [ ] Build `/compare` page with synchronized playback
- [ ] Add `/about` page with project abstract
- [ ] Connect to real Python backend via WebSocket
- [ ] Add CSV/JSON export for telemetry
- [ ] Implement run summary PDF generation
- [ ] Add user authentication for multi-user scenarios

## 📝 License

MIT License - See `../LICENSE` for details.

## 🙏 Acknowledgments

- **Gemini 2.0 Flash** for LLM strategic guidance
- **Stable-Baselines3** for PPO implementation
- **NOAA** for weather data
- **USGS** for terrain data
- **FIRMS** for historical fire records

## 📧 Contact

For questions or demo access, contact: [Your Email]

---

**Built for ISEF 2024 | AURORA Project | Hybrid RL+LLM Wildfire Suppression**
