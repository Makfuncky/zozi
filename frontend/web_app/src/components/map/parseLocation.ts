export interface LatLng {
  lat: number;
  lng: number;
}

/** Parse a location value coming from the backend / UI into {lat, lng}.
 *
 * Accepts:
 *  - the stored "lat,lon" string (order.delivery_location)
 *  - a {lat, lng} object
 *  - a [lat, lng] tuple
 *  - a {latitude, longitude} object (geolocation payloads)
 * Returns null when nothing usable is present.
 */
export function parseLatLng(
  value: unknown,
): LatLng | null {
  if (value == null || value === "") return null;

  // "lat,lon" string
  if (typeof value === "string") {
    const parts = value.split(",").map((p) => Number(p.trim()));
    if (parts.length >= 2 && Number.isFinite(parts[0]) && Number.isFinite(parts[1])) {
      return { lat: parts[0], lng: parts[1] };
    }
    return null;
  }

  // tuple
  if (Array.isArray(value) && value.length >= 2) {
    const lat = Number(value[0]);
    const lng = Number(value[1]);
    if (Number.isFinite(lat) && Number.isFinite(lng)) return { lat, lng };
  }

  if (typeof value === "object") {
    const obj = value as Record<string, unknown>;
    if (obj.lat != null && obj.lng != null) {
      const lat = Number(obj.lat);
      const lng = Number(obj.lng);
      if (Number.isFinite(lat) && Number.isFinite(lng)) return { lat, lng };
    }
    if (obj.latitude != null && obj.longitude != null) {
      const lat = Number(obj.latitude);
      const lng = Number(obj.longitude);
      if (Number.isFinite(lat) && Number.isFinite(lng)) return { lat, lng };
    }
  }

  return null;
}

export function latLngToString(p: LatLng | null): string {
  if (!p) return "";
  return `${p.lat.toFixed(6)},${p.lng.toFixed(6)}`;
}

export function isWithinWorld(p: LatLng | null): boolean {
  if (!p) return false;
  return p.lat >= -90 && p.lat <= 90 && p.lng >= -180 && p.lng <= 180;
}

/** Returns a short human readable coordinate string for display. */
export function formatLatLng(p: LatLng | null): string {
  if (!p) return "—";
  return `${p.lat.toFixed(5)}, ${p.lng.toFixed(5)}`;
}
