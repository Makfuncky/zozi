/**
 * Geo helpers for the mobile app.
 * Powers the dependency-free interactive map picker (OpenStreetMap static tiles
 * + Web Mercator tap math) used in checkout and elsewhere.
 */

export interface LatLng {
  lat: number;
  lng: number;
}

/** Sensible default map centers per supported country (falls back to Oman). */
export const COUNTRY_CENTERS: Record<string, LatLng> = {
  OM: { lat: 23.588, lng: 58.3829 }, // Muscat
  AE: { lat: 25.2048, lng: 55.2708 }, // Dubai
  SA: { lat: 24.7136, lng: 46.6753 }, // Riyadh
  QA: { lat: 25.2854, lng: 51.531 }, // Doha
  KW: { lat: 29.3759, lng: 47.9774 }, // Kuwait City
  BH: { lat: 26.2285, lng: 50.586 }, // Manama
  PK: { lat: 24.8607, lng: 67.0011 }, // Karachi
  EG: { lat: 30.0444, lng: 31.2357 }, // Cairo
  IN: { lat: 28.6139, lng: 77.209 }, // New Delhi
  US: { lat: 38.9072, lng: -77.0369 }, // Washington
  GB: { lat: 51.5074, lng: -0.1278 }, // London
};

export function defaultCenterForCountry(country?: string | null): LatLng {
  if (country && COUNTRY_CENTERS[country.toUpperCase()]) {
    return COUNTRY_CENTERS[country.toUpperCase()];
  }
  return COUNTRY_CENTERS.OM;
}

export function parseLatLng(value?: string | null): LatLng | null {
  if (!value) return null;
  const parts = String(value)
    .split(",")
    .map((p) => parseFloat(p.trim()));
  if (parts.length === 2 && Number.isFinite(parts[0]) && Number.isFinite(parts[1])) {
    return { lat: parts[0], lng: parts[1] };
  }
  return null;
}

export function formatLatLng(point: LatLng): string {
  // Keep precision reasonable for the backend's "lat,lng" convention.
  return `${point.lat.toFixed(6)},${point.lng.toFixed(6)}`;
}

const TILE_SIZE = 256;

function lngToWorldX(lng: number, worldSize: number): number {
  return ((lng + 180) / 360) * worldSize;
}

function latToWorldY(lat: number, worldSize: number): number {
  const latRad = (lat * Math.PI) / 180;
  return ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * worldSize;
}

function worldXToLng(x: number, worldSize: number): number {
  return (x / worldSize) * 360 - 180;
}

function worldYToLat(y: number, worldSize: number): number {
  const n = Math.PI - (2 * Math.PI * y) / worldSize;
  return (180 / Math.PI) * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)));
}

function clampLat(lat: number): number {
  return Math.max(-85.05, Math.min(85.05, lat));
}

function clampLng(lng: number): number {
  return Math.max(-180, Math.min(180, lng));
}

/**
 * Convert a tap position (px, py) relative to a viewport (vw x vh) that is
 * centered on `center` at the given `zoom`, into a geographic coordinate.
 * Uses the standard Web Mercator projection (same as OSM raster tiles).
 */
export function pixelToLatLng(
  center: LatLng,
  zoom: number,
  px: number,
  py: number,
  vw: number,
  vh: number,
): LatLng {
  const worldSize = TILE_SIZE * Math.pow(2, zoom);
  const centerX = lngToWorldX(center.lng, worldSize);
  const centerY = latToWorldY(center.lat, worldSize);
  const tapX = centerX + (px - vw / 2);
  const tapY = centerY + (py - vh / 2);
  return {
    lat: clampLat(worldYToLat(tapY, worldSize)),
    lng: clampLng(worldXToLng(tapX, worldSize)),
  };
}

/** Build an OpenStreetMap static-map image URL centered on `center`. */
export function staticMapUrl(center: LatLng, zoom: number, width = 600, height = 300): string {
  const c = `${center.lat},${center.lng}`;
  return `https://staticmap.openstreetmap.de/staticmap.php?center=${c}&zoom=${zoom}&size=${width}x${height}&maptype=mapnik&markers=${c},red-pushpin&scale=2`;
}
