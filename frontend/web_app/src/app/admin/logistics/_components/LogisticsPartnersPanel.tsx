"use client";

import { useEffect, useMemo, useState } from "react";
import { PanelContent } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useAdminCountry } from "@/lib/useAdminCountry";

interface LogisticsPartnersPanelProps {
  scope?: string;
}

interface Partner {
  id: number;
  name: string;
  code: string;
  contact_email?: string;
  status?: string;
  verification_status?: string;
  verification_note?: string;
  country?: string;
  city?: string;
  coverage_regions?: string[];
  service_types?: string[];
  created_at?: string;
}

interface ServiceArea {
  id: number;
  partner_id: number;
  country_code?: string;
  country_name?: string;
  city_name?: string;
  zone_label?: string;
  charge_amount?: number;
  minimum_charge?: number;
  per_kg_rate?: number;
  per_km_rate?: number;
  fuel_multiplier?: number;
  pickup_charge?: number;
  dropoff_charge?: number;
  currency?: string;
  delivery_days_min?: number;
  delivery_days_max?: number;
  is_active?: boolean;
  approval_status?: string;
  latitude?: number | null;
  longitude?: number | null;
}

interface PricingProfile {
  id: number;
  partner_id: number;
  service_area_id?: number;
  profile_name?: string;
  currency?: string;
  approval_status?: string;
  is_active?: boolean;
  base_in_city_fee?: number;
  base_inter_city_fee?: number;
  per_kg_rate?: number;
  per_km_rate?: number;
  minimum_charge?: number;
  maximum_charge?: number;
  fuel_multiplier?: number;
  bulk_discount_threshold_kg?: number;
  bulk_discount_percent?: number;
}

interface CategoryRule {
  id: number;
  partner_id: number;
  service_area_id?: number;
  category_name?: string;
  flat_fee_override?: number;
  special_handling_fee?: number;
  currency?: string;
  approval_status?: string;
  is_active?: boolean;
}

interface VehicleRule {
  id: number;
  partner_id: number;
  service_area_id?: number;
  vehicle_type?: string;
  route_scope?: string;
  cost_multiplier?: number;
  max_weight_kg?: number;
  max_volume_cm3?: number;
  priority_rank?: number;
  currency?: string;
  approval_status?: string;
  is_active?: boolean;
}

interface CityDistance {
  id: number;
  origin_country_code?: string;
  origin_city_name?: string;
  destination_country_code?: string;
  destination_city_name?: string;
  distance_km?: number;
  notes?: string;
}

type AreaForm = {
  partner_id: string;
  country_code: string;
  country_name: string;
  city_name: string;
  zone_label: string;
  charge_amount: string;
  minimum_charge: string;
  per_kg_rate: string;
  per_km_rate: string;
  fuel_multiplier: string;
  pickup_charge: string;
  dropoff_charge: string;
  currency: string;
  latitude: string;
  longitude: string;
  delivery_days_min: string;
  delivery_days_max: string;
};

type ProfileForm = {
  partner_id: string;
  service_area_id: string;
  profile_name: string;
  base_in_city_fee: string;
  base_inter_city_fee: string;
  per_kg_rate: string;
  per_km_rate: string;
  minimum_charge: string;
  maximum_charge: string;
  fuel_multiplier: string;
  bulk_discount_threshold_kg: string;
  bulk_discount_percent: string;
  currency: string;
};

type CatRuleForm = {
  partner_id: string;
  service_area_id: string;
  category_name: string;
  special_handling_fee: string;
  currency: string;
};

type VehRuleForm = {
  partner_id: string;
  service_area_id: string;
  vehicle_type: string;
  route_scope: string;
  cost_multiplier: string;
  max_weight_kg: string;
  max_volume_cm3: string;
  priority_rank: string;
};

type DistanceForm = {
  origin_country_code: string;
  origin_city_name: string;
  destination_country_code: string;
  destination_city_name: string;
  distance_km: string;
  notes: string;
};

const asArray = (data: any) => (Array.isArray(data) ? data : (data?.items ?? []));

