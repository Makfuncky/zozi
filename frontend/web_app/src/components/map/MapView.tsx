"use client";

import { useMemo } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { createPinIcon } from "./mapMarker";
import { parseLatLng, LatLng, formatLatLng, isWithinWorld } from "./parseLocation";

interface MapViewProps {
  location: string | LatLng | null | undefined;
  zoom?: number;
  height?: string;
  className?: string;
  markerColor?: string;
  markerLabel?: string;
  popupText?: React.ReactNode;
  emptyText?: string;
}

/** Internal helper that re-centers the map whenever the location changes. */
function Recenter({ center }: { center: LatLng }) {
  const map = useMap();
  useMemo(() => {
    map.setView([center.lat, center.lng], map.getZoom(), { animate: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [center.lat, center.lng]);
  return null;
}

export default function MapView({
  location,
  zoom = 15,
  height = "260px",
  className = "",
  markerColor,
  markerLabel,
  popupText,
  emptyText = "No location provided",
}: MapViewProps) {
  const point = useMemo(() => parseLatLng(location), [location]);
  const valid = isWithinWorld(point);
  const icon = useMemo(
    () => createPinIcon({ color: markerColor, label: markerLabel }),
    [markerColor, markerLabel],
  );

  if (!valid || !point) {
    return (
      <div
        className={`flex items-center justify-center rounded-xl border border-border bg-surface-2 text-xs text-text-faint ${className}`}
        style={{ height }}
      >
        <span>{emptyText}</span>
      </div>
    );
  }

  const center: [number, number] = [point.lat, point.lng];

  return (
    <div className={`overflow-hidden rounded-xl border border-border ${className}`} style={{ height }}>
      <MapContainer
        center={center}
        zoom={zoom}
        scrollWheelZoom={false}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Recenter center={point} />
        <Marker position={center} icon={icon}>
          <Popup>
            {popupText ?? (
              <span className="text-xs">Delivery location: {formatLatLng(point)}</span>
            )}
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}
