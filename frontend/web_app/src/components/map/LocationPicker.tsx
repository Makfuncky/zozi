"use client";

import { useMemo } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMapEvents, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { createPinIcon } from "./mapMarker";
import { parseLatLng, LatLng, formatLatLng, isWithinWorld } from "./parseLocation";

interface LocationPickerProps {
  value: string | LatLng | null | undefined;
  onChange: (lat: number, lng: number) => void;
  zoom?: number;
  height?: string;
  className?: string;
  markerColor?: string;
  popupText?: React.ReactNode;
}

function ClickToSet({ onChange }: { onChange: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onChange(Number(e.latlng.lat.toFixed(6)), Number(e.latlng.lng.toFixed(6)));
    },
  });
  return null;
}

function Recenter({ center }: { center: LatLng | null }) {
  const map = useMap();
  useMemo(() => {
    if (center) map.setView([center.lat, center.lng], map.getZoom(), { animate: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [center?.lat, center?.lng]);
  return null;
}

export default function LocationPicker({
  value,
  onChange,
  zoom = 15,
  height = "300px",
  className = "",
  markerColor,
  popupText,
}: LocationPickerProps) {
  const point = useMemo(() => parseLatLng(value), [value]);
  const valid = isWithinWorld(point);
  const icon = useMemo(
    () => createPinIcon({ color: markerColor, label: "Drop-off" }),
    [markerColor],
  );

  const center: [number, number] = valid && point ? [point.lat, point.lng] : [25.2048, 55.2708];

  return (
    <div className={`overflow-hidden rounded-xl border border-border ${className}`} style={{ height }}>
      <MapContainer
        center={center}
        zoom={valid ? zoom : 3}
        scrollWheelZoom={false}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ClickToSet onChange={onChange} />
        <Recenter center={point} />
        {valid && point && (
          <Marker
            position={[point.lat, point.lng]}
            icon={icon}
            draggable
            eventHandlers={{
              dragend(e) {
                const ll = (e.target as L.Marker).getLatLng();
                onChange(Number(ll.lat.toFixed(6)), Number(ll.lng.toFixed(6)));
              },
            }}
          >
            <Popup>
              {popupText ?? (
                <span className="text-xs">Drop-off: {formatLatLng(point)}</span>
              )}
            </Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  );
}
