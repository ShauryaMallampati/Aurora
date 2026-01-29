import { NextRequest, NextResponse } from 'next/server';

interface ResidentialZone {
  lat: number;
  lng: number;
  name: string;
  radius_meters: number;
}

const RESIDENTIAL_ZONES: ResidentialZone[] = [
  { lat: 36.8186, lng: -119.4242, name: 'Paradise Town', radius_meters: 2000 },
  { lat: 37.7749, lng: -122.4194, name: 'San Francisco', radius_meters: 15000 },
  { lat: 34.0522, lng: -118.2437, name: 'Los Angeles', radius_meters: 20000 },
  { lat: 39.5501, lng: -121.2313, name: 'Oroville', radius_meters: 5000 },
];

interface ProximityRequest {
  latitude: number;
  longitude: number;
  proximity_limit_m: number;
  manual_override: boolean;
}

interface ProximityResponse {
  safe: boolean;
  within_restricted_zone: boolean;
  nearest_zone: ResidentialZone | null;
  distance_to_zone_m: number | null;
  reason: string;
}

function calculateDistance(lat1: number, lng1: number, lat2: number, lng2: number): number {
  // Haversine for accurate distance
  const R = 6371000; // Earth radius (m)
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) *
      Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

export async function POST(request: NextRequest): Promise<NextResponse<ProximityResponse | { error: string }>> {
  try {
    const body: ProximityRequest = await request.json();

    // Validate input
    if (body.latitude === undefined || body.longitude === undefined) {
      return NextResponse.json({ error: 'Missing latitude or longitude' }, { status: 400 });
    }

    if (body.latitude < -90 || body.latitude > 90 || body.longitude < -180 || body.longitude > 180) {
      return NextResponse.json({ error: 'Invalid coordinates' }, { status: 400 });
    }

    const proximityLimit = body.proximity_limit_m || 200;

    // Check proximity to residential zones
    let nearestZone: ResidentialZone | null = null;
    let minDistance = Infinity;
    let withinRestrictedZone = false;

    for (const zone of RESIDENTIAL_ZONES) {
      const distance = calculateDistance(body.latitude, body.longitude, zone.lat, zone.lng);

      if (distance < minDistance) {
        minDistance = distance;
        nearestZone = zone;
      }

      // Check if within zone + buffer
      if (distance < zone.radius_meters + proximityLimit) {
        withinRestrictedZone = true;
        break;
      }
    }

    // Determine safety
    const safe = !withinRestrictedZone || body.manual_override;

    let reason = '';
    if (withinRestrictedZone && !body.manual_override) {
      reason = `Too close to ${nearestZone?.name} (${(minDistance / 1000).toFixed(2)}km away). Minimum distance: ${proximityLimit}m`;
    } else if (withinRestrictedZone && body.manual_override) {
      reason = `Override active: Can operate near ${nearestZone?.name}`;
    } else {
      reason = `Safe to operate. Nearest zone: ${nearestZone?.name} (${(minDistance / 1000).toFixed(2)}km away)`;
    }

    return NextResponse.json({
      safe,
      within_restricted_zone: withinRestrictedZone,
      nearest_zone: nearestZone,
      distance_to_zone_m: minDistance === Infinity ? null : Math.round(minDistance),
      reason,
    });
  } catch (error) {
    console.error('Safety proximity check error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  const lat = request.nextUrl.searchParams.get('lat');
  const lng = request.nextUrl.searchParams.get('lng');
  const limit = request.nextUrl.searchParams.get('limit') || '200';
  const override = request.nextUrl.searchParams.get('override') === 'true';

  if (!lat || !lng) {
    return NextResponse.json({ error: 'Missing lat or lng query params' }, { status: 400 });
  }

  try {
    const latitude = parseFloat(lat);
    const longitude = parseFloat(lng);
    const proximityLimit = parseInt(limit);

    const result = await POST(
      new NextRequest(new URL('http://localhost'), {
        method: 'POST',
        body: JSON.stringify({
          latitude,
          longitude,
          proximity_limit_m: proximityLimit,
          manual_override: override,
        }),
      })
    );

    return result;
  } catch (error) {
    console.error('GET request error:', error);
    return NextResponse.json({ error: 'Invalid parameters' }, { status: 400 });
  }
}
