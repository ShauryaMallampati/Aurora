export interface PresetScenario {
  id: string;
  name: string;
  year: number;
  location: string;
  acres: number;
  lat: number;
  lng: number;
  initialRadius: number;
  weather: {
    windSpeed: number;
    windDir: number;
    temp: number;
    humidity: number;
  };
}

export const PRESET_SCENARIOS: PresetScenario[] = [
  {
    id: "camp-fire-2018",
    name: "Camp Fire",
    year: 2018,
    location: "Paradise, CA",
    acres: 153336,
    lat: 39.8103,
    lng: -121.4372,
    initialRadius: 14,
    weather: { windSpeed: 9.4, windDir: 40, temp: 31, humidity: 0.18 },
  },
  {
    id: "dixie-fire-2021",
    name: "Dixie Fire",
    year: 2021,
    location: "Northern California",
    acres: 963405,
    lat: 40.211,
    lng: -121.0471,
    initialRadius: 24,
    weather: { windSpeed: 8.1, windDir: 305, temp: 34, humidity: 0.22 },
  },
  {
    id: "august-complex-2020",
    name: "August Complex",
    year: 2020,
    location: "Mendocino NF, CA",
    acres: 1032648,
    lat: 39.7761,
    lng: -122.8957,
    initialRadius: 26,
    weather: { windSpeed: 7.9, windDir: 280, temp: 33, humidity: 0.2 },
  },
  {
    id: "bootleg-fire-2021",
    name: "Bootleg Fire",
    year: 2021,
    location: "Fremont-Winema NF, OR",
    acres: 413715,
    lat: 42.629,
    lng: -121.0759,
    initialRadius: 20,
    weather: { windSpeed: 10.2, windDir: 300, temp: 32, humidity: 0.17 },
  },
  {
    id: "east-troublesome-2020",
    name: "East Troublesome Fire",
    year: 2020,
    location: "Grand County, CO",
    acres: 193812,
    lat: 40.2456,
    lng: -106.0514,
    initialRadius: 16,
    weather: { windSpeed: 11.4, windDir: 255, temp: 24, humidity: 0.16 },
  },
  {
    id: "caldor-fire-2021",
    name: "Caldor Fire",
    year: 2021,
    location: "El Dorado County, CA",
    acres: 221835,
    lat: 38.6945,
    lng: -120.3181,
    initialRadius: 18,
    weather: { windSpeed: 8.8, windDir: 292, temp: 30, humidity: 0.19 },
  },
];

const SCENARIO_ID_ALIASES = new Map<string, string>(
  PRESET_SCENARIOS.flatMap((scenario) => {
    const shortId = scenario.id.replace("-fire-", "-");
    return [
      [scenario.id, scenario.id],
      [shortId, scenario.id],
    ];
  }),
);

const PRESET_SCENARIO_LOOKUP = new Map(
  PRESET_SCENARIOS.flatMap((scenario) => [
    [scenario.id, scenario],
    [scenario.id.replace("-fire-", "-"), scenario],
  ]),
);

export function normalizeScenarioId(scenarioId?: string): string | null {
  if (!scenarioId) {
    return null;
  }

  return SCENARIO_ID_ALIASES.get(scenarioId) ?? scenarioId;
}

export function findPresetScenarioById(scenarioId?: string): PresetScenario | null {
  if (!scenarioId) {
    return null;
  }

  return PRESET_SCENARIO_LOOKUP.get(normalizeScenarioId(scenarioId) ?? scenarioId) ?? null;
}

export function formatScenarioLabel(scenarioId: string): string {
  if (scenarioId === "random") {
    return "Auto-selected scenario";
  }

  if (scenarioId === "custom") {
    return "Custom fire";
  }

  const scenario = findPresetScenarioById(scenarioId);
  if (scenario) {
    return `${scenario.name} (${scenario.year})`;
  }

  return scenarioId
    .split("-")
    .map((part) =>
      /^\d+$/.test(part) ? part : part.charAt(0).toUpperCase() + part.slice(1),
    )
    .join(" ");
}
