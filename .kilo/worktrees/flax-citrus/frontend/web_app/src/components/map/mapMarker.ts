import L from "leaflet";

export interface PinOptions {
  color?: string;
  label?: string;
}

/** Build an inline SVG pin as a Leaflet divIcon so we never depend on the
 *  bundled marker PNGs (which break under webpack/Next.js asset handling). */
export function createPinIcon({ color = "#e11d48", label }: PinOptions = {}): L.DivIcon {
  const html = `
    <div style="position:relative;transform:translate(-50%,-100%);">
      <svg width="32" height="42" viewBox="0 0 32 42" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M16 0C7.163 0 0 7.163 0 16c0 11.5 16 26 16 26s16-14.5 16-26C32 7.163 24.837 0 16 0z" fill="${color}"/>
        <circle cx="16" cy="16" r="6" fill="#ffffff"/>
      </svg>
      ${label ? `<span style="position:absolute;top:42px;left:50%;transform:translateX(-50%);white-space:nowrap;background:#0f172a;color:#fff;font-size:10px;padding:2px 6px;border-radius:6px;font-family:system-ui,sans-serif;">${label}</span>` : ""}
    </div>`;
  return L.divIcon({
    html,
    className: "zozi-pin",
    iconSize: [32, 42],
    iconAnchor: [16, 42],
    popupAnchor: [0, -40],
  });
}
