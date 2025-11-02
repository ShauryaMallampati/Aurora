# Phase 1 UI Productization - Implementation Plan

## Overview
8 interconnected frontend/backend tasks to transform AURORA into a competition-ready platform. Estimated effort: **14-18 hours total**.

## Task Status & Dependencies

### ✅ Task 1.1: Split View PPO vs Hybrid Comparison
**Status**: COMPLETE (90% - minor tweaks needed)
**Dependencies**: None (foundational)
**Deliverable**: Real-time comparison with synchronized timeline scrubber
**Key Metrics**:
- Containment Time Reduction %
- Water Efficiency %
- Area Saved (hectares)
- Success Rate (% fires contained)

**Current Implementation**:
- ✅ `SplitViewComparison.tsx` displays metrics
- ✅ `runsDataLoader.ts` computes comparison metrics correctly
- ✅ Synchronized scrubber at bottom
- ✅ Mock data generator produces realistic comparisons
- ⚠️ **Todo**: Wire to real `/api/runs` backend endpoints

**Next Steps**:
1. Create `/api/runs` Express routes to serve SimulationRun data
2. Create `/api/runs/compare` endpoint for matched pairs
3. Update SplitViewComparison to fetch real data instead of mock
4. Add error handling & loading states

---

### 🔄 Task 1.2: Experiment Lab Backend Connection
**Status**: NOT STARTED
**Dependencies**: Task 1.1 (metrics computation)
**Effort**: 3-4 hours
**Deliverable**: Live experiment runner with 4 mini-charts

**Architecture**:
```
Frontend (Lab page)
    ↓ POST {model, seed, episodes, llm_cadence, max_steps, noise}
Backend /api/run_experiment
    ↓ Call train_manager.py with parameters
Python train_manager.py
    ↓ Execute training, store results
Backend stores to:
    - results/aurora_runs.json (full telemetry)
    - results/aurora_runs.csv (summary stats)
    ↓
Frontend fetches updated metrics
    ↓ Updates 4 charts in real-time
```

**Implementation Checklist**:
- [ ] Create `train_manager.py` wrapper (if not exists)
- [ ] Implement `/api/run_experiment` POST route
- [ ] Accept payload: `{ model, seed, episodes, llm_cadence, max_steps, noise }`
- [ ] Stream execution status back to frontend
- [ ] Persist results to `results/aurora_runs.json` + CSV
- [ ] Create Lab page 4-chart dashboard
  - [ ] Episode return over seed (line chart)
  - [ ] Completion rate vs cadence (bar chart)
  - [ ] Idle steps distribution (histogram)
  - [ ] LLM latency histogram

---

### 🔄 Task 1.3: Run History Save, Pin & Replay
**Status**: NOT STARTED
**Dependencies**: Task 1.1 (metrics)
**Effort**: 1.5-2 hours
**Deliverable**: Persistent run history with replay & comparison

**Implementation Checklist**:
- [ ] Extend Zustand store: `runsHistory` state
- [ ] Add localStorage persistence: `saveRunHistory()`, `loadRunHistory()`
- [ ] Create Run History page at `/runs`
- [ ] Display runs in sortable table:
  - [ ] Run ID (clickable)
  - [ ] Model type (PPO / Hybrid)
  - [ ] Seed
  - [ ] Timestamp
  - [ ] Key metrics (area saved, time improvement, etc.)
  - [ ] Star icon (pin/favorite)
- [ ] "Pin Best Run" button → saves to localStorage with ⭐ indicator
- [ ] "Replay" button → loads config, routes to `/sim?config=<runId>`
- [ ] "Compare Two Runs" modal for side-by-side comparison
- [ ] Visual indicators for pinned runs (gold background)

---

### 🔄 Task 1.4: Custom Fire Creator Backend Integration
**Status**: NOT STARTED (UI exists, backend needed)
**Dependencies**: Task 1.1 (metrics)
**Effort**: 1.5-2 hours
**Deliverable**: Interactive fire creation → immediate simulation

**Implementation Checklist**:
- [ ] Create `/api/scenarios/create` POST endpoint
  - [ ] Accept: `{ lat, lon, wind, ignition_point, num_drones }`
  - [ ] Validate coordinates (CA bounds)
  - [ ] Initialize fire grid from USGS elevation
  - [ ] Create fresh environment
  - [ ] Return `run_id`
