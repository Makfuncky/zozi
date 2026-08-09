"use client";

import { Fragment } from "react";
import { Button } from "@/components/ui/Button";
import { Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check } from "@/lib/icons";
import type { CountriesTabProps } from "./CountriesTabProps";
import type { DeliveryZone } from "../types";

export default function LogisticsModelTab({
  ...p
}: CountriesTabProps) {
  const { baseRate, busyAction, canSubmit, cities, defaultVehicleType, deliveryZones, logisticsModel, minimumCharge, newZoneCarRate, newZoneCities, newZoneCode, newZoneDescription, newZoneName, newZoneTruckRate, newZoneVanRate, newZoneWeightSurcharge, newZoneWeightThreshold, perKmRate, submitLogisticsDraft, weightSurchargeRate, weightThresholdKg, setBaseRate, setDefaultVehicleType, setDeliveryZones, setLogisticsModel, setMinimumCharge, setNewZoneCarRate, setNewZoneCities, setNewZoneCode, setNewZoneDescription, setNewZoneName, setNewZoneTruckRate, setNewZoneVanRate, setNewZoneWeightSurcharge, setNewZoneWeightThreshold, setPerKmRate, setWeightSurchargeRate, setWeightThresholdKg } = p;

  return (
    <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1" data-testid="country-logistics-panel">
      <h3 className="text-sm font-bold text-text">Internal Logistics Engine</h3>
      <p className="text-xs text-text-muted">Specify the core logistics pricing model (fixed fee, per kilometer distance, or regional zone-based routing).</p>

      <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
        <label className="space-y-1 text-xs text-text-muted">
          Logistics Model
          <select
            className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
            value={logisticsModel}
            onChange={(event) => setLogisticsModel(event.target.value)}
          >
            <option value="fixed">Fixed Rate</option>
            <option value="per_km">Per Kilometer</option>
            <option value="zone">Zone-Based Delivery</option>
          </select>
        </label>
        <label className="space-y-1 text-xs text-text-muted">
          Default Vehicle Type
          <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={defaultVehicleType} onChange={(event) => setDefaultVehicleType(event.target.value)} />
        </label>
        <label className="space-y-1 text-xs text-text-muted">
          Base Rate
          <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={baseRate} onChange={(event) => setBaseRate(event.target.value)} />
        </label>
        <label className="space-y-1 text-xs text-text-muted">
          Per KM Rate
          <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={perKmRate} onChange={(event) => setPerKmRate(event.target.value)} />
        </label>
        <label className="space-y-1 text-xs text-text-muted">
          Minimum Charge
          <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={minimumCharge} onChange={(event) => setMinimumCharge(event.target.value)} />
        </label>
        <label className="space-y-1 text-xs text-text-muted">
          Weight Surcharge Rate
          <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={weightSurchargeRate} onChange={(event) => setWeightSurchargeRate(event.target.value)} />
        </label>
        <label className="space-y-1 text-xs text-text-muted md:col-span-2">
          Weight Threshold (KG)
          <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={weightThresholdKg} onChange={(event) => setWeightThresholdKg(event.target.value)} />
        </label>
      </div>

      {logisticsModel === "zone" && (
        <div className="space-y-3 border-t border-border pt-4">
          <span className="block text-xs font-bold text-text">Delivery Zones Management</span>
          <p className="text-[11px] text-text-muted">Create specific delivery zones to override internal vehicle rates and set custom pricing thresholds.</p>

          <div className="grid gap-2 grid-cols-2 md:grid-cols-4 lg:grid-cols-5 p-3 rounded-lg border border-border bg-surface">
            <label className="space-y-1 text-[10px] text-text-muted">
              Zone Code
              <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newZoneCode} onChange={(e) => setNewZoneCode(e.target.value)} placeholder="e.g. Z1" />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              Zone Name
              <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newZoneName} onChange={(e) => setNewZoneName(e.target.value)} placeholder="Central Riyadh" />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              Description
              <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newZoneDescription} onChange={(e) => setNewZoneDescription(e.target.value)} placeholder="Metro area" />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              Car Rate
              <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newZoneCarRate} onChange={(e) => setNewZoneCarRate(e.target.value)} />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              Van Rate
              <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newZoneVanRate} onChange={(e) => setNewZoneVanRate(e.target.value)} />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              Truck Rate
              <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newZoneTruckRate} onChange={(e) => setNewZoneTruckRate(e.target.value)} />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              Weight Surcharge
              <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newZoneWeightSurcharge} onChange={(e) => setNewZoneWeightSurcharge(e.target.value)} />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted">
              Weight Threshold
              <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newZoneWeightThreshold} onChange={(e) => setNewZoneWeightThreshold(e.target.value)} />
            </label>
            <label className="space-y-1 text-[10px] text-text-muted md:col-span-2">
              Cities (comma-separated)
              <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newZoneCities} onChange={(e) => setNewZoneCities(e.target.value)} placeholder="Riyadh, Diriyah" />
            </label>
            <div className="flex items-end md:col-span-4 lg:col-span-5 mt-2 justify-end">
              <button
                type="button"
                onClick={() => {
                  const codeZ = newZoneCode.trim().toUpperCase();
                  const nameZ = newZoneName.trim();
                  if (!codeZ || !nameZ) return;
                  const nextZones: DeliveryZone[] = [
                    ...deliveryZones,
                    {
                      zone_code: codeZ,
                      zone_name: nameZ,
                      description: newZoneDescription.trim() || null,
                      car_rate: Number(newZoneCarRate) || 0,
                      van_rate: Number(newZoneVanRate) || 0,
                      truck_rate: Number(newZoneTruckRate) || 0,
                      weight_surcharge_rate: Number(newZoneWeightSurcharge) || 0,
                      weight_surcharge_threshold_kg: Number(newZoneWeightThreshold) || 0,
                      cities: newZoneCities.split(",").map((c) => c.trim()).filter(Boolean),
                      is_active: true,
                      sort_order: deliveryZones.length + 1
                    }
                  ];
                  setDeliveryZones(nextZones);
                  setNewZoneCode("");
                  setNewZoneName("");
                  setNewZoneDescription("");
                  setNewZoneCities("");
                }}
                className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface-2 px-4 text-xs font-semibold text-text hover:bg-surface-3 transition"
              >
                <Plus className="h-3.5 w-3.5" />
                Add Delivery Zone
              </button>
            </div>
          </div>

          <div className="overflow-x-auto rounded-lg border border-border bg-surface mt-2">
            <table className="w-full border-collapse text-left text-xs min-w-[800px]">
              <thead className="bg-surface-2 text-text-muted">
                <tr>
                  <th className="px-3 py-2 font-semibold">Zone Code</th>
                  <th className="px-3 py-2 font-semibold">Zone Name</th>
                  <th className="px-3 py-2 font-semibold">Car/Van/Truck Rates</th>
                  <th className="px-3 py-2 font-semibold">Weight Rule</th>
                  <th className="px-3 py-2 font-semibold">Cities Coverage</th>
                  <th className="px-3 py-2 font-semibold w-16 text-center">Action</th>
                </tr>
              </thead>
              <tbody>
                {deliveryZones.map((zone, idx) => (
                  <tr key={idx} className="border-t border-border">
                    <td className="px-3 py-2 text-text font-bold font-mono">{zone.zone_code}</td>
                    <td className="px-3 py-2 text-text">
                      <div className="font-medium">{zone.zone_name}</div>
                      <div className="text-[10px] text-text-faint">{zone.description || "No description"}</div>
                    </td>
                    <td className="px-3 py-2 text-text font-medium">
                      Car: {zone.car_rate} / Van: {zone.van_rate} / Truck: {zone.truck_rate}
                    </td>
                    <td className="px-3 py-2 text-text">
                      {zone.weight_surcharge_rate && zone.weight_surcharge_threshold_kg
                        ? `+${zone.weight_surcharge_rate}/kg after ${zone.weight_surcharge_threshold_kg}kg`
                        : "No surcharge"}
                    </td>
                    <td className="px-3 py-2 text-text font-mono max-w-[200px] truncate" title={zone.cities.join(", ")}>
                      {zone.cities.join(", ") || "No cities"}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <Button variant="danger" className="p-1 rounded transition" type="button"
                        onClick={() => setDeliveryZones(deliveryZones.filter((_, i) => i !== idx))}
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </td>
                  </tr>
                ))}
                {deliveryZones.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-3 py-3 text-center text-text-faint italic">No custom zones configured.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="flex justify-end pt-2">
        <Button variant="primary" type="button"
          onClick={submitLogisticsDraft}
          disabled={!canSubmit || busyAction === "logistics"}
          data-testid="create-logistics-draft-button">
          <Save className="h-3.5 w-3.5" />
          {busyAction === "logistics" ? "Creating draft..." : "Save Logistics Draft"}
        </Button>
      </div>
    </section>
  );
}
