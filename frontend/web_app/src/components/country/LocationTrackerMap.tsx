"use client";

import { useState, useEffect } from "react";
import { MapPin, Navigation, Clock, Package, Shield } from "@/lib/icons";

interface Location {
  id: number;
  name: string;
  type: "shop" | "warehouse" | "partner";
  lat: number;
  lng: number;
  status: "active" | "inactive";
}

interface LocationTrackerMapProps {
  locations: Location[];
  showOnlyActive?: boolean;
}

export default function LocationTrackerMap({ locations, showOnlyActive = true }: LocationTrackerMapProps) {
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);

  const filteredLocations = showOnlyActive
    ? locations.filter((loc) => loc.status === "active")
    : locations;

  return (
    <div className="border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MapPin className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-bold text-text">Location Tracker</h3>
        </div>
        <span className="text-xs text-text-muted">
          {filteredLocations.length} locations
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {filteredLocations.map((loc) => {
          const Icon = loc.type === "shop" ? Package : loc.type === "warehouse" ? Navigation : Shield;
          return (
            <div
              key={loc.id}
              className={`border rounded-lg p-3 cursor-pointer transition ${
                selectedLocation?.id === loc.id
                  ? "border-primary bg-primary/5"
                  : "border-border hover:bg-surface-2/50"
              }`}
              onClick={() => setSelectedLocation(loc)}
            >
              <div className="flex items-center gap-2">
                <Icon className="h-4 w-4 text-primary" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-text">{loc.name}</p>
                  <p className="text-[10px] text-text-muted capitalize">{loc.type}</p>
                </div>
                <div className={`w-2 h-2 rounded-full ${
                  loc.status === "active" ? "bg-success" : "bg-danger"
                }`} />
              </div>
            </div>
          );
        })}
      </div>

      {selectedLocation && (
        <div className="mt-4 p-3 bg-surface-1 rounded-lg">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-text-muted">Coordinates:</span>
              <p className="font-mono text-text">
                {selectedLocation.lat.toFixed(4)}, {selectedLocation.lng.toFixed(4)}
              </p>
            </div>
            <div>
              <span className="text-text-muted">Status:</span>
              <p className={selectedLocation.status === "active" ? "text-success" : "text-danger"}>
                {selectedLocation.status}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