- [ ] Update `handleCreateFire()` in Scenarios page:
  - [ ] POST to `/api/scenarios/create`
  - [ ] Show toast: "Scenario created — Open in Split View"
  - [ ] Add button: "View in Simulation" → routes to `/sim?scenario=<scenarioId>`
- [ ] Backend: Auto-run both PPO and Hybrid agents
- [ ] Stream results to `/results/aurora_runs.csv`

---

### 🔄 Task 1.5: Drone "Why" Popover — Explainability
**Status**: NOT STARTED
**Dependencies**: None (independent feature)
**Effort**: 2-3 hours
**Deliverable**: Transparent drone decision explainability

**Implementation Checklist**:
- [ ] Create `/logs/drone_actions.jsonl` logging format:
  ```json
  { "drone": "d0", "step": 42, "action": "suppress", "reason": "fire detected at bearing 45°, intensity >0.7", "confidence": 0.87, "alt_actions": ["scout", "move"] }
  ```
- [ ] Integrate logging into `MapStage.tsx` drone rendering
- [ ] Create `DroneActionPopover.tsx` component:
  - [ ] Trigger on drone hover
  - [ ] Display last 3 actions with reasons
  - [ ] Color-code by action:
    - 🔴 Red: suppress (high intensity)
    - 🟡 Yellow: scout (low confidence)
    - 🟢 Green: move (repositioning)
    - 🔵 Blue: idle/loiter
  - [ ] Show confidence score 0-100%
  - [ ] Animate on appear
- [ ] Update `MapStage` to attach popover to drones
- [ ] **Judges Impact**: Direct evidence of AI interpretability

---

### 🔄 Task 1.6: Safety Mode & Manual Override
**Status**: NOT STARTED
**Dependencies**: None (independent)
**Effort**: 2-3 hours
**Deliverable**: Trustworthy AI with safety guarantees

**Implementation Checklist**:
- [ ] Add "Safety-First Mode" toggle to ControlBar
- [ ] When ON:
  - [ ] Hard-limit drone proximity to residential cells: distance = 0
  - [ ] Veto LLM proposals that predict growth into towns
  - [ ] Cap water usage to conserve reserves (80% max per step)
  - [ ] Display "🛡️ Safety Mode ON" indicator
- [ ] Add "Redirect Drone" button:
  - [ ] Click button → show crosshair cursor
  - [ ] Click target cell on map
  - [ ] Send command to backend
  - [ ] Backend validates: within bounds, not in residential
  - [ ] Drone moves to target
- [ ] Log all overrides to `/logs/manual_interventions.jsonl`:
  ```json
  { "timestamp": "2024-11-01T...", "intervention": "redirect", "drone": "d0", "from": [x,y], "to": [x',y'], "reason": "threat to town" }
  ```
- [ ] **Judges Impact**: Addresses AI safety concerns

---

### 🔄 Task 1.7: Offline Mode Export
**Status**: NOT STARTED
**Dependencies**: All tasks (final deliverable)
**Effort**: 1-2 hours
**Deliverable**: Self-contained offline backup kit

**Implementation Checklist**:
- [ ] Run `next export` (or equivalent static build)
  - [ ] Output to `aurora_offline_demo/`
- [ ] Verify all assets included:
  - [ ] `index.html`
  - [ ] `css/` (Tailwind output)
  - [ ] `js/` (Next.js bundles)
  - [ ] `public/` (images, fonts)
- [ ] Record 2 demo videos (OBS or equivalent):
  - [ ] **Video 1**: PPO vs Hybrid on Camp Fire scenario (30-60s)
    - Show split view comparison
    - Highlight metrics delta
    - Showcase synchronized scrubber
  - [ ] **Video 2**: Safety Mode + drone popovers demo (30-60s)
    - Toggle safety mode
    - Hover over drones to show rationales
    - Click redirect button
- [ ] Create `aurora_offline_demo/` structure:
  ```
  aurora_offline_demo/
  ├── index.html
  ├── css/
  ├── js/
  ├── demo_video_ppo_vs_hybrid.mp4
  ├── demo_video_safety_demo.mp4
  └── README.txt (instructions)
  ```
- [ ] Test: Open `index.html` in browser with NO internet → verify works

---

### 🔄 Task 1.8: Run History Visualization Dashboard
**Status**: NOT STARTED
**Dependencies**: Task 1.2, 1.3 (run history data)
**Effort**: 1.5-2 hours
**Deliverable**: Visual run analytics dashboard