function roundCharge(value: number): number {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

function hasCoordinates(latitude: number | null | undefined, longitude: number | null | undefined): boolean {
  return typeof latitude === "number" && Number.isFinite(latitude) && typeof longitude === "number" && Number.isFinite(longitude);
}

function formatMoney(value: number | null | undefined): string {
  return value != null ? value.toFixed(2) : "0.00";
}

function formatStatusLabel(value: string | null | undefined): string {
  return (value || "unknown").replace(/_/g, " ");
}

type PricingCalculatorForm = {
  routeType: "in_city" | "inter_city";
  weightKg: string;
  distanceKm: string;
  pickupCount: string;
  dropoffCount: string;
  selectedCategories: string[];
};

function createDefaultCalculatorForm(): PricingCalculatorForm {
  return {
    routeType: "in_city",
    weightKg: "8",
    distanceKm: "0",
    pickupCount: "2",
    dropoffCount: "1",
    selectedCategories: ["fragile"],
  };
}

const BLANK_AREA_FORM: AreaForm = {
  partner_id: "",
  country_code: "",
  country_name: "",
  city_name: "",
  zone_label: "",
  charge_amount: "",
  minimum_charge: "",
  per_kg_rate: "",
  per_km_rate: "",
  fuel_multiplier: "",
  pickup_charge: "",
  dropoff_charge: "",
  currency: "AED",
  latitude: "",
  longitude: "",
  delivery_days_min: "",
  delivery_days_max: "",
};

const BLANK_PROFILE_FORM: ProfileForm = {
  partner_id: "",
  service_area_id: "",
  profile_name: "",
  base_in_city_fee: "",
  base_inter_city_fee: "",
  per_kg_rate: "",
  per_km_rate: "",
  minimum_charge: "",
  maximum_charge: "",
  fuel_multiplier: "",
  bulk_discount_threshold_kg: "",
  bulk_discount_percent: "",
  currency: "AED",
};

const BLANK_CAT_RULE_FORM: CatRuleForm = {
  partner_id: "",
  service_area_id: "",
  category_name: "",
  special_handling_fee: "",
  currency: "AED",
};

const BLANK_VEH_RULE_FORM: VehRuleForm = {
  partner_id: "",
  service_area_id: "",
  vehicle_type: "",
  route_scope: "any",
  cost_multiplier: "1.0",
  max_weight_kg: "",
  max_volume_cm3: "",
  priority_rank: "100",
};

const BLANK_DISTANCE_FORM: DistanceForm = {
  origin_country_code: "",
  origin_city_name: "",
  destination_country_code: "",
  destination_city_name: "",
  distance_km: "",
  notes: "",
};

export default function LogisticsPartnersPanel({ scope }: LogisticsPartnersPanelProps) {
  const isPricing = scope === "pricing";
  const { selectedCountry } = useAdminCountry();
  const countryHeader =
    selectedCountry?.code && selectedCountry.code !== "*" ? selectedCountry.code : null;

  async function fetchJson(path: string, options?: RequestInit): Promise<any> {
    const opts = countryScopedOptions(options);
    const res = opts ? await apiFetch(path, opts) : await apiFetch(path);
    if (!res.ok) {
      const payload = await res.json().catch(() => ({}));
      throw new Error((payload as { detail?: string }).detail || `Request failed: ${path} ${res.status}`);
    }
    return res.json();
  }

  function countryScopedOptions(options?: RequestInit): RequestInit | undefined {
    if (!countryHeader) return options;
    const headers = { ...(options?.headers || {}), "X-Country-Code": countryHeader };
    return { ...(options || {}), headers };
  }

  const [tab, setTab] = useState<"partners" | "service-areas" | "city-distances">("partners");
  const [pricingTab, setPricingTab] = useState<"profiles" | "handling" | "vehicles" | "calculator">("profiles");
  const [partners, setPartners] = useState<Partner[]>([]);
  const [serviceAreas, setServiceAreas] = useState<ServiceArea[]>([]);
  const [pricingProfiles, setPricingProfiles] = useState<PricingProfile[]>([]);
  const [categoryRules, setCategoryRules] = useState<CategoryRule[]>([]);
  const [vehicleRules, setVehicleRules] = useState<VehicleRule[]>([]);
  const [cityDistances, setCityDistances] = useState<CityDistance[]>([]);
  const [selectedPartnerIds, setSelectedPartnerIds] = useState<number[]>([]);
  const [sectionError, setSectionError] = useState<string>("");
  const [sectionMessage, setSectionMessage] = useState<string>("");

  const [pricingPartnerId, setPricingPartnerId] = useState<string>("");
  const [pricingAreaId, setPricingAreaId] = useState<string>("");

  // Service area form
  const [showAreaForm, setShowAreaForm] = useState(false);
  const [editingAreaId, setEditingAreaId] = useState<number | null>(null);
  const [areaForm, setAreaForm] = useState<AreaForm>(BLANK_AREA_FORM);

  // City distance form
  const [showDistanceForm, setShowDistanceForm] = useState(false);
  const [editingDistanceId, setEditingDistanceId] = useState<number | null>(null);
  const [distanceForm, setDistanceForm] = useState<DistanceForm>(BLANK_DISTANCE_FORM);

  // Pricing profile form
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [editingProfileId, setEditingProfileId] = useState<number | null>(null);
  const [profileForm, setProfileForm] = useState<ProfileForm>(BLANK_PROFILE_FORM);

  // Category rule form
  const [showCatRuleForm, setShowCatRuleForm] = useState(false);
  const [editingCatRuleId, setEditingCatRuleId] = useState<number | null>(null);
  const [catRuleForm, setCatRuleForm] = useState<CatRuleForm>(BLANK_CAT_RULE_FORM);

  // Vehicle rule form
  const [showVehRuleForm, setShowVehRuleForm] = useState(false);
  const [editingVehRuleId, setEditingVehRuleId] = useState<number | null>(null);
  const [vehRuleForm, setVehRuleForm] = useState<VehRuleForm>(BLANK_VEH_RULE_FORM);

  const [calculatorForm, setCalculatorForm] = useState<PricingCalculatorForm>(() => createDefaultCalculatorForm());
  const [liveQuote, setLiveQuote] = useState<{ amount: number; currency: string; source: string } | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([
      fetchJson("/logistics-partners/").then(asArray).catch(() => []),
      fetchJson("/logistics-partners/service-areas").then(asArray).catch(() => []),
      fetchJson("/logistics-partners/pricing-profiles").then(asArray).catch(() => []),
      fetchJson("/logistics-partners/category-rules").then(asArray).catch(() => []),
      fetchJson("/logistics-partners/vehicle-rules").then(asArray).catch(() => []),
      fetchJson("/logistics-partners/city-distances").then(asArray).catch(() => []),
    ])
      .then(([p, sa, pp, cr, vr, cd]) => {
        if (!active) return;
        setPartners(p);
        setServiceAreas(sa);
        setPricingProfiles(pp);
        setCategoryRules(cr);
        setVehicleRules(vr);
        setCityDistances(cd);
        if (p.length) setPricingPartnerId(String(p[0].id));
        if (sa.length) setPricingAreaId(String(sa[0].id));
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  // ── Partner actions ─────────────────────────────────────────────────────────
  async function approvePartner(id: number) {
    await fetchJson(`/logistics-partners/review/profile/${id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "approved" }),
    });
    setPartners((prev) =>
      prev.map((p) => (p.id === id ? { ...p, verification_status: "approved", status: "active" } : p)),
    );
  }

  async function suspendPartner(id: number) {
    await fetchJson(`/logistics-partners/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "suspended" }),
    });
  }

  async function deletePartner(id: number) {
    if (typeof window !== "undefined" && !window.confirm("Delete this logistics partner?")) return;
    await fetchJson(`/logistics-partners/${id}`, { method: "DELETE" });
    setPartners((prev) => prev.filter((p) => p.id !== id));
  }

  async function bulkApprove() {
    await fetchJson(`/logistics-partners/bulk`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ partner_ids: selectedPartnerIds, action: "approve" }),
    });
    setSelectedPartnerIds([]);
  }

  function toggleSelect(id: number) {
    setSelectedPartnerIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  // ── Service area CRUD ───────────────────────────────────────────────────────
  function openCreateArea() {
    setEditingAreaId(null);
    setAreaForm({ ...BLANK_AREA_FORM, partner_id: pricingPartnerId || (partners[0] ? String(partners[0].id) : ""), currency: "AED" });
    setShowAreaForm(true);
    setSectionError("");
  }

  function openEditArea(area: ServiceArea) {
    setEditingAreaId(area.id);
    setAreaForm({
      partner_id: String(area.partner_id),
      country_code: area.country_code ?? "",
      country_name: area.country_name ?? "",
      city_name: area.city_name ?? "",
      zone_label: area.zone_label ?? "",
      charge_amount: String(area.charge_amount ?? 0),
      minimum_charge: area.minimum_charge != null ? String(area.minimum_charge) : "",
      per_kg_rate: area.per_kg_rate != null ? String(area.per_kg_rate) : "",
      per_km_rate: area.per_km_rate != null ? String(area.per_km_rate) : "",
      fuel_multiplier: area.fuel_multiplier != null ? String(area.fuel_multiplier) : "",
      pickup_charge: area.pickup_charge != null ? String(area.pickup_charge) : "",
      dropoff_charge: area.dropoff_charge != null ? String(area.dropoff_charge) : "",
      currency: area.currency || "AED",
      latitude: area.latitude != null ? String(area.latitude) : "",
      longitude: area.longitude != null ? String(area.longitude) : "",
      delivery_days_min: area.delivery_days_min != null ? String(area.delivery_days_min) : "",
      delivery_days_max: area.delivery_days_max != null ? String(area.delivery_days_max) : "",
    });
    setShowAreaForm(true);
    setSectionError("");
  }

  async function saveArea() {
    setSectionError("");
    try {
      const url = editingAreaId ? `/logistics-partners/service-areas/${editingAreaId}` : "/logistics-partners/service-areas";
      const body: Record<string, unknown> = {
        partner_id: Number(areaForm.partner_id),
        country_code: areaForm.country_code,
        country_name: areaForm.country_name,
        city_name: areaForm.city_name,
        zone_label: areaForm.zone_label,
        currency: areaForm.currency || "AED",
        charge_amount: Number(areaForm.charge_amount) || 0,
        minimum_charge: areaForm.minimum_charge ? Number(areaForm.minimum_charge) : null,
        per_kg_rate: areaForm.per_kg_rate ? Number(areaForm.per_kg_rate) : null,
        per_km_rate: areaForm.per_km_rate ? Number(areaForm.per_km_rate) : null,
        fuel_multiplier: areaForm.fuel_multiplier ? Number(areaForm.fuel_multiplier) : null,
        pickup_charge: areaForm.pickup_charge ? Number(areaForm.pickup_charge) : null,
        dropoff_charge: areaForm.dropoff_charge ? Number(areaForm.dropoff_charge) : null,
        latitude: areaForm.latitude ? Number(areaForm.latitude) : null,
        longitude: areaForm.longitude ? Number(areaForm.longitude) : null,
        delivery_days_min: areaForm.delivery_days_min ? Number(areaForm.delivery_days_min) : null,
        delivery_days_max: areaForm.delivery_days_max ? Number(areaForm.delivery_days_max) : null,
      };
      await fetchJson(url, {
        method: editingAreaId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const refreshed = asArray(await fetchJson("/logistics-partners/service-areas"));
      setServiceAreas(refreshed);
      setShowAreaForm(false);
      setEditingAreaId(null);
    } catch (err) {
      setSectionError(err instanceof Error ? err.message : "Could not save service area");
    }
  }

  async function deleteArea(areaId: number) {
    if (typeof window !== "undefined" && !window.confirm("Delete this service area?")) return;
    await fetchJson(`/logistics-partners/service-areas/${areaId}`, { method: "DELETE" });
    setServiceAreas((prev) => prev.filter((a) => a.id !== areaId));
  }

  async function reviewArea(areaId: number, status: "approved" | "rejected") {
    setSectionError("");
    try {
      await fetchJson(`/logistics-partners/review/service-areas/${areaId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      setServiceAreas((prev) =>
        prev.map((a) => (a.id === areaId ? { ...a, approval_status: status } : a)),
      );
      setSectionMessage(`Service area ${status}.`);
    } catch (err) {
      setSectionError(err instanceof Error ? err.message : "Could not review service area");
    }
  }

  // ── City distance CRUD ──────────────────────────────────────────────────────
  function openCreateDistance() {
    setEditingDistanceId(null);
    setDistanceForm(BLANK_DISTANCE_FORM);
    setShowDistanceForm(true);
    setSectionError("");
  }

  function openEditDistance(d: CityDistance) {
    setEditingDistanceId(d.id);
    setDistanceForm({
      origin_country_code: d.origin_country_code ?? "",
      origin_city_name: d.origin_city_name ?? "",
      destination_country_code: d.destination_country_code ?? "",
      destination_city_name: d.destination_city_name ?? "",
      distance_km: String(d.distance_km ?? 0),
      notes: d.notes ?? "",
    });
    setShowDistanceForm(true);
    setSectionError("");
  }

  async function saveDistance() {
    setSectionError("");
    try {
      const url = editingDistanceId ? `/logistics-partners/city-distances/${editingDistanceId}` : "/logistics-partners/city-distances";
      await fetchJson(url, {
        method: editingDistanceId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...distanceForm, distance_km: Number(distanceForm.distance_km) }),
      });
      const refreshed = asArray(await fetchJson("/logistics-partners/city-distances"));
      setCityDistances(refreshed);
      setShowDistanceForm(false);
      setEditingDistanceId(null);
    } catch (err) {
      setSectionError(err instanceof Error ? err.message : "Could not save city distance");
    }
  }

  async function deleteDistance(matrixId: number) {
    if (typeof window !== "undefined" && !window.confirm("Delete this city distance?")) return;
    await fetchJson(`/logistics-partners/city-distances/${matrixId}`, { method: "DELETE" });
    setCityDistances((prev) => prev.filter((d) => d.id !== matrixId));
  }

  // ── Pricing profile CRUD ───────────────────────────────────────────────────
  function openCreateProfile() {
    setEditingProfileId(null);
    setProfileForm({ ...BLANK_PROFILE_FORM, partner_id: pricingPartnerId || (partners[0] ? String(partners[0].id) : ""), currency: "AED" });
    setShowProfileForm(true);
    setSectionError("");
  }

  function openEditProfile(profile: PricingProfile) {
    setEditingProfileId(profile.id);
    setProfileForm({
      partner_id: String(profile.partner_id),
      service_area_id: profile.service_area_id != null ? String(profile.service_area_id) : "",
      profile_name: profile.profile_name ?? "",
      base_in_city_fee: profile.base_in_city_fee != null ? String(profile.base_in_city_fee) : "",
      base_inter_city_fee: profile.base_inter_city_fee != null ? String(profile.base_inter_city_fee) : "",
      per_kg_rate: profile.per_kg_rate != null ? String(profile.per_kg_rate) : "",
      per_km_rate: profile.per_km_rate != null ? String(profile.per_km_rate) : "",
      minimum_charge: profile.minimum_charge != null ? String(profile.minimum_charge) : "",
      maximum_charge: profile.maximum_charge != null ? String(profile.maximum_charge) : "",
      fuel_multiplier: profile.fuel_multiplier != null ? String(profile.fuel_multiplier) : "",
      bulk_discount_threshold_kg: profile.bulk_discount_threshold_kg != null ? String(profile.bulk_discount_threshold_kg) : "",
      bulk_discount_percent: profile.bulk_discount_percent != null ? String(profile.bulk_discount_percent) : "",
      currency: profile.currency || "AED",
    });
    setShowProfileForm(true);
    setSectionError("");
  }

  async function saveProfile() {
    setSectionError("");
    try {
      const url = editingProfileId ? `/logistics-partners/pricing-profiles/${editingProfileId}` : "/logistics-partners/pricing-profiles";
      const body: Record<string, unknown> = {
        partner_id: Number(profileForm.partner_id),
        service_area_id: profileForm.service_area_id ? Number(profileForm.service_area_id) : null,
        profile_name: profileForm.profile_name,
        currency: profileForm.currency || "AED",
        base_in_city_fee: profileForm.base_in_city_fee ? Number(profileForm.base_in_city_fee) : null,
        base_inter_city_fee: profileForm.base_inter_city_fee ? Number(profileForm.base_inter_city_fee) : null,
        per_kg_rate: profileForm.per_kg_rate ? Number(profileForm.per_kg_rate) : null,
        per_km_rate: profileForm.per_km_rate ? Number(profileForm.per_km_rate) : null,
        minimum_charge: profileForm.minimum_charge ? Number(profileForm.minimum_charge) : null,
        maximum_charge: profileForm.maximum_charge ? Number(profileForm.maximum_charge) : null,
        fuel_multiplier: profileForm.fuel_multiplier ? Number(profileForm.fuel_multiplier) : null,
        bulk_discount_threshold_kg: profileForm.bulk_discount_threshold_kg ? Number(profileForm.bulk_discount_threshold_kg) : null,
        bulk_discount_percent: profileForm.bulk_discount_percent ? Number(profileForm.bulk_discount_percent) : null,
      };
      await fetchJson(url, {
        method: editingProfileId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const refreshed = asArray(await fetchJson("/logistics-partners/pricing-profiles"));
      setPricingProfiles(refreshed);
      setShowProfileForm(false);
      setEditingProfileId(null);
    } catch (err) {
      setSectionError(err instanceof Error ? err.message : "Could not save pricing profile");
    }
  }

  async function deleteProfile(profileId: number) {
    if (typeof window !== "undefined" && !window.confirm("Delete this pricing profile?")) return;
    await fetchJson(`/logistics-partners/pricing-profiles/${profileId}`, { method: "DELETE" });
    setPricingProfiles((prev) => prev.filter((p) => p.id !== profileId));
  }

  async function reviewProfile(profileId: number, status: "approved" | "rejected") {
    setSectionError("");
    try {
      await fetchJson(`/logistics-partners/review/pricing-profiles/${profileId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      setPricingProfiles((prev) => prev.map((p) => (p.id === profileId ? { ...p, approval_status: status } : p)));
      setSectionMessage(`Pricing profile ${status}.`);
    } catch (err) {
      setSectionError(err instanceof Error ? err.message : "Could not review pricing profile");
    }
  }

  // ── Category rule (handling) CRUD ───────────────────────────────────────────
  function openCreateCatRule() {
    setEditingCatRuleId(null);
    setCatRuleForm({ ...BLANK_CAT_RULE_FORM, partner_id: pricingPartnerId || (partners[0] ? String(partners[0].id) : ""), currency: "AED" });
    setShowCatRuleForm(true);
    setSectionError("");
  }

  function openEditCatRule(rule: CategoryRule) {
    setEditingCatRuleId(rule.id);
    setCatRuleForm({
      partner_id: String(rule.partner_id),
      service_area_id: rule.service_area_id != null ? String(rule.service_area_id) : "",
      category_name: rule.category_name ?? "",
      special_handling_fee: rule.special_handling_fee != null ? String(rule.special_handling_fee) : "",
      currency: rule.currency || "AED",
    });
    setShowCatRuleForm(true);
    setSectionError("");
  }

  async function saveCatRule() {
    setSectionError("");
    try {
      const url = editingCatRuleId ? `/logistics-partners/category-rules/${editingCatRuleId}` : "/logistics-partners/category-rules";
      const body: Record<string, unknown> = {
        partner_id: Number(catRuleForm.partner_id),
        service_area_id: catRuleForm.service_area_id ? Number(catRuleForm.service_area_id) : null,
        category_name: catRuleForm.category_name,
        special_handling_fee: catRuleForm.special_handling_fee ? Number(catRuleForm.special_handling_fee) : null,
        currency: catRuleForm.currency || "AED",
      };
      await fetchJson(url, {
        method: editingCatRuleId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const refreshed = asArray(await fetchJson("/logistics-partners/category-rules"));
      setCategoryRules(refreshed);
      setShowCatRuleForm(false);
      setEditingCatRuleId(null);
    } catch (err) {
      setSectionError(err instanceof Error ? err.message : "Could not save handling rule");
    }
  }

  async function deleteCatRule(ruleId: number) {
    if (typeof window !== "undefined" && !window.confirm("Delete this handling rule?")) return;
    await fetchJson(`/logistics-partners/category-rules/${ruleId}`, { method: "DELETE" });
    setCategoryRules((prev) => prev.filter((r) => r.id !== ruleId));
  }

  async function reviewCatRule(ruleId: number, status: "approved" | "rejected") {
    setSectionError("");
    try {
      await fetchJson(`/logistics-partners/review/category-rules/${ruleId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      setCategoryRules((prev) => prev.map((r) => (r.id === ruleId ? { ...r, approval_status: status } : r)));
      setSectionMessage(`Handling rule ${status}.`);
    } catch (err) {
      setSectionError(err instanceof Error ? err.message : "Could not review handling rule");
    }
  }

  // ── Vehicle rule CRUD ───────────────────────────────────────────────────────
  function openCreateVehRule() {
    setEditingVehRuleId(null);
    setVehRuleForm({ ...BLANK_VEH_RULE_FORM, partner_id: pricingPartnerId || (partners[0] ? String(partners[0].id) : "") });
    setShowVehRuleForm(true);
    setSectionError("");
  }

  function openEditVehRule(rule: VehicleRule) {
    setEditingVehRuleId(rule.id);
    setVehRuleForm({
      partner_id: String(rule.partner_id),
      service_area_id: rule.service_area_id != null ? String(rule.service_area_id) : "",
      vehicle_type: rule.vehicle_type ?? "",
      route_scope: rule.route_scope ?? "any",
      cost_multiplier: rule.cost_multiplier != null ? String(rule.cost_multiplier) : "1.0",
      max_weight_kg: rule.max_weight_kg != null ? String(rule.max_weight_kg) : "",
      max_volume_cm3: rule.max_volume_cm3 != null ? String(rule.max_volume_cm3) : "",
      priority_rank: rule.priority_rank != null ? String(rule.priority_rank) : "100",
    });
    setShowVehRuleForm(true);
    setSectionError("");
  }

  async function saveVehRule() {
    setSectionError("");
    try {
      const url = editingVehRuleId ? `/logistics-partners/vehicle-rules/${editingVehRuleId}` : "/logistics-partners/vehicle-rules";
      const body: Record<string, unknown> = {
        partner_id: Number(vehRuleForm.partner_id),
        service_area_id: vehRuleForm.service_area_id ? Number(vehRuleForm.service_area_id) : null,
        vehicle_type: vehRuleForm.vehicle_type,
        route_scope: vehRuleForm.route_scope,
        cost_multiplier: Number(vehRuleForm.cost_multiplier) || 1,
        max_weight_kg: vehRuleForm.max_weight_kg ? Number(vehRuleForm.max_weight_kg) : null,
        max_volume_cm3: vehRuleForm.max_volume_cm3 ? Number(vehRuleForm.max_volume_cm3) : null,
        priority_rank: Number(vehRuleForm.priority_rank) || 100,
      };
      await fetchJson(url, {
        method: editingVehRuleId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const refreshed = asArray(await fetchJson("/logistics-partners/vehicle-rules"));
      setVehicleRules(refreshed);
      setShowVehRuleForm(false);
      setEditingVehRuleId(null);
    } catch (err) {
      setSectionError(err instanceof Error ? err.message : "Could not save load-fit rule");
    }
  }

  async function deleteVehRule(ruleId: number) {
    if (typeof window !== "undefined" && !window.confirm("Delete this load-fit rule?")) return;
    await fetchJson(`/logistics-partners/vehicle-rules/${ruleId}`, { method: "DELETE" });
    setVehicleRules((prev) => prev.filter((r) => r.id !== ruleId));
  }

  async function reviewVehRule(ruleId: number, status: "approved" | "rejected") {
    setSectionError("");
    try {
      await fetchJson(`/logistics-partners/review/vehicle-rules/${ruleId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      setVehicleRules((prev) => prev.map((r) => (r.id === ruleId ? { ...r, approval_status: status } : r)));
      setSectionMessage(`Load-fit rule ${status}.`);
    } catch (err) {
      setSectionError(err instanceof Error ? err.message : "Could not review load-fit rule");
    }
  }

  // ── Calculator ──────────────────────────────────────────────────────────────
  const selectedPartnerIdNum = pricingPartnerId ? Number(pricingPartnerId) : partners[0]?.id ?? 0;
  const areasForPartner = useMemo(
    () => serviceAreas.filter((sa) => sa.partner_id === selectedPartnerIdNum),
    [serviceAreas, selectedPartnerIdNum],
  );
  const selectedAreaIdNum = pricingAreaId ? Number(pricingAreaId) : areasForPartner[0]?.id ?? 0;
  const selectedArea = serviceAreas.find((sa) => sa.id === selectedAreaIdNum) || null;

  const controlApprovedProfiles = useMemo(
    () => pricingProfiles.filter((p) => p.partner_id === selectedPartnerIdNum && p.approval_status === "approved" && p.is_active),
    [pricingProfiles, selectedPartnerIdNum],
  );
  const controlProfile = useMemo(() => {
    const scoped = selectedAreaIdNum ? selectedAreaIdNum : null;
    return controlApprovedProfiles.find((p) => p.service_area_id === scoped) ?? controlApprovedProfiles.find((p) => p.service_area_id == null) ?? null;
  }, [controlApprovedProfiles, selectedAreaIdNum]);

  const controlCategoryOptions = useMemo(() => {
    const scoped = selectedAreaIdNum ? selectedAreaIdNum : null;
    const candidates = categoryRules
      .filter(
        (r) =>
          r.partner_id === selectedPartnerIdNum &&
          r.approval_status === "approved" &&
          r.is_active &&
          (r.service_area_id == null || r.service_area_id === scoped),
      )
      .sort((a, b) => {
        const la = a.service_area_id === scoped ? 0 : 1;
        const lb = b.service_area_id === scoped ? 0 : 1;
        if (la !== lb) return la - lb;
        return (a.category_name ?? "").localeCompare(b.category_name ?? "");
      });
    const deduped = new Map<string, CategoryRule>();
    candidates.forEach((r) => {
      const key = (r.category_name ?? "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "-");
      if (key && !deduped.has(key)) deduped.set(key, r);
    });
    return Array.from(deduped.entries()).map(([key, rule]) => ({ key, rule }));
  }, [categoryRules, selectedPartnerIdNum, selectedAreaIdNum]);

  const calculatorBreakdown = useMemo(() => {
    const routeType = calculatorForm.routeType;
    const weightKg = Math.max(Number(calculatorForm.weightKg) || 0, 0);
    const distanceKm = routeType === "inter_city" ? Math.max(Number(calculatorForm.distanceKm) || 0, 0) : 0;
    const pickupCount = Math.max(Number(calculatorForm.pickupCount) || 1, 1);
    const dropoffCount = Math.max(Number(calculatorForm.dropoffCount) || 1, 1);
    const extraPickupCount = Math.max(pickupCount - 1, 0);
    const extraDropoffCount = Math.max(dropoffCount - 1, 0);

    const baseFee = roundCharge(routeType === "in_city"
      ? Number(controlProfile?.base_in_city_fee ?? selectedArea?.charge_amount ?? 0)
      : Number(controlProfile?.base_inter_city_fee ?? selectedArea?.charge_amount ?? 0));
    const perKgRate = Number(controlProfile?.per_kg_rate ?? selectedArea?.per_kg_rate ?? 0);
    const perKmRate = routeType === "inter_city" ? Number(controlProfile?.per_km_rate ?? selectedArea?.per_km_rate ?? 0) : 0;
    const pickupRate = Number(selectedArea?.pickup_charge ?? 0);
    const dropoffRate = Number(selectedArea?.dropoff_charge ?? 0);
    const fuelMultiplier = Number(controlProfile?.fuel_multiplier ?? selectedArea?.fuel_multiplier ?? 1);
    const minimumCharge = controlProfile?.minimum_charge ?? selectedArea?.minimum_charge ?? null;
    const maximumCharge = controlProfile?.maximum_charge ?? null;
    const weightFee = roundCharge(weightKg * perKgRate);
    const distanceFee = roundCharge(distanceKm * perKmRate);
    const pickupFee = roundCharge(extraPickupCount * pickupRate);
    const dropoffFee = roundCharge(extraDropoffCount * dropoffRate);

    const selectedCategoryRules = controlCategoryOptions
      .filter((o) => calculatorForm.selectedCategories.includes(o.key))
      .map((o) => o.rule);
    const applied = selectedCategoryRules.reduce<{ rule: CategoryRule | null; total: number }>((cur, rule) => {
      const total = roundCharge(Math.max(Number(rule.flat_fee_override ?? 0), Number(rule.special_handling_fee ?? 0)));
      if (!cur.rule || total > cur.total) return { rule, total };
      return cur;
    }, { rule: null, total: 0 });
    const categoryTotal = applied.total;

    const subtotal = roundCharge(baseFee + weightFee + distanceFee + pickupFee + dropoffFee + categoryTotal);
    const fuelAdjusted = roundCharge(subtotal * fuelMultiplier);
    const minimumChargeApplied = minimumCharge != null && fuelAdjusted < minimumCharge;
    const afterMinimum = minimumChargeApplied ? roundCharge(Number(minimumCharge)) : fuelAdjusted;
    const maximumChargeApplied = maximumCharge != null && maximumCharge > 0 && afterMinimum > maximumCharge;
    const finalCharge = maximumChargeApplied ? roundCharge(Number(maximumCharge)) : afterMinimum;

    return {
      baseFee,
      weightFee,
      distanceFee,
      pickupFee,
      dropoffFee,
      categoryTotal,
      subtotal,
      fuelMultiplier,
      fuelAdjusted,
      minimumCharge,
      maximumCharge,
      minimumChargeApplied,
      maximumChargeApplied,
      finalCharge,
      extraPickupCount,
      extraDropoffCount,
    };
  }, [calculatorForm, controlProfile, selectedArea, controlCategoryOptions]);

  async function getLiveQuote() {
    setSectionError("");
    setLiveQuote(null);
    try {
      const payload = {
        country: selectedArea?.country_code || countryHeader || "",
        city: selectedArea?.city_name || "",
        total_weight_kg: Number(calculatorForm.weightKg) || 0,
        pickup_count: Number(calculatorForm.pickupCount) || 1,
        dropoff_count: Number(calculatorForm.dropoffCount) || 1,
      };
      const data = await fetchJson("/logistics-partners/shipping-quote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setLiveQuote({ amount: Number(data.shipping_amount ?? 0), currency: data.currency || "AED", source: data.source || "unknown" });
    } catch (err) {
      setSectionError(err instanceof Error ? err.message : "Could not fetch live quote");
    }
  }

  const currency = controlProfile?.currency || selectedArea?.currency || "AED";

  // ── RENDER: pricing scope ────────────────────────────────────────────────
  if (isPricing) {
    return (
      <PanelContent title="Logistics Pricing Control" className="space-y-4">
        <h2 className="text-lg font-semibold text-text">zozi logistics pricing control</h2>

        <div className="flex flex-wrap gap-3">
          <label className="flex flex-col gap-1 text-xs font-semibold text-text-muted">
            Partner
            <select
              aria-label="Partner"
              value={pricingPartnerId || (partners[0] ? String(partners[0].id) : "")}
              onChange={(e) => setPricingPartnerId(e.target.value)}
              className="rounded-lg border border-border bg-surface px-2 py-1.5 text-sm text-text"
            >
              {partners.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-xs font-semibold text-text-muted">
            Service Area
            <select
              aria-label="Service Area"
              value={pricingAreaId || (areasForPartner[0] ? String(areasForPartner[0].id) : "")}
              onChange={(e) => setPricingAreaId(e.target.value)}
              className="rounded-lg border border-border bg-surface px-2 py-1.5 text-sm text-text"
            >
              {areasForPartner.map((sa) => (
                <option key={sa.id} value={sa.id}>
                  {sa.city_name}
                  {sa.zone_label ? ` — ${sa.zone_label}` : ""}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="flex flex-wrap gap-2">
          {(["profiles", "handling", "vehicles", "calculator"] as const).map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setPricingTab(key)}
              className={pricingTab === key ? "theme-btn-primary rounded-lg px-3 py-2 text-xs font-semibold" : "theme-btn-secondary rounded-lg px-3 py-2 text-xs font-semibold"}
            >
              {key === "profiles" ? "Pricing Profiles" : key === "handling" ? "Handling Rules" : key === "vehicles" ? "Load-fit Rules" : "Calculator"}
            </button>
          ))}
        </div>

        {sectionError ? <p className="text-xs text-danger">{sectionError}</p> : null}
        {sectionMessage ? <p className="text-xs text-success">{sectionMessage}</p> : null}

        {pricingTab === "profiles" && (
          <section className="space-y-3">
            <button type="button" onClick={openCreateProfile} className="theme-btn-primary rounded-lg px-3 py-2 text-xs font-semibold">
              New Pricing Profile
            </button>
            {showProfileForm && (
              <div className="theme-card space-y-2 rounded-xl border p-3">
                <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
                  <Field label="Partner" value={profileForm.partner_id} onChange={(v) => setProfileForm((f) => ({ ...f, partner_id: v }))} select>
                    <option value="">Partner</option>
                    {partners.map((p) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </Field>
                  <Field label="Service Area" value={profileForm.service_area_id} onChange={(v) => setProfileForm((f) => ({ ...f, service_area_id: v }))} select>
                    <option value="">Partner-wide</option>
                    {areasForPartner.map((sa) => (
                      <option key={sa.id} value={sa.id}>{sa.city_name}{sa.zone_label ? ` — ${sa.zone_label}` : ""}</option>
                    ))}
                  </Field>
                  <Field label="Profile Name" value={profileForm.profile_name} onChange={(v) => setProfileForm((f) => ({ ...f, profile_name: v }))} />
                  <Field label="Base In-City Fee" value={profileForm.base_in_city_fee} onChange={(v) => setProfileForm((f) => ({ ...f, base_in_city_fee: v }))} type="number" />
                  <Field label="Base Inter-City Fee" value={profileForm.base_inter_city_fee} onChange={(v) => setProfileForm((f) => ({ ...f, base_inter_city_fee: v }))} type="number" />
                  <Field label="Per-Kg Rate" value={profileForm.per_kg_rate} onChange={(v) => setProfileForm((f) => ({ ...f, per_kg_rate: v }))} type="number" />
                  <Field label="Per-Km Rate" value={profileForm.per_km_rate} onChange={(v) => setProfileForm((f) => ({ ...f, per_km_rate: v }))} type="number" />
                  <Field label="Minimum Charge" value={profileForm.minimum_charge} onChange={(v) => setProfileForm((f) => ({ ...f, minimum_charge: v }))} type="number" />
                  <Field label="Maximum Charge" value={profileForm.maximum_charge} onChange={(v) => setProfileForm((f) => ({ ...f, maximum_charge: v }))} type="number" />
                  <Field label="Fuel Multiplier" value={profileForm.fuel_multiplier} onChange={(v) => setProfileForm((f) => ({ ...f, fuel_multiplier: v }))} type="number" />
                  <Field label="Bulk Threshold Kg" value={profileForm.bulk_discount_threshold_kg} onChange={(v) => setProfileForm((f) => ({ ...f, bulk_discount_threshold_kg: v }))} type="number" />
                  <Field label="Bulk Discount %" value={profileForm.bulk_discount_percent} onChange={(v) => setProfileForm((f) => ({ ...f, bulk_discount_percent: v }))} type="number" />
                  <Field label="Currency" value={profileForm.currency} onChange={(v) => setProfileForm((f) => ({ ...f, currency: v }))} />
                </div>
                <div className="flex gap-2">
                  <button type="button" onClick={saveProfile} className="theme-btn-primary rounded-lg px-3 py-1.5 text-xs font-semibold">Save Profile</button>
                  <button type="button" onClick={() => setShowProfileForm(false)} className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold">Cancel</button>
                </div>
              </div>
            )}
            <div className="overflow-x-auto rounded-xl border">
              <table className="w-full text-sm">
                <thead className="bg-surface-2 text-text-muted">
                  <tr>
                    <th className="px-2 py-2 text-left">Profile</th>
                    <th className="px-2 py-2 text-left">Partner</th>
                    <th className="px-2 py-2 text-left">Base</th>
                    <th className="px-2 py-2 text-left">Status</th>
                    <th className="px-2 py-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {pricingProfiles.map((p) => (
                    <tr key={p.id} className="border-t">
                      <td className="px-2 py-2">{p.profile_name || `#${p.id}`}</td>
                      <td className="px-2 py-2">{partners.find((x) => x.id === p.partner_id)?.name ?? p.partner_id}</td>
                      <td className="px-2 py-2">{p.currency} {formatMoney(p.base_in_city_fee)} / {formatMoney(p.base_inter_city_fee)}</td>
                      <td className="px-2 py-2">{formatStatusLabel(p.approval_status)}</td>
                      <td className="flex flex-wrap gap-2 px-2 py-2">
                        <button type="button" onClick={() => openEditProfile(p)} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Edit</button>
                        <button type="button" onClick={() => deleteProfile(p.id)} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Delete</button>
                        {p.approval_status !== "approved" && (
                          <button type="button" onClick={() => reviewProfile(p.id, "approved")} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Approve</button>
                        )}
                        {p.approval_status !== "rejected" && (
                          <button type="button" onClick={() => reviewProfile(p.id, "rejected")} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Reject</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {pricingTab === "handling" && (
          <section className="space-y-3">
            <button type="button" onClick={openCreateCatRule} className="theme-btn-primary rounded-lg px-3 py-2 text-xs font-semibold">
              New Handling Rule
            </button>
            {showCatRuleForm && (
              <div className="theme-card space-y-2 rounded-xl border p-3">
                <div className="grid grid-cols-2 gap-2">
                  <Field label="Partner" value={catRuleForm.partner_id} onChange={(v) => setCatRuleForm((f) => ({ ...f, partner_id: v }))} select>
                    <option value="">Partner</option>
                    {partners.map((p) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </Field>
                  <Field label="Service Area" value={catRuleForm.service_area_id} onChange={(v) => setCatRuleForm((f) => ({ ...f, service_area_id: v }))} select>
                    <option value="">Partner-wide</option>
                    {areasForPartner.map((sa) => (
                      <option key={sa.id} value={sa.id}>{sa.city_name}{sa.zone_label ? ` — ${sa.zone_label}` : ""}</option>
                    ))}
                  </Field>
                  <Field label="Category" value={catRuleForm.category_name} onChange={(v) => setCatRuleForm((f) => ({ ...f, category_name: v }))} />
                  <Field label="Special Handling Fee" value={catRuleForm.special_handling_fee} onChange={(v) => setCatRuleForm((f) => ({ ...f, special_handling_fee: v }))} type="number" />
                  <Field label="Currency" value={catRuleForm.currency} onChange={(v) => setCatRuleForm((f) => ({ ...f, currency: v }))} />
                </div>
                <div className="flex gap-2">
                  <button type="button" onClick={saveCatRule} className="theme-btn-primary rounded-lg px-3 py-1.5 text-xs font-semibold">Save Rule</button>
                  <button type="button" onClick={() => setShowCatRuleForm(false)} className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold">Cancel</button>
                </div>
              </div>
            )}
            <div className="overflow-x-auto rounded-xl border">
              <table className="w-full text-sm">
                <thead className="bg-surface-2 text-text-muted">
                  <tr>
                    <th className="px-2 py-2 text-left">Category</th>
                    <th className="px-2 py-2 text-left">Partner</th>
                    <th className="px-2 py-2 text-left">Handling Fee</th>
                    <th className="px-2 py-2 text-left">Status</th>
                    <th className="px-2 py-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {categoryRules.map((r) => (
                    <tr key={r.id} className="border-t">
                      <td className="px-2 py-2">{r.category_name}</td>
                      <td className="px-2 py-2">{partners.find((x) => x.id === r.partner_id)?.name ?? r.partner_id}</td>
                      <td className="px-2 py-2">{r.currency} {formatMoney(r.special_handling_fee)}</td>
                      <td className="px-2 py-2">{formatStatusLabel(r.approval_status)}</td>
                      <td className="flex flex-wrap gap-2 px-2 py-2">
                        <button type="button" onClick={() => openEditCatRule(r)} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Edit</button>
                        <button type="button" onClick={() => deleteCatRule(r.id)} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Delete</button>
                        {r.approval_status !== "approved" && (
                          <button type="button" onClick={() => reviewCatRule(r.id, "approved")} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Approve</button>
                        )}
                        {r.approval_status !== "rejected" && (
                          <button type="button" onClick={() => reviewCatRule(r.id, "rejected")} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Reject</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {pricingTab === "vehicles" && (
          <section className="space-y-3">
            <button type="button" onClick={openCreateVehRule} className="theme-btn-primary rounded-lg px-3 py-2 text-xs font-semibold">
              New Load-fit Rule
            </button>
            {showVehRuleForm && (
              <div className="theme-card space-y-2 rounded-xl border p-3">
                <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
                  <Field label="Partner" value={vehRuleForm.partner_id} onChange={(v) => setVehRuleForm((f) => ({ ...f, partner_id: v }))} select>
                    <option value="">Partner</option>
                    {partners.map((p) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </Field>
                  <Field label="Service Area" value={vehRuleForm.service_area_id} onChange={(v) => setVehRuleForm((f) => ({ ...f, service_area_id: v }))} select>
                    <option value="">Partner-wide</option>
                    {areasForPartner.map((sa) => (
                      <option key={sa.id} value={sa.id}>{sa.city_name}{sa.zone_label ? ` — ${sa.zone_label}` : ""}</option>
                    ))}
                  </Field>
                  <Field label="Vehicle Type" value={vehRuleForm.vehicle_type} onChange={(v) => setVehRuleForm((f) => ({ ...f, vehicle_type: v }))} />
                  <Field label="Route Scope" value={vehRuleForm.route_scope} onChange={(v) => setVehRuleForm((f) => ({ ...f, route_scope: v }))} select>
                    <option value="any">any</option>
                    <option value="in_city">in_city</option>
                    <option value="inter_city">inter_city</option>
                  </Field>
                  <Field label="Cost Multiplier" value={vehRuleForm.cost_multiplier} onChange={(v) => setVehRuleForm((f) => ({ ...f, cost_multiplier: v }))} type="number" />
                  <Field label="Max Weight Kg" value={vehRuleForm.max_weight_kg} onChange={(v) => setVehRuleForm((f) => ({ ...f, max_weight_kg: v }))} type="number" />
                  <Field label="Max Volume cm3" value={vehRuleForm.max_volume_cm3} onChange={(v) => setVehRuleForm((f) => ({ ...f, max_volume_cm3: v }))} type="number" />
                  <Field label="Priority Rank" value={vehRuleForm.priority_rank} onChange={(v) => setVehRuleForm((f) => ({ ...f, priority_rank: v }))} type="number" />
                </div>
                <div className="flex gap-2">
                  <button type="button" onClick={saveVehRule} className="theme-btn-primary rounded-lg px-3 py-1.5 text-xs font-semibold">Save Rule</button>
                  <button type="button" onClick={() => setShowVehRuleForm(false)} className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold">Cancel</button>
                </div>
              </div>
            )}
            <div className="overflow-x-auto rounded-xl border">
              <table className="w-full text-sm">
                <thead className="bg-surface-2 text-text-muted">
                  <tr>
                    <th className="px-2 py-2 text-left">Vehicle</th>
                    <th className="px-2 py-2 text-left">Scope</th>
                    <th className="px-2 py-2 text-left">Multiplier</th>
                    <th className="px-2 py-2 text-left">Status</th>
                    <th className="px-2 py-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {vehicleRules.map((r) => (
                    <tr key={r.id} className="border-t">
                      <td className="px-2 py-2">{r.vehicle_type}</td>
                      <td className="px-2 py-2">{r.route_scope}</td>
                      <td className="px-2 py-2">x{r.cost_multiplier}</td>
                      <td className="px-2 py-2">{formatStatusLabel(r.approval_status)}</td>
                      <td className="flex flex-wrap gap-2 px-2 py-2">
                        <button type="button" onClick={() => openEditVehRule(r)} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Edit</button>
                        <button type="button" onClick={() => deleteVehRule(r.id)} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Delete</button>
                        {r.approval_status !== "approved" && (
                          <button type="button" onClick={() => reviewVehRule(r.id, "approved")} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Approve</button>
                        )}
                        {r.approval_status !== "rejected" && (
                          <button type="button" onClick={() => reviewVehRule(r.id, "rejected")} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Reject</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {pricingTab === "calculator" && (
          <section className="space-y-3">
            <div className="theme-card space-y-3 rounded-xl border p-3">
              <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
                <label className="flex flex-col gap-1 text-xs font-semibold text-text-muted">
                  Route Type
                  <select
                    aria-label="Route Type"
                    value={calculatorForm.routeType}
                    onChange={(e) => setCalculatorForm((f) => ({ ...f, routeType: e.target.value as "in_city" | "inter_city" }))}
                    className="rounded-lg border border-border bg-surface px-2 py-1.5 text-sm text-text"
                  >
                    <option value="in_city">In City</option>
                    <option value="inter_city">Inter City</option>
                  </select>
                </label>
                <NumField label="Weight (kg)" value={calculatorForm.weightKg} onChange={(v) => setCalculatorForm((f) => ({ ...f, weightKg: v }))} />
                {calculatorForm.routeType === "inter_city" && (
                  <NumField label="Distance (km)" value={calculatorForm.distanceKm} onChange={(v) => setCalculatorForm((f) => ({ ...f, distanceKm: v }))} />
                )}
                <NumField label="Pickup Count" value={calculatorForm.pickupCount} onChange={(v) => setCalculatorForm((f) => ({ ...f, pickupCount: v }))} />
                <NumField label="Dropoff Count" value={calculatorForm.dropoffCount} onChange={(v) => setCalculatorForm((f) => ({ ...f, dropoffCount: v }))} />
              </div>

              <div className="flex flex-wrap gap-2">
                {controlCategoryOptions.map(({ key, rule }) => (
                  <label key={key} className="flex items-center gap-1 text-xs text-text-muted">
                    <input
                      type="checkbox"
                      checked={calculatorForm.selectedCategories.includes(key)}
                      onChange={(e) =>
                        setCalculatorForm((f) => ({
                          ...f,
                          selectedCategories: e.target.checked
                            ? [...f.selectedCategories, key]
                            : f.selectedCategories.filter((k) => k !== key),
                        }))
                      }
                    />
                    {rule.category_name}
                  </label>
                ))}
                {controlCategoryOptions.length === 0 ? <span className="text-xs text-text-muted">No approved handling rules</span> : null}
              </div>

              <button type="button" onClick={getLiveQuote} className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold">
                Get Live Server Quote
              </button>
              {liveQuote ? (
                <p className="text-sm text-text">
                  Server quote: <span className="font-bold">{liveQuote.amount.toFixed(2)} {liveQuote.currency}</span> ({liveQuote.source})
                </p>
              ) : null}
            </div>

            <div className="theme-card rounded-xl border p-3 text-sm">
              <h3 className="text-sm font-bold text-text">Quote Breakdown ({currency})</h3>
              <div className="mt-2 space-y-1">
                <Row label="Base Fee" value={calculatorBreakdown.baseFee} />
                <Row label={`Weight (${Number(calculatorForm.weightKg || 0)}kg)`} value={calculatorBreakdown.weightFee} />
                {calculatorForm.routeType === "inter_city" && (
                  <Row label={`Distance (${Number(calculatorForm.distanceKm || 0)}km)`} value={calculatorBreakdown.distanceFee} />
                )}
                <Row label={`Extra Pickups (${calculatorBreakdown.extraPickupCount})`} value={calculatorBreakdown.pickupFee} />
                <Row label={`Extra Drop-offs (${calculatorBreakdown.extraDropoffCount})`} value={calculatorBreakdown.dropoffFee} />
                <Row label="Handling Amount" value={calculatorBreakdown.categoryTotal} />
                <Row label="Subtotal" value={calculatorBreakdown.subtotal} />
                <Row label={`After Fuel (x${calculatorBreakdown.fuelMultiplier.toFixed(2)})`} value={calculatorBreakdown.fuelAdjusted} />
                {calculatorBreakdown.minimumChargeApplied && (
                  <Row label={`Minimum Floor (${calculatorBreakdown.minimumCharge != null ? Number(calculatorBreakdown.minimumCharge).toFixed(2) : "0.00"})`} value={calculatorBreakdown.fuelAdjusted < (calculatorBreakdown.minimumCharge ?? 0) ? (calculatorBreakdown.minimumCharge ?? 0) : calculatorBreakdown.fuelAdjusted} />
                )}
                {calculatorBreakdown.maximumChargeApplied && (
                  <Row label="Maximum Cap Applied" value={calculatorBreakdown.finalCharge} />
                )}
                <div className="flex items-center justify-between border-t border-border pt-2 font-bold text-text">
                  <span>Final Charge</span>
                  <span>{calculatorBreakdown.finalCharge.toFixed(2)} {currency}</span>
                </div>
              </div>
            </div>
          </section>
        )}

        <p className="text-[11px] text-text-faint">
          {pricingProfiles.length} pricing profile(s) · {vehicleRules.length} vehicle rule(s) · {categoryRules.length} handling rule(s) loaded.
        </p>
      </PanelContent>
    );
  }

  // ── RENDER: partners scope ────────────────────────────────────────────────
  return (
    <PanelContent title="Logistics Partners" className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {(["partners", "service-areas", "city-distances"] as const).map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={tab === key ? "theme-btn-primary rounded-lg px-3 py-2 text-xs font-semibold" : "theme-btn-secondary rounded-lg px-3 py-2 text-xs font-semibold"}
          >
            {key === "partners" ? "Partners" : key === "service-areas" ? "Service Areas" : "City Distances"}
          </button>
        ))}
      </div>

      {sectionError ? <p className="text-xs text-red-600">{sectionError}</p> : null}
      {sectionMessage ? <p className="text-xs text-success">{sectionMessage}</p> : null}

      {tab === "partners" && (
        <div className="space-y-3">
          {selectedPartnerIds.length > 0 && (
            <button type="button" onClick={bulkApprove} className="theme-btn-primary rounded-lg px-3 py-2 text-xs font-semibold">
              Approve Selected
            </button>
          )}
          <div className="overflow-x-auto rounded-xl border">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 text-text-muted">
                <tr>
                  <th className="px-2 py-2 text-left">Select</th>
                  <th className="px-2 py-2 text-left">Partner</th>
                  <th className="px-2 py-2 text-left">Code</th>
                  <th className="px-2 py-2 text-left">Coverage</th>
                  <th className="px-2 py-2 text-left">Status</th>
                  <th className="px-2 py-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {partners.map((p) => (
                  <tr key={p.id} className="border-t">
                    <td className="px-2 py-2">
                      <input
                        type="checkbox"
                        aria-label={`Select row ${p.id}`}
                        checked={selectedPartnerIds.includes(p.id)}
                        onChange={() => toggleSelect(p.id)}
                      />
                    </td>
                    <td className="px-2 py-2">{p.name}</td>
                    <td className="px-2 py-2">{p.code}</td>
                    <td className="px-2 py-2">
                      {[p.city, p.country].filter(Boolean).join(", ")}
                    </td>
                    <td className="px-2 py-2">
                      {p.verification_status} / {p.status}
                    </td>
                    <td className="flex flex-wrap gap-2 px-2 py-2">
                      {p.verification_status !== "approved" && (
                        <button type="button" onClick={() => approvePartner(p.id)} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">
                          Approve
                        </button>
                      )}
                      {p.status === "active" && (
                        <button type="button" onClick={() => suspendPartner(p.id)} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">
                          Suspend
                        </button>
                      )}
                      <button type="button" onClick={() => deletePartner(p.id)} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "service-areas" && (
        <div className="space-y-4">
          <button type="button" onClick={openCreateArea} className="theme-btn-primary rounded-lg px-3 py-2 text-xs font-semibold">
            New Service Area
          </button>
          {showAreaForm && (
            <div className="theme-card space-y-2 rounded-xl border p-3">
              <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
                <Field label="Partner" value={areaForm.partner_id} onChange={(v) => setAreaForm((f) => ({ ...f, partner_id: v }))} select>
                  <option value="">Partner</option>
                  {partners.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </Field>
                <Field label="Country Code" value={areaForm.country_code} onChange={(v) => setAreaForm((f) => ({ ...f, country_code: v }))} />
                <Field label="Country Name" value={areaForm.country_name} onChange={(v) => setAreaForm((f) => ({ ...f, country_name: v }))} />
                <Field label="City" value={areaForm.city_name} onChange={(v) => setAreaForm((f) => ({ ...f, city_name: v }))} />
                <Field label="Zone Label" value={areaForm.zone_label} onChange={(v) => setAreaForm((f) => ({ ...f, zone_label: v }))} />
                <Field label="Base Charge" value={areaForm.charge_amount} onChange={(v) => setAreaForm((f) => ({ ...f, charge_amount: v }))} type="number" />
                <Field label="Minimum Charge" value={areaForm.minimum_charge} onChange={(v) => setAreaForm((f) => ({ ...f, minimum_charge: v }))} type="number" />
                <Field label="Per-Kg Rate" value={areaForm.per_kg_rate} onChange={(v) => setAreaForm((f) => ({ ...f, per_kg_rate: v }))} type="number" />
                <Field label="Per-Km Rate" value={areaForm.per_km_rate} onChange={(v) => setAreaForm((f) => ({ ...f, per_km_rate: v }))} type="number" />
                <Field label="Fuel Multiplier" value={areaForm.fuel_multiplier} onChange={(v) => setAreaForm((f) => ({ ...f, fuel_multiplier: v }))} type="number" />
                <Field label="Pickup Charge" value={areaForm.pickup_charge} onChange={(v) => setAreaForm((f) => ({ ...f, pickup_charge: v }))} type="number" />
                <Field label="Dropoff Charge" value={areaForm.dropoff_charge} onChange={(v) => setAreaForm((f) => ({ ...f, dropoff_charge: v }))} type="number" />
                <Field label="Latitude" value={areaForm.latitude} onChange={(v) => setAreaForm((f) => ({ ...f, latitude: v }))} type="number" />
                <Field label="Longitude" value={areaForm.longitude} onChange={(v) => setAreaForm((f) => ({ ...f, longitude: v }))} type="number" />
                <Field label="Delivery Days Min" value={areaForm.delivery_days_min} onChange={(v) => setAreaForm((f) => ({ ...f, delivery_days_min: v }))} type="number" />
                <Field label="Delivery Days Max" value={areaForm.delivery_days_max} onChange={(v) => setAreaForm((f) => ({ ...f, delivery_days_max: v }))} type="number" />
                <Field label="Currency" value={areaForm.currency} onChange={(v) => setAreaForm((f) => ({ ...f, currency: v }))} />
              </div>
              <div className="flex gap-2">
                <button type="button" onClick={saveArea} className="theme-btn-primary rounded-lg px-3 py-1.5 text-xs font-semibold">Save Area</button>
                <button type="button" onClick={() => setShowAreaForm(false)} className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold">Cancel</button>
              </div>
            </div>
          )}

          <div className="overflow-x-auto rounded-xl border">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 text-text-muted">
                <tr>
                  <th className="px-2 py-2 text-left">Area</th>
                  <th className="px-2 py-2 text-left">Base</th>
                  <th className="px-2 py-2 text-left">Stop fees</th>
                  <th className="px-2 py-2 text-left">Status</th>
                  <th className="px-2 py-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {serviceAreas.map((area) => (
                  <tr key={area.id} className="border-t">
                    <td className="px-2 py-2">
                      {area.city_name}
                      {area.zone_label ? ` — ${area.zone_label}` : ""}
                    </td>
                    <td className="px-2 py-2">
                      {area.currency} {formatMoney(area.charge_amount)}
                    </td>
                    <td className="px-2 py-2">pickup {formatMoney(area.pickup_charge)}/stop</td>
                    <td className="px-2 py-2">{formatStatusLabel(area.approval_status)}</td>
                    <td className="flex flex-wrap gap-2 px-2 py-2">
                      <button type="button" onClick={() => openEditArea(area)} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Edit</button>
                      <button type="button" onClick={() => deleteArea(area.id)} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Delete</button>
                      {area.approval_status !== "approved" && (
                        <button type="button" onClick={() => reviewArea(area.id, "approved")} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Approve</button>
                      )}
                      {area.approval_status !== "rejected" && (
                        <button type="button" onClick={() => reviewArea(area.id, "rejected")} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Reject</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <section className="theme-card rounded-xl border p-3">
            <h3 className="text-sm font-bold text-text">Coverage and Route Board</h3>
            <h4 className="mt-3 text-xs font-bold uppercase tracking-wide text-text-faint">Rows that still need coordinates</h4>
            <ul className="mt-1 space-y-1 text-sm">
              {serviceAreas.filter((sa) => !hasCoordinates(sa.latitude ?? null, sa.longitude ?? null)).length === 0 ? (
                <li className="text-text-faint">All service areas have coordinates.</li>
              ) : (
                serviceAreas
                  .filter((sa) => !hasCoordinates(sa.latitude ?? null, sa.longitude ?? null))
                  .map((sa) => (
                    <li key={sa.id} className="rounded-lg bg-warning/10 px-2 py-1.5 text-warning">
                      {sa.city_name}
                      {sa.zone_label ? ` — ${sa.zone_label}` : ""}:{" "}
                      <span>Missing service-area latitude or longitude.</span>
                    </li>
                  ))
              )}
            </ul>
          </section>
        </div>
      )}

      {tab === "city-distances" && (
        <div className="space-y-4">
          <button type="button" onClick={openCreateDistance} className="theme-btn-primary rounded-lg px-3 py-2 text-xs font-semibold">
            New Route
          </button>
          {showDistanceForm && (
            <div className="theme-card space-y-2 rounded-xl border p-3">
              <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
                <Field label="Origin Country" value={distanceForm.origin_country_code} onChange={(v) => setDistanceForm((f) => ({ ...f, origin_country_code: v }))} />
                <Field label="Origin City" value={distanceForm.origin_city_name} onChange={(v) => setDistanceForm((f) => ({ ...f, origin_city_name: v }))} />
                <Field label="Dest Country" value={distanceForm.destination_country_code} onChange={(v) => setDistanceForm((f) => ({ ...f, destination_country_code: v }))} />
                <Field label="Dest City" value={distanceForm.destination_city_name} onChange={(v) => setDistanceForm((f) => ({ ...f, destination_city_name: v }))} />
                <Field label="Distance (km)" value={distanceForm.distance_km} onChange={(v) => setDistanceForm((f) => ({ ...f, distance_km: v }))} type="number" />
                <Field label="Notes" value={distanceForm.notes} onChange={(v) => setDistanceForm((f) => ({ ...f, notes: v }))} />
              </div>
              <div className="flex gap-2">
                <button type="button" onClick={saveDistance} className="theme-btn-primary rounded-lg px-3 py-1.5 text-xs font-semibold">Save Route</button>
                <button type="button" onClick={() => setShowDistanceForm(false)} className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold">Cancel</button>
              </div>
            </div>
          )}

          <div className="overflow-x-auto rounded-xl border">
            <table className="w-full text-sm">
              <thead className="bg-surface-2 text-text-muted">
                <tr>
                  <th className="px-2 py-2 text-left">Origin</th>
                  <th className="px-2 py-2 text-left">Destination</th>
                  <th className="px-2 py-2 text-left">Distance</th>
                  <th className="px-2 py-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {cityDistances.map((d) => (
                  <tr key={d.id} className="border-t">
                    <td className="px-2 py-2">{d.origin_city_name} ({d.origin_country_code})</td>
                    <td className="px-2 py-2">{d.destination_city_name} ({d.destination_country_code})</td>
                    <td className="px-2 py-2">{formatMoney(d.distance_km)} km</td>
                    <td className="flex flex-wrap gap-2 px-2 py-2">
                      <button type="button" onClick={() => openEditDistance(d)} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Edit</button>
                      <button type="button" onClick={() => deleteDistance(d.id)} className="theme-btn-secondary rounded-lg px-2 py-1 text-xs font-semibold">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </PanelContent>
  );
}

// ── Small form-field helpers ──────────────────────────────────────────────────
function Field({
  label,
  value,
  onChange,
  type,
  select,
  children,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  select?: boolean;
  children?: React.ReactNode;
}) {
  const common = "w-full rounded-lg border border-border bg-surface px-2 py-1.5 text-sm text-text";
  return (
    <label className="flex flex-col gap-1 text-xs font-semibold text-text-muted">
      {label}
      {select ? (
        <select aria-label={label} value={value} onChange={(e) => onChange(e.target.value)} className={common}>
          {children}
        </select>
      ) : (
        <input aria-label={label} type={type || "text"} value={value} onChange={(e) => onChange(e.target.value)} className={common} />
      )}
    </label>
  );
}

function NumField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <Field label={label} value={value} onChange={onChange} type="number" />
  );
}

function Row({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span>{label}</span>
      <span>{value.toFixed(2)}</span>
    </div>
  );
}
