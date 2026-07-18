"use client";

import { Button } from "@/components/ui/Button";

import { useState, useEffect, useRef, useCallback } from "react";
import { MapPin, Plus, Trash2, Edit3, Save, X, Globe, Search } from "@/lib/icons";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";

interface City {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  population?: number;
  is_capital?: boolean;
}

interface CountryMapViewProps {
  countryCode: string;
  cities: City[];
  onCitiesChange: (cities: City[]) => void;
}

// Simple SVG map component with city markers
export default function CountryMapView({ countryCode, cities, onCitiesChange }: CountryMapViewProps) {
  const addToast = useToastStore((state) => state.addToast);
  const [isAddingCity, setIsAddingCity] = useState(false);
  const [editingCity, setEditingCity] = useState<City | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [newCityName, setNewCityName] = useState("");
  const [newCityLat, setNewCityLat] = useState("");
  const [newCityLng, setNewCityLng] = useState("");
  const [newCityPopulation, setNewCityPopulation] = useState("");
  const [selectedCity, setSelectedCity] = useState<City | null>(null);
  
  const mapRef = useRef<HTMLDivElement>(null);

  // Handle map click to add new city
  const handleMapClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!isAddingCity) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 360 - 180; // Normalize to -180 to 180
    const y = 90 - ((e.clientY - rect.top) / rect.height) * 180; // Normalize to 90 to -90
    
    setNewCityLat(y.toFixed(4));
    setNewCityLng(x.toFixed(4));
    setIsAddingCity(false);
  }, [isAddingCity]);

  const handleAddCity = async () => {
    if (!newCityName.trim() || !newCityLat || !newCityLng) return;
    
    const city: City = {
      id: `city_${Date.now()}`,
      name: newCityName.trim(),
      latitude: parseFloat(newCityLat),
      longitude: parseFloat(newCityLng),
      population: newCityPopulation ? parseInt(newCityPopulation) : undefined,
      is_capital: false,
    };
    
    onCitiesChange([...cities, city]);
    setNewCityName("");
    setNewCityLat("");
    setNewCityLng("");
    setNewCityPopulation("");
    addToast(`City "${city.name}" added`, "success");
  };

  const handleUpdateCity = async () => {
    if (!editingCity || !newCityName.trim()) return;
    
    const updatedCity: City = {
      ...editingCity,
      name: newCityName.trim(),
      population: newCityPopulation ? parseInt(newCityPopulation) : editingCity.population,
    };
    
    onCitiesChange(cities.map(c => c.id === editingCity.id ? updatedCity : c));
    setEditingCity(null);
    setSelectedCity(null);
    addToast(`City "${updatedCity.name}" updated`, "success");
  };

  const handleDeleteCity = (cityId: string) => {
    onCitiesChange(cities.filter(c => c.id !== cityId));
    addToast("City deleted", "success");
  };

  const filteredCities = cities.filter(city => 
    city.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-4">
      {/* Header Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Globe className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-bold text-text">Cities Map Editor</h3>
          <span className="text-xs text-text-muted bg-surface-2 px-2 py-0.5 rounded-full">
            {cities.length} cities
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-faint" />
            <input
              type="text"
              placeholder="Search cities..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-7 pr-3 rounded-lg border border-border bg-surface text-xs text-text w-40"
            />
          </div>
          <Button variant="primary" className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold hover:opacity-90 transition shadow" type="button"
            onClick={() => setIsAddingCity(true)}
          >
            <Plus className="h-3.5 w-3.5" />
            Add City
          </Button>
        </div>
      </div>

      {/* Map Container */}
      <div 
        ref={mapRef}
        className="relative h-80 rounded-lg border border-border bg-surface-2 overflow-hidden cursor-crosshair"
        onClick={handleMapClick}
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='720' height='360' viewBox='0 0 720 360'%3E%3Cpath d='M0,0 L720,0 L720,360 L0,360 Z' fill='%23f8fafc'/%3E%3Cpath d='M0,180 L720,180 M180,0 L180,360' stroke='%23e2e8f0' stroke-width='1'/%3E%3C/svg%3E")`,
          backgroundSize: 'cover'
        }}
        data-testid="country-map"
      >
        {/* City Markers */}
        {filteredCities.map((city) => (
          <div
            key={city.id}
            className={`absolute w-6 h-6 rounded-full border-2 border-white shadow-lg transform -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-transform hover:scale-125 ${
              city.is_capital ? 'bg-warning' : 'bg-primary'
            }`}
            style={{
              left: `${((city.longitude + 180) / 360) * 100}%`,
              top: `${((90 - city.latitude) / 180) * 100}%`,
            }}
            onClick={(e) => {
              e.stopPropagation();
              setSelectedCity(city);
              setNewCityName(city.name);
              setNewCityPopulation(city.population?.toString() || "");
              setEditingCity(city);
            }}
            title={city.name}
            data-testid={`city-marker-${city.id}`}
          >
            {city.is_capital && (
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-300 rounded-full"></div>
            )}
          </div>
        ))}

        {/* Empty State Overlay */}
        {cities.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/20">
            <div className="text-center text-text">
              <MapPin className="h-12 w-12 mx-auto mb-2 text-text-faint" />
              <p className="text-sm font-medium">Click on the map to add cities</p>
              <p className="text-xs text-text-faint mt-1">Or use the form below</p>
            </div>
          </div>
        )}
      </div>

      {/* City List */}
      <div className="space-y-2 max-h-60 overflow-y-auto">
        {filteredCities.length === 0 ? (
          <p className="text-sm text-text-faint italic text-center py-4">
            {searchTerm ? "No cities match your search" : "No cities configured"}
          </p>
        ) : (
          filteredCities.map((city) => (
            <div
              key={city.id}
              className={`flex items-center justify-between rounded-lg border p-3 ${
                selectedCity?.id === city.id ? 'border-primary bg-primary/5' : 'border-border'
              }`}
            >
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-text-faint" />
                <div>
                  <span className="text-sm font-medium text-text">{city.name}</span>
                  <div className="text-[10px] text-text-muted">
                    {city.latitude.toFixed(4)}, {city.longitude.toFixed(4)}
                    {city.is_capital && <span className="ml-2 text-warning font-medium">★ Capital</span>}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => {
                    setSelectedCity(city);
                    setNewCityName(city.name);
                    setNewCityPopulation(city.population?.toString() || "");
                    setEditingCity(city);
                  }}
                  className="p-1.5 text-text-muted hover:text-primary transition"
                  title="Edit"
                >
                  <Edit3 className="h-3.5 w-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => handleDeleteCity(city.id)}
                  className="p-1.5 text-text-muted hover:text-danger transition"
                  title="Delete"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Edit City Form (when selecting a city) */}
      {editingCity && (
        <div className="border-t border-border pt-4 mt-4">
          <h4 className="text-xs font-bold text-text mb-3">Edit City Details</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <label className="space-y-1 text-[10px] text-text-muted">
              City Name
              <input
                type="text"
                value={newCityName}
                onChange={(e) => setNewCityName(e.target.value)}
                className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text"
              />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              Latitude
              <input
                type="number"
                step="0.0001"
                value={newCityLat}
                onChange={(e) => setNewCityLat(e.target.value)}
                className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text font-mono"
                disabled
              />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              Longitude
              <input
                type="number"
                step="0.0001"
                value={newCityLng}
                onChange={(e) => setNewCityLng(e.target.value)}
                className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text font-mono"
                disabled
              />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              Population
              <input
                type="number"
                value={newCityPopulation}
                onChange={(e) => setNewCityPopulation(e.target.value)}
                className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-text"
                placeholder="e.g. 1500000"
              />
            </label>
          </div>
          <div className="flex justify-end gap-2 mt-3">
            <button
              type="button"
              onClick={() => setEditingCity(null)}
              className="rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-text-muted hover:bg-surface-2 transition"
            >
              Cancel
            </button>
            <Button variant="primary" type="button"
              onClick={handleUpdateCity}>
              <Save className="h-3.5 w-3.5" />
              Save Changes
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}


