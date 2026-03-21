const readEnvValue = (value: string | undefined): string => {
  return (value || "").trim();
};

const readNumberValue = (value: string | undefined, fallback: number): number => {
  const parsed = Number(readEnvValue(value));
  const valueAsNumber = Number.isFinite(parsed) ? parsed : fallback;
  return valueAsNumber;
};

export const publicEnv = {
  // Use direct property access so Next can expose these variables to the client bundle.
  googleMapsApiKey: readEnvValue(process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY),
  mapDefaults: {
    lat: readNumberValue(process.env.NEXT_PUBLIC_MAP_DEFAULT_LAT, 36.7783),
    lng: readNumberValue(process.env.NEXT_PUBLIC_MAP_DEFAULT_LNG, -119.4179),
    zoom: readNumberValue(process.env.NEXT_PUBLIC_MAP_DEFAULT_ZOOM, 12),
  },
};