**Implementation Checklist**:
- [ ] Create `/runs` page (if not exists)
- [ ] Add 3 mini-charts:
  - [ ] **Line Chart**: Return over seed (color by model: blue=PPO, purple=Hybrid)
    - X-axis: Seed (1-50)
    - Y-axis: Avg return
    - Lines for each model
  - [ ] **Bar Chart**: Completion rate (side-by-side bars)
    - X-axis: Model type
    - Y-axis: % runs completed
    - Blue vs purple
  - [ ] **Box Plot**: Idle steps distribution
    - X-axis: Model type
    - Y-axis: # idle steps
    - Show quartiles + outliers
- [ ] Add filter dropdowns:
  - [ ] "Show only best seed" (highlight max return)
  - [ ] "Highlight latest" (most recent run)
  - [ ] "Filter by model" (PPO / Hybrid / Both)
- [ ] Hover interactions:
  - [ ] Show full run details (seed, cadence, timestamp, all metrics)
  - [ ] Click point → routes to run in Split View
- [ ] Visual polish:
  - [ ] Responsive grid layout
  - [ ] Legend with color coding
  - [ ] Grid lines for readability

---

## Backend API Requirements

### Routes to Create

```typescript
// 1.1 - Run Management
GET  /api/runs                      // List all runs
GET  /api/runs?model=ppo            // Filter by model
GET  /api/runs/:runId               // Get specific run
GET  /api/runs/compare?scenario=...&seed=... // Get PPO+Hybrid pair

// 1.2 - Experiment Execution
POST /api/run_experiment            // Trigger training
  payload: { model, seed, episodes, llm_cadence, max_steps, noise }
  response: { run_id, job_id, status }
GET  /api/run_experiment/:jobId     // Poll job status

// 1.4 - Scenario Creation
POST /api/scenarios/create          // Create custom fire
  payload: { lat, lon, wind, ignition_point, num_drones }
  response: { run_id, scenario_id }

// 1.3 - Run History (frontend localStorage for MVP)
// No backend needed - use Zustand + localStorage

// 1.5 - Action Logging (streamed from simulation)
// Handled by logging within simulation

// 1.6 - Manual Override
POST /api/drone/redirect            // Manual drone command
  payload: { drone_id, target_x, target_y }
  response: { success, message }
```

---

## Timeline & Effort Distribution

| Task | Priority | Effort | Dependency |
|------|----------|--------|-----------|
| 1.1 ✅ Split View | P0 | 2-3h | None |
| 1.2 Lab | P1 | 3-4h | 1.1 |
| 1.3 History | P1 | 1.5-2h | 1.1 |
| 1.4 Custom Fire | P2 | 1.5-2h | 1.1 |
| 1.5 Drone Why | P1 | 2-3h | None |
| 1.6 Safety | P2 | 2-3h | None |
| 1.7 Offline | P3 | 1-2h | All |
| 1.8 Dashboard | P2 | 1.5-2h | 1.2, 1.3 |
| **Total** | — | **14-18h** | — |

---

## Recommended Implementation Order

1. **Fix 1.1** - Wire real backend (30 min)
2. **Task 1.3** - Run history (localStorage MVP) (1.5h)
3. **Task 1.5** - Drone popovers (high judge impact) (2-3h)
4. **Task 1.2** - Lab backend (3-4h)
5. **Task 1.8** - Dashboard (1.5-2h)
6. **Task 1.4** - Custom fire (1.5-2h)
7. **Task 1.6** - Safety mode (2-3h)
8. **Task 1.7** - Offline export (1-2h, done last)

---

## Key Judge Criteria Addressed

✅ **Explainability** (1.5, 1.6) - Transparent drone decisions + safety rationales
✅ **Safety** (1.6) - Manual overrides + residential protection
✅ **Performance** (1.1, 1.2) - Live metrics showing 15%+ improvements
✅ **Reproducibility** (1.3, 1.8) - Full run history + replay capability
✅ **User Experience** (All) - Interactive, responsive, beautiful UI

---

## Success Criteria

- ✅ All 8 tasks implemented and functional
- ✅ No console errors or TypeScript warnings
- ✅ Responsive design on mobile/tablet/desktop
- ✅ All metrics computed correctly (verified manually)
- ✅ Offline HTML demo opens in browser without internet
- ✅ Judge can easily understand each feature in <5 min demos
