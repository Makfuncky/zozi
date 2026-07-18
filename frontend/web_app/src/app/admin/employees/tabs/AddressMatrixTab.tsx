"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useState } from "react";
import { motion } from "framer-motion";
import {
  Plus,
  X,
  Check,
  AlertTriangle,
  Loader2,
  MapPin,
  Home,
  Building2,
  Globe,
  Phone,
} from "@/lib/icons";
import type { Employee } from "../employee-types";
import { useAdminCountry } from "@/lib/useAdminCountry";

interface Address {
  id: number;
  employee_id: number;
  address_type: string;
  street_address: string;
  city: string;
  state_province: string;
  postal_code: string;
  country: string;
  is_primary: boolean;
  geo_lat?: number | null;
  geo_lng?: number | null;
  valid_from?: string | null;
  valid_to?: string | null;
}

import type { ToastType } from "@/lib/toastStore";
import { apiFetch } from "@/lib/api";

interface AddressMatrixTabProps {
  employees: Employee[];
  addToast: (message: string, type?: ToastType, duration?: number) => void;
}

export default function AddressMatrixTab({ employees, addToast }: AddressMatrixTabProps) {
  const { selectedCountry } = useAdminCountry();
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<number | null>(null);
  const [form, setForm] = useState({
    employee_id: "",
    address_type: "home",
    street_address: "",
    city: "",
    state_province: "",
    postal_code: "",
    country: selectedCountry?.code || "",
    is_primary: false,
    geo_lat: "",
    geo_lng: "",
    valid_from: "",
    valid_to: "",
  });

  const loadAddresses = useCallback(
    async (employeeId: number) => {
      setLoading(true);
      try {
        const res = await apiFetch(`/employees/${employeeId}/addresses`);
        if (res.ok) {
          const data = await res.json().catch(() => []);
          setAddresses(Array.isArray(data) ? data : data?.addresses ?? []);
        } else {
          setAddresses([]);
        }
      } catch {
        addToast("Failed to load addresses", "error");
      } finally {
        setLoading(false);
      }
    },
    [addToast]
  );

  const handleSubmit = async () => {
    if (!form.employee_id || !form.street_address || !form.city || !form.postal_code) {
      addToast("Employee, street, city, and postal code are required", "error");
      return;
    }
    try {
      const payload: Record<string, unknown> = {
        address_type: form.address_type,
        street_address: form.street_address,
        city: form.city,
        state_province: form.state_province || undefined,
        postal_code: form.postal_code,
        country: form.country,
        is_primary: form.is_primary,
        geo_lat: form.geo_lat ? parseFloat(form.geo_lat) : undefined,
        geo_lng: form.geo_lng ? parseFloat(form.geo_lng) : undefined,
        valid_from: form.valid_from || undefined,
        valid_to: form.valid_to || undefined,
      };
      const res = await apiFetch(`/employees/${form.employee_id}/addresses`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        addToast("Address added", "success");
        setShowForm(false);
        setForm({ employee_id: "", address_type: "home", street_address: "", city: "", state_province: "", postal_code: "", country: selectedCountry?.code || "", is_primary: false, geo_lat: "", geo_lng: "", valid_from: "", valid_to: "" });
        if (form.employee_id) loadAddresses(parseInt(form.employee_id));
      } else {
        addToast("Failed to add address", "error");
      }
    } catch {
      addToast("Network error", "error");
    }
  };

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-text">Address Matrix</h3>
        <div className="flex items-center gap-2">
          <select
            onChange={(e) => {
              const id = parseInt(e.target.value);
              if (id) {
                setSelectedEmployeeId(id);
                setForm((f) => ({ ...f, employee_id: String(id) }));
                loadAddresses(id);
              }
            }}
            className="rounded-lg border border-border bg-surface-2 px-3 py-2 text-xs text-text outline-none"
          >
            <option value="">Select employee</option>
            {employees.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.full_name ?? emp.name ?? emp.employee_code}
              </option>
            ))}
          </select>
          <Button variant="primary" className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold shadow-sm transition-colors" onClick={() => {
              if (!selectedEmployeeId) {
                addToast("Please select an employee first", "error");
                return;
              }
              setShowForm(true);
            }}
          >
            <Plus className="h-3.5 w-3.5" />
            Add Address
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin text-text-faint" />
        </div>
      ) : !selectedEmployeeId ? (
        <div className="rounded-xl border border-border bg-surface-1 p-8 text-center">
          <MapPin className="h-8 w-8 mx-auto mb-2 text-text-faint/40" />
          <p className="text-sm text-text-muted">Select an employee to view addresses</p>
        </div>
      ) : addresses.length === 0 ? (
        <div className="rounded-xl border border-border bg-surface-1 p-8 text-center">
          <MapPin className="h-8 w-8 mx-auto mb-2 text-text-faint/40" />
          <p className="text-sm text-text-muted">No addresses on record</p>
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-surface-1 overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-border bg-surface-2 text-text-muted">
                <th className="px-4 py-2.5 font-semibold">Type</th>
                <th className="px-4 py-2.5 font-semibold">Address</th>
                <th className="px-4 py-2.5 font-semibold">City</th>
                <th className="px-4 py-2.5 font-semibold">Country</th>
                <th className="px-4 py-2.5 font-semibold">Primary</th>
                <th className="px-4 py-2.5 font-semibold">Valid From</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {addresses.map((addr) => (
                <tr key={addr.id} className="hover:bg-surface-2/50 transition-colors">
                  <td className="px-4 py-3 text-text capitalize">
                    <div className="flex items-center gap-1.5">
                      {addr.address_type === "home" && <Home className="h-3.5 w-3.5 text-primary" />}
                      {addr.address_type === "office" && <Building2 className="h-3.5 w-3.5 text-success" />}
                      {addr.address_type === "work" && <Building2 className="h-3.5 w-3.5 text-amber-400" />}
                      {addr.address_type}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-text-muted">{addr.street_address}</td>
                  <td className="px-4 py-3 text-text-muted">{addr.city}{addr.state_province ? `, ${addr.state_province}` : ""}</td>
                  <td className="px-4 py-3 text-text-muted">{addr.country}</td>
                  <td className="px-4 py-3">
                    {addr.is_primary && <span className="rounded-full bg-success/10 text-success text-[10px] font-semibold px-2 py-0.5 border border-success/20">Primary</span>}
                  </td>
                  <td className="px-4 py-3 text-text-muted">
                    {addr.valid_from ? new Date(addr.valid_from).toLocaleDateString() : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4" onClick={(e: any) => e.target === e.currentTarget && setShowForm(false)}>
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }} className="w-full max-w-lg rounded-2xl border border-border bg-surface-1 shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-5 py-4">
              <h2 className="font-bold text-text flex items-center gap-2"><MapPin className="h-4 w-4 text-primary" /> Add Address</h2>
              <button onClick={() => setShowForm(false)} className="text-text-muted hover:text-text"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-5 space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Address Type *</label>
                <select value={form.address_type} onChange={(e) => setForm((f) => ({ ...f, address_type: e.target.value }))} className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none">
                  <option value="home">Home</option>
                  <option value="office">Office</option>
                  <option value="work">Work</option>
                  <option value="emergency">Emergency Contact</option>
                </select>
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-text-muted mb-1">Street Address *</label>
                <input type="text" value={form.street_address} onChange={(e) => setForm((f) => ({ ...f, street_address: e.target.value }))} placeholder="123 Main Street, Apt 4B" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-text-muted mb-1">City *</label>
                  <input type="text" value={form.city} onChange={(e) => setForm((f) => ({ ...f, city: e.target.value }))} placeholder="Muscat" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-text-muted mb-1">State / Province</label>
                  <input type="text" value={form.state_province} onChange={(e) => setForm((f) => ({ ...f, state_province: e.target.value }))} placeholder="Muscat Governorate" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-text-muted mb-1">Postal Code *</label>
                  <input type="text" value={form.postal_code} onChange={(e) => setForm((f) => ({ ...f, postal_code: e.target.value }))} placeholder="123" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-text-muted mb-1">Country *</label>
                  <input type="text" value={form.country} onChange={(e) => setForm((f) => ({ ...f, country: e.target.value }))} placeholder="OM" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-text-muted mb-1">Latitude</label>
                  <input type="number" step="any" value={form.geo_lat} onChange={(e) => setForm((f) => ({ ...f, geo_lat: e.target.value }))} placeholder="23.5880" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-text-muted mb-1">Longitude</label>
                  <input type="number" step="any" value={form.geo_lng} onChange={(e) => setForm((f) => ({ ...f, geo_lng: e.target.value }))} placeholder="58.3829" className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-faint outline-none focus:border-primary/50" />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" checked={form.is_primary} onChange={(e) => setForm((f) => ({ ...f, is_primary: e.target.checked }))} className="rounded border-border" />
                <label className="text-xs text-text-muted">Primary address</label>
              </div>
            </div>
            <div className="flex items-center justify-end gap-2 border-t border-border px-5 py-4">
              <button onClick={() => setShowForm(false)} className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text-muted hover:text-text transition-colors">Cancel</button>
              <Button variant="primary" onClick={handleSubmit}><Check className="h-3.5 w-3.5" /> Save</Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </section>
  );
}


