export const posterSectionLinks = [
  {
    href: "/#overview",
    label: "Overview",
    note: "Mission, architecture, and measurable impact at a glance.",
  },
  {
    href: "/#evidence",
    label: "Impact",
    note: "Benchmark deltas, operational outcomes, and reliability signal.",
  },
  {
    href: "/#method",
    label: "System",
    note: "How training, guidance cadence, and simulation runtime connect.",
  },
  {
    href: "/#sources",
    label: "Operations",
    note: "Command modules for sim, runs, export, scenarios, and analytics.",
  },
];

export const secondaryRouteLinks = [
  {
    href: "/sim",
    label: "Simulator",
    note: "Live tactical playback with fire perimeter, drones, and telemetry overlays.",
  },
  {
    href: "/runs",
    label: "Runs",
    note: "Run archive with reproducible comparisons and episode-level evidence.",
  },
  {
    href: "/export",
    label: "Export",
    note: "Build handoff-ready evidence packages for judges, teams, and stakeholders.",
  },
  {
    href: "/scenarios",
    label: "Scenarios",
    note: "Historical fire library plus custom ignition and weather setup.",
  },
  {
    href: "/dashboard",
    label: "Dashboard",
    note: "Training and evaluation analytics, trend tracking, and KPI summary.",
  },
  {
    href: "/lab",
    label: "Lab",
    note: "Experimental workspace for rapid iteration and controlled tests.",
  },
  {
    href: "/costs",
    label: "Costs",
    note: "Suppression and impact economics for baseline vs hybrid policy.",
  },
];

export const heroStats = [
  {
    label: "Real fire scenarios",
    value: "116,337",
    detail: "InterAgency Fire Perimeter History (1308-2024).",
  },
  {
    label: "Completed episodes",
    value: "53,055",
    detail: "Three models across four random seeds.",
  },
  {
    label: "Baseline return",
    value: "34.57",
    detail: "PPO control without LLM guidance.",
  },
  {
    label: "Hybrid return",
    value: "41.84",
    detail: "Qwen 2.5-3B guidance every 50 steps.",
  },
];

export const evidenceHighlights = [
  {
    label: "Headline lift",
    value: "+21.03%",
    detail: "Average final return improvement over PPO baseline.",
  },
  {
    label: "Hard-scenario lift",
    value: "+49.86%",
    detail: "The gains concentrate where coordination is hardest.",
  },
  {
    label: "Easy-scenario lift",
    value: "0.00%",
    detail: "No change where PPO was already strong.",
  },
];

export const resultRows = [
  {
    metric: "Average final return",
    baseline: "34.57",
    hybrid: "41.84",
    note: "The main benchmark result from the stored evaluation runs.",
  },
  {
    metric: "Easy seeds",
    baseline: "42.68 / 41.99",
    hybrid: "No change",
    note: "The hybrid model does not move easy cases that PPO already solves.",
  },
  {
    metric: "Hard seeds",
    baseline: "17.34 / 36.26",
    hybrid: "23.83 / 58.85",
    note: "The biggest gains appear on the more difficult scenarios.",
  },
  {
    metric: "Extended variant",
    baseline: "PPO",
    hybrid: "Qwen 2.5-7B: 39.08",
    note: "The larger model improves over PPO, but trails the 3B hybrid.",
  },
];

export const methodSteps = [
  "Historical wildfire perimeters are paired with NOAA weather and USGS terrain to define the simulation state.",
  "A PPO policy handles low-level movement and suppression control.",
  "Qwen 2.5-3B adds higher-level guidance every 50 steps for strategic coordination.",
  "Runs, checkpoints, and logs stay traceable so every benchmark claim can be reproduced.",
];

export const sourceCards = [
  {
    label: "Fire data",
    title: "116,337 real historical fires",
    detail: "InterAgency Fire Perimeter History (1308-2024), used as the scenario backbone.",
  },
  {
    label: "Weather",
    title: "NOAA inputs",
    detail: "Temperature, wind speed, wind direction, and humidity are folded into the state.",
  },
  {
    label: "Terrain",
    title: "USGS 3DEP elevation",
    detail: "Terrain information adds slope and geography to the decision context.",
  },
  {
    label: "Runs",
    title: "53,055 completed episodes",
    detail: "Stored metrics and evaluation logs support the headline comparison.",
  },
];
