"use client";

import { Button } from "@/components/ui/Button";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  BadgeCheck,
  Building2,
  CheckCircle,
  Clock,
  Clock3,
  FileText,
  Globe,
  Info,
  Link2,
  Loader2,
  Lock,
  MapPin,
  MapPinned,
  PackageCheck,
  Phone,
  Plus,
  RefreshCw,
  Save,
  Search,
  Shield,
  ShieldCheck,
  Trash2,
  Truck,
  Upload,
  User,
  XCircle,
} from "@/lib/icons";
import { motion } from "framer-motion";
import LogisticsPartnerLayout from "@/components/LogisticsPartnerLayout";
import { PanelContent, PanelHero, PanelLoadingState } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

type TabKey = "overview" | "profile" | "coverage" | "operations";

type SocialLinks = {
  website?: string;
  linkedin?: string;
  instagram?: string;
  facebook?: string;
};

type PartnerProfile = {
  id: number;
  name: string;
  code: string;
  contact_name?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  website?: string | null;
  business_type?: string | null;
  country?: string | null;
  region?: string | null;
  city?: string | null;
  address?: string | null;
  postal_code?: string | null;
  tax_id?: string | null;
  bio?: string | null;
  about_us?: string | null;
  logo_url?: string | null;
  banner_url?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  verification_status: string;
  verification_note?: string | null;
  status: string;
  is_terms_accepted: boolean;
  terms_version?: string | null;
  service_types?: string[];
  coverage_regions?: string[];
  social_links?: SocialLinks;
};

type ServiceArea = {
  id: number;
  country_code: string;
  country_name: string;
  city_name?: string | null;
  origin_city?: string | null;
  zone_label?: string | null;
  charge_amount: number;
  minimum_charge?: number | null;
  per_kg_rate?: number | null;
  per_km_rate?: number | null;
  fuel_multiplier?: number | null;
  pickup_charge?: number | null;
  dropoff_charge?: number | null;
  currency: string;
  latitude?: number | null;
  longitude?: number | null;
  delivery_days_min?: number | null;
  delivery_days_max?: number | null;
  is_active: boolean;
  approval_status: string;
  review_note?: string | null;
};

type PricingProfile = {
  id: number;
  partner_id: number;
  service_area_id?: number | null;
  profile_name?: string | null;
  base_in_city_fee?: number | null;
  base_inter_city_fee?: number | null;
  per_km_rate?: number | null;
  per_kg_rate?: number | null;
  minimum_charge?: number | null;
  fuel_multiplier?: number | null;
  bulk_discount_threshold_kg?: number | null;
  bulk_discount_percent?: number | null;
  currency: string;
  is_active: boolean;
  approval_status: string;
  review_note?: string | null;
};

type CategoryPricingRule = {
  id: number;
  partner_id: number;
  service_area_id?: number | null;
  category_name: string;
  flat_fee_override?: number | null;
  special_handling_fee?: number | null;
  currency: string;
  is_active: boolean;
  approval_status: string;
  review_note?: string | null;
};

type VehicleRule = {
  id: number;
  partner_id: number;
  service_area_id?: number | null;
  route_scope: string;
  vehicle_type: string;
  max_weight_kg?: number | null;
  max_volume_cm3?: number | null;
  cost_multiplier: number;
  priority_rank: number;
  is_active: boolean;
  approval_status: string;
  review_note?: string | null;
};

interface LPBankAccount {
  id?: number;
  beneficiary_name?: string;
  bank_name?: string;
  branch_name?: string;
  account_number?: string;
  iban?: string;
  swift_code?: string;
  routing_number?: string;
  bank_country?: string;
  currency?: string;
  verification_status?: string;
  verification_note?: string | null;
}

interface LPDocument {
  id: number;
  document_type?: string;
  document_name?: string;
  file_url?: string | null;
  expires_at?: string | null;
  status: string;
  review_note?: string | null;
}

const EMPTY_LP_BANK_FORM = {
  beneficiary_name: "",
  bank_name: "",
  branch_name: "",
  account_number: "",
  iban: "",
  swift_code: "",
  routing_number: "",
  bank_country: "",
  currency: "OMR",
};

const LP_DOC_TYPES = [
  { value: "trade_license", label: "Trade License" },
  { value: "vat_certificate", label: "VAT Certificate" },
  { value: "insurance", label: "Insurance Certificate" },
  { value: "bank_statement", label: "Bank Statement" },
  { value: "id_document", label: "ID / Passport" },
  { value: "other", label: "Other" },
];

const SERVICE_TYPES = [
  { value: "standard", label: "Standard Delivery" },
  { value: "express", label: "Express Delivery" },
  { value: "same_day", label: "Same Day" },
  { value: "cross_border", label: "Cross Border" },
  { value: "returns", label: "Returns Handling" },
  { value: "cold_chain", label: "Cold Chain" },
  { value: "fragile", label: "Fragile Goods" },
];

const COUNTRY_OPTIONS = [
  "Oman",
  "United Arab Emirates",
  "Saudi Arabia",
  "Qatar",
  "Kuwait",
  "Bahrain",
  "Jordan",
  "Egypt",
  "India",
  "Pakistan",
  "United Kingdom",
  "United States",
];

const TABS: Array<{ key: TabKey; label: string; icon: typeof BadgeCheck; hint: string }> = [
  { key: "overview", label: "Overview", icon: BadgeCheck, hint: "Approval status, public preview, and live queue snapshot" },
  { key: "profile", label: "Business Profile", icon: Building2, hint: "Partner identity, location, and public-facing information" },
  { key: "coverage", label: "Delivery Settings", icon: MapPinned, hint: "Service areas, pricing profiles, handling rules, and load-fit rules" },
  { key: "operations", label: "Operations & Compliance", icon: ShieldCheck, hint: "Security, documents, banking, terms, and partner guidance" },
];

const STATUS_CHIP: Record<string, string> = {
  approved: "theme-chip-success",
  active: "theme-chip-success",
  under_review: "theme-chip-info",
  pending: "theme-chip-warning",
  pending_onboarding: "theme-chip-warning",
  rejected: "theme-chip-danger",
  suspended: "theme-chip-danger",
};

const GUIDE_CHECKLIST = [
  "Profile approval controls whether this partner can become public and searchable.",
  "Approved service areas decide whether customer cart and checkout use your delivery charge.",
  "Prepared shipments appear in the pickup queue only when the order destination matches an approved service area.",
  "Editing a previously approved profile or charge row sends it back through admin review before it becomes active again.",
];

const TERMS = [
  "Keep service coverage accurate. Charges only go live after admin approval.",
  "Only approved profile changes and approved city or country charge rows are reflected to customer cart, checkout, and shipment pickup eligibility.",
  "Rejected rate rows stay visible to you for correction, but they do not affect customer totals or prepared shipment queues.",
  "GPS coordinates should match your operational delivery location so routing and map-based support remain accurate.",
];

const PARTNER_PERMISSION_CARDS = [
  {
    title: "You can manage",
    body: "Your own profile, service areas, pricing profiles, handling rules, load-fit rules, banking details, and shipment updates for parcels assigned to your portal.",
  },
  {
    title: "Admin must approve",
    body: "Profile visibility, every charge row, pricing profile, handling rule, and load-fit rule. Pending items stay visible here but do not affect quotes or pickup eligibility.",
  },
  {
    title: "Operational workflow",
    body: "Supplier prepares parcel, eligible partner sees it in Shipments, partner confirms Picking Up, Scan confirms field handoff, then delivery closes as Delivered, Failed, or Returned.",
  },
];

const emptyProfile = (): PartnerProfile => ({
  id: 0,
  name: "",
  code: "",
  contact_name: "",
  contact_email: "",
  contact_phone: "",
  website: "",
  business_type: "",
  country: "",
  region: "",
  city: "",
  address: "",
  postal_code: "",
  tax_id: "",
  bio: "",
  about_us: "",
  logo_url: "",
  banner_url: "",
  latitude: null,
  longitude: null,
  verification_status: "pending",
  verification_note: "",
  status: "pending_onboarding",
  is_terms_accepted: false,
  terms_version: null,
  service_types: [],
  coverage_regions: [],
  social_links: {},
});

const emptyArea = () => ({
  country_name: "",
  country_code: "",
  city_name: "",
  origin_city: "",
  zone_label: "",
  charge_amount: "",
  minimum_charge: "",
  per_kg_rate: "",
  per_km_rate: "",
  fuel_multiplier: "",
  pickup_charge: "",
  dropoff_charge: "",
  currency: "OMR",
  latitude: "",
  longitude: "",
  delivery_days_min: "",
  delivery_days_max: "",
  is_active: true,
});

const emptyPricingProfile = () => ({
  service_area_id: "",
  profile_name: "",
  base_in_city_fee: "",
  base_inter_city_fee: "",
  per_km_rate: "",
  per_kg_rate: "",
  minimum_charge: "",
  fuel_multiplier: "",
  bulk_discount_threshold_kg: "",
  bulk_discount_percent: "",
  currency: "OMR",
  is_active: true,
});

const emptyCategoryRule = () => ({
  service_area_id: "",
  category_name: "",
  flat_fee_override: "",
  special_handling_fee: "",
  currency: "OMR",
  is_active: true,
});

const emptyVehicleRule = () => ({
  service_area_id: "",
  route_scope: "any",
  vehicle_type: "",
  max_weight_kg: "",
  max_volume_cm3: "",
  cost_multiplier: "1",
  priority_rank: "100",
  is_active: true,
});

const normalizeProfile = (payload: Partial<PartnerProfile> | null | undefined): PartnerProfile => ({
  ...emptyProfile(),
  ...payload,
  service_types: Array.isArray(payload?.service_types) ? payload?.service_types : [],
  coverage_regions: Array.isArray(payload?.coverage_regions) ? payload?.coverage_regions : [],
  social_links: payload?.social_links && typeof payload.social_links === "object" ? payload.social_links : {},
});

const titleCase = (value: string) => value.replace(/_/g, " ");
const joinSummary = (parts: Array<string | null | undefined | false>) => parts.filter(Boolean).join(" · ");
const describeAreaLocation = (area: ServiceArea) => [area.origin_city ? `from ${area.origin_city}` : null, area.city_name, area.country_name, area.country_code].filter(Boolean).join(" · ");
const describeServiceArea = (area: ServiceArea) => joinSummary([
  `${area.currency} ${area.charge_amount.toFixed(2)}`,
  area.minimum_charge != null ? `min ${area.minimum_charge.toFixed(2)}` : null,
  area.per_kg_rate != null ? `${area.per_kg_rate}/kg` : null,
  area.per_km_rate != null ? `${area.per_km_rate}/km` : null,
  area.pickup_charge != null ? `pickup ${area.pickup_charge.toFixed(2)}/stop` : null,
  area.dropoff_charge != null ? `dropoff ${area.dropoff_charge.toFixed(2)}/stop` : null,
  area.fuel_multiplier != null && area.fuel_multiplier !== 1 ? `runtime x${area.fuel_multiplier}` : null,
  area.delivery_days_min != null || area.delivery_days_max != null ? `${area.delivery_days_min ?? "?"}-${area.delivery_days_max ?? "?"} days` : null,
]);
const describePricingProfile = (pricingProfile: PricingProfile) => joinSummary([
  pricingProfile.currency,
  pricingProfile.base_in_city_fee != null ? `in-city ${pricingProfile.base_in_city_fee.toFixed(2)}` : "in-city inherit",
  pricingProfile.base_inter_city_fee != null ? `inter-city ${pricingProfile.base_inter_city_fee.toFixed(2)}` : null,
  pricingProfile.per_kg_rate != null ? `${pricingProfile.per_kg_rate}/kg` : null,
  pricingProfile.per_km_rate != null ? `${pricingProfile.per_km_rate}/km` : null,
  pricingProfile.minimum_charge != null ? `min ${pricingProfile.minimum_charge.toFixed(2)}` : null,
  pricingProfile.fuel_multiplier != null && pricingProfile.fuel_multiplier !== 1 ? `runtime x${pricingProfile.fuel_multiplier}` : null,
  pricingProfile.bulk_discount_percent != null ? `${pricingProfile.bulk_discount_percent}% weight discount on weight fee` : null,
]);
const describeCategoryRule = (rule: CategoryPricingRule) => {
  const handlingAmount = Math.max(Number(rule.flat_fee_override ?? 0), Number(rule.special_handling_fee ?? 0));
  return joinSummary([
    rule.currency,
    handlingAmount > 0 ? `handling ${handlingAmount.toFixed(2)}` : null,
  ]);
};
const describeVehicleRule = (rule: VehicleRule) => joinSummary([
  `${titleCase(rule.route_scope)} route`,
  rule.max_weight_kg != null ? `up to ${rule.max_weight_kg}kg` : null,
  rule.max_volume_cm3 != null ? `up to ${rule.max_volume_cm3}cm3` : null,
  `x${rule.cost_multiplier} cost`,
  `priority ${rule.priority_rank}`,
]);

export default function LogisticsPartnerProfilePage() {
  const { user, isLoading: authLoading } = useAuth();
  const [tab, setTab] = useState<TabKey>("overview");
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingArea, setSavingArea] = useState(false);
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [profile, setProfile] = useState<PartnerProfile>(emptyProfile);
  const [serviceAreas, setServiceAreas] = useState<ServiceArea[]>([]);
  const [pricingProfiles, setPricingProfiles] = useState<PricingProfile[]>([]);
  const [categoryRules, setCategoryRules] = useState<CategoryPricingRule[]>([]);
  const [vehicleRules, setVehicleRules] = useState<VehicleRule[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [editingAreaId, setEditingAreaId] = useState<number | null>(null);
  const [areaForm, setAreaForm] = useState(emptyArea);
  const [editingPricingProfileId, setEditingPricingProfileId] = useState<number | null>(null);
  const [pricingProfileForm, setPricingProfileForm] = useState(emptyPricingProfile);
  const [savingPricingProfile, setSavingPricingProfile] = useState(false);
  const [editingCategoryRuleId, setEditingCategoryRuleId] = useState<number | null>(null);
  const [categoryRuleForm, setCategoryRuleForm] = useState(emptyCategoryRule);
  const [savingCategoryRule, setSavingCategoryRule] = useState(false);
  const [editingVehicleRuleId, setEditingVehicleRuleId] = useState<number | null>(null);
  const [vehicleRuleForm, setVehicleRuleForm] = useState(emptyVehicleRule);
  const [savingVehicleRule, setSavingVehicleRule] = useState(false);
  const [coverageSearch, setCoverageSearch] = useState("");
  const [countrySearch, setCountrySearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | "approved" | "pending" | "rejected">("all");

  // Security tab state
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [pwSaving, setPwSaving] = useState(false);

  // Documents tab state
  const [lpDocs, setLpDocs] = useState<LPDocument[]>([]);
  const [lpDocsLoading, setLpDocsLoading] = useState(false);
  const [lpDocForm, setLpDocForm] = useState({ document_type: "trade_license", document_name: "", expires_at: "" });
  const [selectedLpDocFile, setSelectedLpDocFile] = useState<File | null>(null);
  const [lpDocUploading, setLpDocUploading] = useState(false);
  const [lpDocDeleteId, setLpDocDeleteId] = useState<number | null>(null);

  // Banking tab state
  const [lpBankAccount, setLpBankAccount] = useState<LPBankAccount | null>(null);
  const [lpBankForm, setLpBankForm] = useState(EMPTY_LP_BANK_FORM);
  const [lpBankSaving, setLpBankSaving] = useState(false);

  const approvedAreas = useMemo(() => serviceAreas.filter((area) => area.approval_status === "approved").length, [serviceAreas]);
  const pendingAreas = useMemo(() => serviceAreas.filter((area) => area.approval_status === "pending").length, [serviceAreas]);
  const rejectedAreas = useMemo(() => serviceAreas.filter((area) => area.approval_status === "rejected").length, [serviceAreas]);
  const approvedPricingProfiles = useMemo(() => pricingProfiles.filter((profile) => profile.approval_status === "approved").length, [pricingProfiles]);
  const pendingPricingProfiles = useMemo(() => pricingProfiles.filter((profile) => profile.approval_status === "pending").length, [pricingProfiles]);
  const approvedCategoryRules = useMemo(() => categoryRules.filter((rule) => rule.approval_status === "approved").length, [categoryRules]);
  const pendingCategoryRules = useMemo(() => categoryRules.filter((rule) => rule.approval_status === "pending").length, [categoryRules]);
  const approvedVehicleRules = useMemo(() => vehicleRules.filter((rule) => rule.approval_status === "approved").length, [vehicleRules]);
  const pendingVehicleRules = useMemo(() => vehicleRules.filter((rule) => rule.approval_status === "pending").length, [vehicleRules]);

  const filteredCountries = useMemo(() => {
    const query = countrySearch.trim().toLowerCase();
    if (!query) return COUNTRY_OPTIONS;
    return COUNTRY_OPTIONS.filter((country) => country.toLowerCase().includes(query));
  }, [countrySearch]);

  const filteredAreas = useMemo(() => {
    const query = coverageSearch.trim().toLowerCase();
    return serviceAreas.filter((area) => {
      const matchesStatus = statusFilter === "all" || area.approval_status === statusFilter;
      const haystack = [area.country_name, area.country_code, area.city_name, area.zone_label].join(" ").toLowerCase();
      const matchesSearch = !query || haystack.includes(query);
      return matchesStatus && matchesSearch;
    });
  }, [coverageSearch, serviceAreas, statusFilter]);

  const readiness = useMemo(() => {
    const checks = [
      { label: "Company name", done: Boolean(profile.name?.trim()) },
      { label: "Contact email", done: Boolean(profile.contact_email?.trim()) },
      { label: "Contact phone", done: Boolean(profile.contact_phone?.trim()) },
      { label: "Base city and country", done: Boolean(profile.city?.trim() && profile.country?.trim()) },
      { label: "Terms accepted", done: profile.is_terms_accepted },
      { label: "At least one approved or pending rate", done: serviceAreas.length > 0 },
    ];
    const completed = checks.filter((check) => check.done).length;
    return { checks, completed, total: checks.length };
  }, [profile, serviceAreas.length]);

  const canLoadPartnerData = !authLoading && user?.role === "logistics_partner";

  const fetchLpDocuments = useCallback(async () => {
    if (!canLoadPartnerData) return;
    setLpDocsLoading(true);
    try {
      const res = await apiFetch("/logistics-partner/me/docs");
      if (res.ok) setLpDocs(await res.json());
    } catch {
      // silently ignore doc fetch errors
    } finally {
      setLpDocsLoading(false);
    }
  }, [canLoadPartnerData]);

  const loadData = useCallback(async () => {
    if (!canLoadPartnerData) return;
    setLoading(true);
    setError("");
    try {
      const [profileResponse, areasResponse, pricingProfilesResponse, categoryRulesResponse, vehicleRulesResponse, bankResponse] = await Promise.all([
        apiFetch("/logistics-partner/profile"),
        apiFetch("/logistics-partner/service-areas"),
        apiFetch("/logistics-partner/pricing-profiles"),
        apiFetch("/logistics-partner/category-rules"),
        apiFetch("/logistics-partner/vehicle-rules"),
        apiFetch("/logistics-partner/me/bank-account"),
      ]);
      if (!profileResponse.ok) {
        throw new Error("Could not load partner profile");
      }
      const nextProfile = await profileResponse.json();
      const nextAreas = areasResponse.ok ? await areasResponse.json() : [];
      const nextPricingProfiles = pricingProfilesResponse.ok ? await pricingProfilesResponse.json() : [];
      const nextCategoryRules = categoryRulesResponse.ok ? await categoryRulesResponse.json() : [];
      const nextVehicleRules = vehicleRulesResponse.ok ? await vehicleRulesResponse.json() : [];
      setProfile(normalizeProfile(nextProfile));
      setServiceAreas(Array.isArray(nextAreas) ? nextAreas : []);
      setPricingProfiles(Array.isArray(nextPricingProfiles) ? nextPricingProfiles : []);
      setCategoryRules(Array.isArray(nextCategoryRules) ? nextCategoryRules : []);
      setVehicleRules(Array.isArray(nextVehicleRules) ? nextVehicleRules : []);
      if (bankResponse.ok) {
        const bankPayload: LPBankAccount = await bankResponse.json();
        if (bankPayload?.id) {
          setLpBankAccount(bankPayload);
          setLpBankForm({
            beneficiary_name: bankPayload.beneficiary_name || "",
            bank_name: bankPayload.bank_name || "",
            branch_name: bankPayload.branch_name || "",
            account_number: bankPayload.account_number || "",
            iban: bankPayload.iban || "",
            swift_code: bankPayload.swift_code || "",
            routing_number: bankPayload.routing_number || "",
            bank_country: bankPayload.bank_country || "",
            currency: bankPayload.currency || "OMR",
          });
        }
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Could not load logistics partner profile");
    } finally {
      setLoading(false);
    }
  }, [canLoadPartnerData]);

  useEffect(() => {
    if (canLoadPartnerData) {
      void loadData();
    }
  }, [canLoadPartnerData, loadData]);

  useEffect(() => {
    if (canLoadPartnerData && tab === "operations") {
      void fetchLpDocuments();
    }
  }, [canLoadPartnerData, fetchLpDocuments, tab]);

  const setProfileField = (field: keyof PartnerProfile, value: string) => {
    setProfile((current) => ({ ...current, [field]: value }));
  };

  const setSocialLink = (field: keyof SocialLinks, value: string) => {
    setProfile((current) => ({
      ...current,
      social_links: {
        ...(current.social_links || {}),
        [field]: value,
      },
    }));
  };

  const toggleServiceType = (serviceType: string) => {
    setProfile((current) => ({
      ...current,
      service_types: current.service_types?.includes(serviceType)
        ? current.service_types.filter((value) => value !== serviceType)
        : [...(current.service_types || []), serviceType],
    }));
  };

  const toggleCoverageRegion = (country: string) => {
    setProfile((current) => ({
      ...current,
      coverage_regions: current.coverage_regions?.includes(country)
        ? current.coverage_regions.filter((value) => value !== country)
        : [...(current.coverage_regions || []), country],
    }));
  };

  const handleSaveProfile = async () => {
    setSavingProfile(true);
    setMessage("");
    setError("");
    try {
      const response = await apiFetch("/logistics-partner/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: profile.name,
          contact_name: profile.contact_name,
          contact_email: profile.contact_email,
          contact_phone: profile.contact_phone,
          website: profile.website,
          business_type: profile.business_type,
          country: profile.country,
          region: profile.region,
          city: profile.city,
          address: profile.address,
          postal_code: profile.postal_code,
          tax_id: profile.tax_id,
          bio: profile.bio,
          about_us: profile.about_us,
          logo_url: profile.logo_url,
          banner_url: profile.banner_url,
          latitude: profile.latitude,
          longitude: profile.longitude,
          coverage_regions: profile.coverage_regions || [],
          service_types: profile.service_types || [],
          social_links: profile.social_links || {},
        }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Could not save logistics partner profile");
      }
      const nextProfile = await response.json();
      setProfile(normalizeProfile(nextProfile));
      setMessage("Profile changes saved. Admin approval is required before approved changes go live.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Could not save profile");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleAcceptTerms = async () => {
    setReviewSubmitting(true);
    setMessage("");
    setError("");
    try {
      const response = await apiFetch("/logistics-partner/profile/terms/accept", { method: "POST" });
      if (!response.ok) {
        throw new Error("Could not accept logistics partner terms");
      }
      await loadData();
      setMessage("Terms accepted. You can now submit your profile for admin review.");
    } catch (acceptError) {
      setError(acceptError instanceof Error ? acceptError.message : "Could not accept terms");
    } finally {
      setReviewSubmitting(false);
    }
  };

  const handleSubmitReview = async () => {
    setReviewSubmitting(true);
    setMessage("");
    setError("");
    try {
      const response = await apiFetch("/logistics-partner/profile/submit-review", { method: "POST" });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Could not submit profile for review");
      }
      const nextProfile = await response.json();
      setProfile(normalizeProfile(nextProfile));
      setMessage("Profile submitted for admin approval.");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Could not submit review");
    } finally {
      setReviewSubmitting(false);
    }
  };

  const handleAreaField = (field: keyof ReturnType<typeof emptyArea>, value: string | boolean) => {
    setAreaForm((current) => ({
      ...current,
      [field]: field === "country_code" && typeof value === "string" ? value.toUpperCase() : value,
    }));
  };

  const handlePricingProfileField = (field: keyof ReturnType<typeof emptyPricingProfile>, value: string | boolean) => {
    setPricingProfileForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleCategoryRuleField = (field: keyof ReturnType<typeof emptyCategoryRule>, value: string | boolean) => {
    setCategoryRuleForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleVehicleRuleField = (field: keyof ReturnType<typeof emptyVehicleRule>, value: string | boolean) => {
    setVehicleRuleForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleEditArea = (area: ServiceArea) => {
    setEditingAreaId(area.id);
    setAreaForm({
      country_name: area.country_name,
      country_code: area.country_code,
      city_name: area.city_name || "",
      origin_city: area.origin_city || "",
      zone_label: area.zone_label || "",
      charge_amount: String(area.charge_amount),
      minimum_charge: area.minimum_charge != null ? String(area.minimum_charge) : "",
      per_kg_rate: area.per_kg_rate != null ? String(area.per_kg_rate) : "",
      per_km_rate: area.per_km_rate != null ? String(area.per_km_rate) : "",
      fuel_multiplier: area.fuel_multiplier != null ? String(area.fuel_multiplier) : "",
      pickup_charge: area.pickup_charge != null ? String(area.pickup_charge) : "",
      dropoff_charge: area.dropoff_charge != null ? String(area.dropoff_charge) : "",
      currency: area.currency,
      latitude: area.latitude != null ? String(area.latitude) : "",
      longitude: area.longitude != null ? String(area.longitude) : "",
      delivery_days_min: area.delivery_days_min != null ? String(area.delivery_days_min) : "",
      delivery_days_max: area.delivery_days_max != null ? String(area.delivery_days_max) : "",
      is_active: area.is_active,
    });
    setTab("coverage");
  };

  const resetAreaForm = () => {
    setEditingAreaId(null);
    setAreaForm(emptyArea());
  };

  const resetPricingProfileForm = () => {
    setEditingPricingProfileId(null);
    setPricingProfileForm(emptyPricingProfile());
  };

  const resetCategoryRuleForm = () => {
    setEditingCategoryRuleId(null);
    setCategoryRuleForm(emptyCategoryRule());
  };

  const resetVehicleRuleForm = () => {
    setEditingVehicleRuleId(null);
    setVehicleRuleForm(emptyVehicleRule());
  };

  const handleSaveArea = async () => {
    setSavingArea(true);
    setMessage("");
    setError("");
    try {
      const url = editingAreaId ? `/logistics-partner/service-areas/${editingAreaId}` : "/logistics-partner/service-areas";
      const response = await apiFetch(url, {
        method: editingAreaId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...areaForm,
          origin_city: areaForm.origin_city || null,
          charge_amount: Number(areaForm.charge_amount || 0),
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
        }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Could not save service area");
      }
      await loadData();
      resetAreaForm();
      setMessage("City, country, and charge row saved. It will affect orders only after admin approval.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Could not save service area");
    } finally {
      setSavingArea(false);
    }
  };

  const handleDeleteArea = async (areaId: number) => {
    setMessage("");
    setError("");
    try {
      const response = await apiFetch(`/logistics-partner/service-areas/${areaId}`, { method: "DELETE" });
      if (!response.ok) {
        throw new Error("Could not delete service area");
      }
      await loadData();
      if (editingAreaId === areaId) resetAreaForm();
      setMessage("Service area removed.");
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Could not delete service area");
    }
  };

  const handleEditPricingProfile = (pricingProfile: PricingProfile) => {
    setEditingPricingProfileId(pricingProfile.id);
    setPricingProfileForm({
      service_area_id: pricingProfile.service_area_id != null ? String(pricingProfile.service_area_id) : "",
      profile_name: pricingProfile.profile_name || "",
      base_in_city_fee: pricingProfile.base_in_city_fee != null ? String(pricingProfile.base_in_city_fee) : "",
      base_inter_city_fee: pricingProfile.base_inter_city_fee != null ? String(pricingProfile.base_inter_city_fee) : "",
      per_km_rate: pricingProfile.per_km_rate != null ? String(pricingProfile.per_km_rate) : "",
      per_kg_rate: pricingProfile.per_kg_rate != null ? String(pricingProfile.per_kg_rate) : "",
      minimum_charge: pricingProfile.minimum_charge != null ? String(pricingProfile.minimum_charge) : "",
      fuel_multiplier: pricingProfile.fuel_multiplier != null ? String(pricingProfile.fuel_multiplier) : "",
      bulk_discount_threshold_kg: pricingProfile.bulk_discount_threshold_kg != null ? String(pricingProfile.bulk_discount_threshold_kg) : "",
      bulk_discount_percent: pricingProfile.bulk_discount_percent != null ? String(pricingProfile.bulk_discount_percent) : "",
      currency: pricingProfile.currency,
      is_active: pricingProfile.is_active,
    });
  };

  const handleSavePricingProfile = async () => {
    setSavingPricingProfile(true);
    setMessage("");
    setError("");
    try {
      const url = editingPricingProfileId ? `/logistics-partner/pricing-profiles/${editingPricingProfileId}` : "/logistics-partner/pricing-profiles";
      const response = await apiFetch(url, {
        method: editingPricingProfileId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          service_area_id: pricingProfileForm.service_area_id ? Number(pricingProfileForm.service_area_id) : null,
          profile_name: pricingProfileForm.profile_name || null,
          base_in_city_fee: pricingProfileForm.base_in_city_fee ? Number(pricingProfileForm.base_in_city_fee) : null,
          base_inter_city_fee: pricingProfileForm.base_inter_city_fee ? Number(pricingProfileForm.base_inter_city_fee) : null,
          per_km_rate: pricingProfileForm.per_km_rate ? Number(pricingProfileForm.per_km_rate) : null,
          per_kg_rate: pricingProfileForm.per_kg_rate ? Number(pricingProfileForm.per_kg_rate) : null,
          minimum_charge: pricingProfileForm.minimum_charge ? Number(pricingProfileForm.minimum_charge) : null,
          fuel_multiplier: pricingProfileForm.fuel_multiplier ? Number(pricingProfileForm.fuel_multiplier) : null,
          bulk_discount_threshold_kg: pricingProfileForm.bulk_discount_threshold_kg ? Number(pricingProfileForm.bulk_discount_threshold_kg) : null,
          bulk_discount_percent: pricingProfileForm.bulk_discount_percent ? Number(pricingProfileForm.bulk_discount_percent) : null,
          currency: pricingProfileForm.currency,
          is_active: pricingProfileForm.is_active,
        }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Could not save pricing profile");
      }
      await loadData();
      resetPricingProfileForm();
      setMessage("Pricing profile saved. It affects quotes only after admin approval.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Could not save pricing profile");
    } finally {
      setSavingPricingProfile(false);
    }
  };

  const handleEditCategoryRule = (rule: CategoryPricingRule) => {
    const handlingAmount = Math.max(Number(rule.flat_fee_override ?? 0), Number(rule.special_handling_fee ?? 0));
    setEditingCategoryRuleId(rule.id);
    setCategoryRuleForm({
      service_area_id: rule.service_area_id != null ? String(rule.service_area_id) : "",
      category_name: rule.category_name,
      flat_fee_override: "",
      special_handling_fee: handlingAmount > 0 ? String(handlingAmount) : "",
      currency: rule.currency,
      is_active: rule.is_active,
    });
  };

  const handleSaveCategoryRule = async () => {
    setSavingCategoryRule(true);
    setMessage("");
    setError("");
    try {
      const url = editingCategoryRuleId ? `/logistics-partner/category-rules/${editingCategoryRuleId}` : "/logistics-partner/category-rules";
      const response = await apiFetch(url, {
        method: editingCategoryRuleId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          service_area_id: categoryRuleForm.service_area_id ? Number(categoryRuleForm.service_area_id) : null,
          category_name: categoryRuleForm.category_name || null,
          flat_fee_override: null,
          special_handling_fee: categoryRuleForm.special_handling_fee ? Number(categoryRuleForm.special_handling_fee) : null,
          currency: categoryRuleForm.currency,
          is_active: categoryRuleForm.is_active,
        }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Could not save handling rule");
      }
      await loadData();
      resetCategoryRuleForm();
      setMessage("Handling rule saved. It affects quotes only after admin approval.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Could not save handling rule");
    } finally {
      setSavingCategoryRule(false);
    }
  };

  const handleDeleteCategoryRule = async (ruleId: number) => {
    setMessage("");
    setError("");
    try {
      const response = await apiFetch(`/logistics-partner/category-rules/${ruleId}`, { method: "DELETE" });
      if (!response.ok) {
        throw new Error("Could not delete handling rule");
      }
      await loadData();
      if (editingCategoryRuleId === ruleId) resetCategoryRuleForm();
      setMessage("Handling rule removed.");
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Could not delete handling rule");
    }
  };

  const handleEditVehicleRule = (rule: VehicleRule) => {
    setEditingVehicleRuleId(rule.id);
    setVehicleRuleForm({
      service_area_id: rule.service_area_id != null ? String(rule.service_area_id) : "",
      route_scope: rule.route_scope,
      vehicle_type: rule.vehicle_type,
      max_weight_kg: rule.max_weight_kg != null ? String(rule.max_weight_kg) : "",
      max_volume_cm3: rule.max_volume_cm3 != null ? String(rule.max_volume_cm3) : "",
      cost_multiplier: String(rule.cost_multiplier),
      priority_rank: String(rule.priority_rank),
      is_active: rule.is_active,
    });
  };

  const handleSaveVehicleRule = async () => {
    setSavingVehicleRule(true);
    setMessage("");
    setError("");
    try {
      const url = editingVehicleRuleId ? `/logistics-partner/vehicle-rules/${editingVehicleRuleId}` : "/logistics-partner/vehicle-rules";
      const response = await apiFetch(url, {
        method: editingVehicleRuleId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          service_area_id: vehicleRuleForm.service_area_id ? Number(vehicleRuleForm.service_area_id) : null,
          route_scope: vehicleRuleForm.route_scope,
          vehicle_type: vehicleRuleForm.vehicle_type || null,
          max_weight_kg: vehicleRuleForm.max_weight_kg ? Number(vehicleRuleForm.max_weight_kg) : null,
          max_volume_cm3: vehicleRuleForm.max_volume_cm3 ? Number(vehicleRuleForm.max_volume_cm3) : null,
          cost_multiplier: vehicleRuleForm.cost_multiplier ? Number(vehicleRuleForm.cost_multiplier) : null,
          priority_rank: vehicleRuleForm.priority_rank ? Number(vehicleRuleForm.priority_rank) : null,
          is_active: vehicleRuleForm.is_active,
        }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || "Could not save load-fit rule");
      }
      await loadData();
      resetVehicleRuleForm();
      setMessage("Load-fit rule saved. It affects route-based compatibility only after admin approval.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Could not save load-fit rule");
    } finally {
      setSavingVehicleRule(false);
    }
  };

  const handleDeleteVehicleRule = async (ruleId: number) => {
    setMessage("");
    setError("");
    try {
      const response = await apiFetch(`/logistics-partner/vehicle-rules/${ruleId}`, { method: "DELETE" });
      if (!response.ok) {
        throw new Error("Could not delete load-fit rule");
      }
      await loadData();
      if (editingVehicleRuleId === ruleId) resetVehicleRuleForm();
      setMessage("Load-fit rule removed.");
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Could not delete load-fit rule");
    }
  };

  const handleDeletePricingProfile = async (profileId: number) => {
    setMessage("");
    setError("");
    try {
      const response = await apiFetch(`/logistics-partner/pricing-profiles/${profileId}`, { method: "DELETE" });
      if (!response.ok) {
        throw new Error("Could not delete pricing profile");
      }
      await loadData();
      if (editingPricingProfileId === profileId) resetPricingProfileForm();
      setMessage("Pricing profile removed.");
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Could not delete pricing profile");
    }
  };

  const handleLpDocUpload = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedLpDocFile) return;
    setLpDocUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", selectedLpDocFile);
      formData.append("document_type", lpDocForm.document_type);
      formData.append("document_name", lpDocForm.document_name || selectedLpDocFile.name);
      if (lpDocForm.expires_at) formData.append("expires_at", lpDocForm.expires_at);
      const res = await apiFetch("/logistics-partner/me/docs/upload", { method: "POST", body: formData });
      if (!res.ok) {
        const payload = await res.json().catch(() => ({}));
        throw new Error(payload.detail || "Upload failed");
      }
      setLpDocForm({ document_type: "trade_license", document_name: "", expires_at: "" });
      setSelectedLpDocFile(null);
      await fetchLpDocuments();
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Could not upload document");
    } finally {
      setLpDocUploading(false);
    }
  };

  const handleLpDocDelete = async (docId: number) => {
    setLpDocDeleteId(docId);
    try {
      const res = await apiFetch(`/logistics-partner/me/docs/${docId}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Could not delete document");
      setLpDocs((prev) => prev.filter((d) => d.id !== docId));
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Could not delete document");
    } finally {
      setLpDocDeleteId(null);
    }
  };

  const handleSaveBankAccount = async () => {
    setMessage("");
    setError("");
    setLpBankSaving(true);
    try {
      const res = await apiFetch("/logistics-partner/me/bank-account", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(lpBankForm),
      });
      const data = await res.json();
      if (res.ok) {
        setLpBankAccount((prev) => ({ ...prev, ...lpBankForm, id: data.id, verification_status: data.verification_status }));
        setMessage("Bank account saved. Pending admin verification.");
      } else {
        setError(data.detail || "Failed to save bank account.");
      }
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setLpBankSaving(false);
    }
  };

  const changeLpPassword = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage("");
    setError("");
    if (newPw !== confirmPw) {
      setError("New passwords do not match.");
      return;
    }
    setPwSaving(true);
    try {
      const res = await apiFetch("/auth/change-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_password: currentPw, new_password: newPw }),
      });
      if (res.ok) {
        setCurrentPw(""); setNewPw(""); setConfirmPw("");
        setMessage("Password changed successfully.");
      } else {
        const payload = await res.json().catch(() => ({}));
        setError(payload.detail || "Could not change password.");
      }
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setPwSaving(false);
    }
  };

  if (loading) {
    return (
      <LogisticsPartnerLayout title="Profile">
        <PanelLoadingState count={4} blockClassName="h-20 animate-pulse rounded-2xl border border-border bg-surface-2" />
      </LogisticsPartnerLayout>
    );
  }

  return (
    <LogisticsPartnerLayout title="Profile">
      <PanelContent width="full" className="space-y-3">
        <PanelHero
          eyebrow="Logistics Partner Workspace"
          title="One-page partner operations"
          description="Profile, delivery settings, and compliance tasks stay in one compact workspace so the live queue and approval state remain easy to read."
          icon={<Truck className="h-5 w-5" />}
          className="rounded-xl p-4"
          actions={(
            <button
              onClick={loadData}
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-surface px-3 py-1.5 text-xs font-semibold text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
            >
              <RefreshCw className="h-3.5 w-3.5" /> Refresh
            </button>
          )}
        />

        <section className="theme-card rounded-xl border p-3">
          <div className="grid gap-2 md:grid-cols-4">
            {[
              { label: "Portal status", value: titleCase(profile.status), chip: STATUS_CHIP[profile.status] ?? "theme-chip-muted", icon: Truck },
              { label: "Profile approval", value: titleCase(profile.verification_status), chip: STATUS_CHIP[profile.verification_status] ?? "theme-chip-muted", icon: BadgeCheck },
              { label: "Approved rates", value: String(approvedAreas), chip: "theme-chip-success", icon: PackageCheck },
              { label: "Pending rates", value: String(pendingAreas), chip: "theme-chip-warning", icon: Clock3 },
            ].map((card) => (
              <div key={card.label} className="rounded-xl border border-border bg-surface-2 p-3">
                <div className="flex items-center justify-between gap-3">
                  <span className={`rounded-xl px-2 py-1 text-[10px] font-bold ${card.chip}`}>{card.label}</span>
                  <card.icon className="h-4 w-4 text-primary" />
                </div>
                <p className="mt-1.5 text-base font-bold capitalize text-text">{card.value}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="theme-card rounded-xl border p-3">
          <div className="grid grid-cols-2 gap-2 lg:grid-cols-4">
            {TABS.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => { setTab(item.key); setMessage(""); setError(""); }}
                  className={`flex min-h-12 items-center justify-center gap-2 rounded-xl px-3 py-1.5 text-center text-[11px] font-semibold transition-colors ${tab === item.key ? "theme-btn-primary" : "theme-btn-secondary border text-text-muted"}`}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="leading-tight">{item.label}</span>
                </button>
              );
            })}
          </div>
        </section>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(0,1.6fr)_minmax(280px,0.8fr)]">
        <div className="lg:col-span-2">
          {error && (
            <div className="mb-3 flex items-center gap-2 rounded-xl border border-danger/20 bg-danger/10 p-3 text-sm text-danger">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}
          {message && <div className="mb-3 rounded-xl border border-success/20 bg-success/10 p-3 text-sm text-success">{message}</div>}

          <div className="space-y-3">
            {tab === "overview" && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                <div className="grid gap-3 lg:grid-cols-[1.15fr,0.85fr]">
                  <div className="rounded-2xl border border-border bg-surface p-4">
                    <h2 className="text-base font-bold text-text">Approval Readiness</h2>
                    <div className="mt-3 space-y-2.5 text-xs text-text-muted">
                      <p>Public visibility and customer search only use partners with an approved profile and an active portal status.</p>
                      <p>Customer cart and checkout only use approved service-area rows. Rejected or pending charges stay out of pricing.</p>
                      <p>Prepared shipments only flash on the pickup board for partners whose approved service areas match the order destination city or country.</p>
                    </div>
                    <div className="mt-4 grid gap-3 md:grid-cols-2">
                      <div className="rounded-xl border border-border bg-surface-2 p-3">
                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Primary coverage</p>
                        <p className="mt-2 text-xs font-semibold text-text">{[profile.city, profile.region, profile.country].filter(Boolean).join(", ") || "Set city and country"}</p>
                      </div>
                      <div className="rounded-xl border border-border bg-surface-2 p-3">
                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Admin note</p>
                        <p className="mt-2 text-xs text-text">{profile.verification_note || "No admin note yet."}</p>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border bg-surface p-4">
                    <h2 className="text-base font-bold text-text">Public Card Preview</h2>
                    <div className="mt-4 rounded-xl border border-border bg-gradient-to-br from-surface-2 to-primary/5 p-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate text-base font-bold text-text">{profile.name || "Logistics partner name"}</p>
                          <p className="text-xs text-text-muted">{[profile.city, profile.country].filter(Boolean).join(", ") || "City, country"}</p>
                        </div>
                        <span className={`rounded-xl px-2 py-1 text-[10px] font-bold ${STATUS_CHIP[profile.verification_status] ?? "theme-chip-muted"}`}>
                          {titleCase(profile.verification_status)}
                        </span>
                      </div>
                      <p className="mt-3 text-xs text-text-muted">{profile.bio || "Short bio for customer-facing search and profile cards."}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {(profile.service_types || []).length > 0 ? (profile.service_types || []).map((service) => (
                          <span key={service} className="rounded-full border border-border bg-surface px-3 py-1 text-[11px] font-semibold text-text-muted">{titleCase(service)}</span>
                        )) : <span className="text-xs text-text-faint">Add service types to clarify your delivery capability.</span>}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid gap-3 md:grid-cols-3">
                  {PARTNER_PERMISSION_CARDS.map((card) => (
                    <div key={card.title} className="rounded-2xl border border-border bg-surface p-4">
                      <h2 className="text-base font-bold text-text">{card.title}</h2>
                      <p className="mt-2 text-xs text-text-muted">{card.body}</p>
                    </div>
                  ))}
                </div>

                <div className="rounded-2xl border border-border bg-surface p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h2 className="text-base font-bold text-text">Rate Queue Snapshot</h2>
                      <p className="text-xs text-text-muted">A quick view of which charge rows are already live and which are still waiting on admin review.</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button onClick={() => setTab("coverage")} className="rounded-xl border border-border px-3 py-1.5 text-xs font-semibold text-text-muted hover:text-text">
                        Open delivery settings
                      </button>
                      <button onClick={() => setTab("operations")} className="rounded-xl border border-border px-3 py-1.5 text-xs font-semibold text-text-muted hover:text-text">
                        Open operations workspace
                      </button>
                    </div>
                  </div>
                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    {[
                      { label: "Approved", value: approvedAreas, tone: "theme-chip-success" },
                      { label: "Pending", value: pendingAreas, tone: "theme-chip-warning" },
                      { label: "Rejected", value: rejectedAreas, tone: "theme-chip-danger" },
                    ].map((card) => (
                      <div key={card.label} className="rounded-xl border border-border bg-surface-2 p-3">
                        <span className={`rounded-xl px-2 py-1 text-[10px] font-bold ${card.tone}`}>{card.label}</span>
                        <p className="mt-2 text-xl font-bold text-text">{card.value}</p>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    {[
                      { label: "Pricing profiles live", value: approvedPricingProfiles, tone: "theme-chip-success" },
                      { label: "Handling rules pending", value: pendingCategoryRules, tone: "theme-chip-warning" },
                      { label: "Load-fit rules live", value: approvedVehicleRules, tone: "theme-chip-success" },
                    ].map((card) => (
                      <div key={card.label} className="rounded-xl border border-border bg-surface-2 p-3">
                        <span className={`rounded-xl px-2 py-1 text-[10px] font-bold ${card.tone}`}>{card.label}</span>
                        <p className="mt-2 text-xl font-bold text-text">{card.value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {tab === "profile" && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="rounded-2xl border border-border bg-surface p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-base font-bold text-text">Business and Location Profile</h2>
                    <p className="text-xs text-text-muted">Use the same structure customers and admins need: partner identity, contact info, service capability, and a clear base location.</p>
                  </div>
                  <button
                    onClick={handleSaveProfile}
                    disabled={savingProfile}
                    className="inline-flex items-center gap-2 rounded-xl theme-btn-primary px-3 py-1.5 text-xs font-semibold disabled:opacity-50"
                  >
                    {savingProfile ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} Save profile
                  </button>
                </div>

                <div className="mt-3 space-y-3">
                  <div>
                    <h3 className="text-xs font-bold text-text">Partner Identity</h3>
                    <div className="mt-2 grid gap-3 md:grid-cols-2">
                      {[
                        { label: "Company name", field: "name" as const, Icon: Building2 },
                        { label: "Contact name", field: "contact_name" as const, Icon: User },
                        { label: "Contact email", field: "contact_email" as const, Icon: Globe },
                        { label: "Contact phone", field: "contact_phone" as const, Icon: Phone },
                        { label: "Website", field: "website" as const, Icon: Link2 },
                        { label: "Business type", field: "business_type" as const, Icon: Building2 },
                      ].map(({ label, field, Icon }) => (
                        <div key={String(field)}>
                          <label className="mb-1 block text-xs font-semibold text-text-muted">{label}</label>
                          <div className="relative">
                            <Icon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                            <input
                              value={profile[field] == null ? "" : String(profile[field])}
                              onChange={(event) => setProfileField(field, event.target.value)}
                              className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs"
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-xs font-bold text-text">Base Location and Routing</h3>
                    <div className="mt-2 grid gap-3 md:grid-cols-2">
                      {[
                        ["Country", "country"],
                        ["Region / State", "region"],
                        ["City", "city"],
                        ["Postal code", "postal_code"],
                        ["Tax ID", "tax_id"],
                        ["Latitude", "latitude"],
                        ["Longitude", "longitude"],
                        ["Logo URL", "logo_url"],
                        ["Banner URL", "banner_url"],
                      ].map(([label, field]) => (
                        <div key={String(field)}>
                          <label className="mb-1 block text-xs font-semibold text-text-muted">{label}</label>
                          <input
                            value={profile[field as keyof PartnerProfile] == null ? "" : String(profile[field as keyof PartnerProfile])}
                            onChange={(event) => setProfileField(field as keyof PartnerProfile, event.target.value)}
                            className="theme-input w-full rounded-xl border px-3 py-2 text-xs"
                          />
                        </div>
                      ))}
                      <div className="md:col-span-2">
                        <label className="mb-1 block text-xs font-semibold text-text-muted">Address</label>
                        <textarea value={profile.address || ""} onChange={(event) => setProfileField("address", event.target.value)} rows={3} className="theme-input w-full resize-none rounded-xl border px-3 py-2 text-xs" />
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-xs font-bold text-text">Public Content and Delivery Capability</h3>
                    <div className="mt-2 grid gap-4">
                      <div>
                        <label className="mb-1 block text-xs font-semibold text-text-muted">Short bio</label>
                        <textarea value={profile.bio || ""} onChange={(event) => setProfileField("bio", event.target.value)} rows={3} className="theme-input w-full resize-none rounded-xl border px-3 py-2 text-xs" />
                      </div>
                      <div>
                        <label className="mb-1 block text-xs font-semibold text-text-muted">About us</label>
                        <textarea value={profile.about_us || ""} onChange={(event) => setProfileField("about_us", event.target.value)} rows={4} className="theme-input w-full resize-none rounded-xl border px-3 py-2 text-xs" />
                      </div>

                      <div>
                        <p className="mb-2 text-xs font-semibold text-text-muted">Service types</p>
                        <div className="flex flex-wrap gap-2">
                          {SERVICE_TYPES.map((serviceType) => {
                            const active = profile.service_types?.includes(serviceType.value);
                            return (
                              <button
                                key={serviceType.value}
                                type="button"
                                onClick={() => toggleServiceType(serviceType.value)}
                                className={`rounded-full border px-2.5 py-1 text-xs font-semibold transition-colors ${active ? "border-primary bg-primary text-on-brand" : "border-border bg-surface-2 text-text-muted hover:text-text"}`}
                              >
                                {serviceType.label}
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      <div>
                        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                          <p className="text-xs font-semibold text-text-muted">Coverage regions</p>
                          <div className="relative w-full sm:w-60">
                            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                            <input
                              value={countrySearch}
                              onChange={(event) => setCountrySearch(event.target.value)}
                              placeholder="Find countries"
                              className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs"
                            />
                          </div>
                        </div>
                        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                          {filteredCountries.map((country) => {
                            const active = profile.coverage_regions?.includes(country);
                            return (
                              <button
                                key={country}
                                type="button"
                                onClick={() => toggleCoverageRegion(country)}
                                className={`rounded-xl border px-3 py-2 text-left text-xs transition-colors ${active ? "border-primary bg-primary/10 text-text" : "border-border bg-surface-2 text-text-muted hover:text-text"}`}
                              >
                                <div className="flex items-center justify-between gap-3">
                                  <span>{country}</span>
                                  {active ? <CheckCircle className="h-4 w-4 text-primary" /> : null}
                                </div>
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      <div>
                        <p className="mb-2 text-xs font-semibold text-text-muted">Social links</p>
                        <div className="grid gap-3 md:grid-cols-2">
                          {[
                            ["website", "Operations website"],
                            ["linkedin", "LinkedIn"],
                            ["instagram", "Instagram"],
                            ["facebook", "Facebook"],
                          ].map(([field, label]) => (
                            <div key={field}>
                              <label className="mb-1 block text-xs font-semibold text-text-muted">{label}</label>
                              <input
                                value={String(profile.social_links?.[field as keyof SocialLinks] || "")}
                                onChange={(event) => setSocialLink(field as keyof SocialLinks, event.target.value)}
                                className="theme-input w-full rounded-xl border px-3 py-2 text-xs"
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {tab === "coverage" && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                {/* -- Pricing Formula Explainer ---------------------------- */}
                <div className="rounded-xl border border-primary/20 bg-primary/5 p-4">
                  <div className="flex items-center gap-2">
                    <Info className="h-4 w-4 text-primary shrink-0" />
                    <h3 className="text-xs font-bold text-text">How Your Delivery Earnings Are Calculated</h3>
                  </div>
                  <div className="mt-3 space-y-2">
                    <div className="flex flex-wrap items-center gap-1 text-[11px] text-text-muted">
                      <span className="rounded-md border border-border bg-surface-2 px-2 py-1 font-semibold text-text">Base charge</span>
                      <span className="font-bold text-text-faint">+</span>
                      <span className="rounded-md border border-border bg-surface-2 px-2 py-1 font-semibold text-text">Pickup charge</span>
                      <span className="font-bold text-text-faint">+</span>
                      <span className="rounded-md border border-border bg-surface-2 px-2 py-1 font-semibold text-text">Dropoff charge</span>
                      <span className="font-bold text-text-faint">+</span>
                      <span className="rounded-md border border-border bg-surface-2 px-2 py-1 font-semibold text-text">Weight x per-kg rate</span>
                      <span className="font-bold text-text-faint">+</span>
                      <span className="rounded-md border border-border bg-surface-2 px-2 py-1 font-semibold text-text">Distance x per-km rate</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-1 text-[11px] text-text-muted">
                      <span className="font-bold text-text-faint">then add</span>
                      <span className="rounded-md border border-primary/30 bg-primary/10 px-2 py-1 font-semibold text-primary">Highest handling amount</span>
                      <span className="font-bold text-text-faint">then apply</span>
                      <span className="rounded-md border border-primary/30 bg-primary/10 px-2 py-1 font-semibold text-primary">Load-fit adjustment</span>
                      <span className="font-bold text-text-faint">and</span>
                      <span className="rounded-md border border-primary/30 bg-primary/10 px-2 py-1 font-semibold text-primary">Runtime surcharge</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-1 text-[11px] text-text-muted">
                      <span className="font-bold text-text-faint">then apply</span>
                      <span className="rounded-md border border-border bg-surface-2 px-2 py-1 font-semibold text-text">minimum charge floor</span>
                      <span className="font-bold text-text-faint">-</span>
                      <span className="rounded-md border border-success/30 bg-success/10 px-2 py-1 font-semibold text-success">weight discount on weight fee</span>
                      <span className="font-bold text-text-faint">= </span>
                      <span className="rounded-md border border-success/40 bg-success/10 px-2 py-1 font-bold text-success text-xs">Your earnings</span>
                    </div>
                    <p className="mt-1 text-[10px] text-text-faint">
                      Service area values are the defaults. Approved pricing profiles override specific fields, and only the highest applicable approved handling rule is used per grouped shipment.
                      Only rows with <span className="font-semibold text-success">approved</span> status are used in checkout and shipment allocation.
                    </p>
                  </div>
                </div>

                <div className="grid gap-3 xl:grid-cols-[1fr,1fr]">
                  <div className="rounded-2xl border border-border bg-surface p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h2 className="text-base font-bold text-text">Service Area Submission</h2>
                        <p className="text-xs text-text-muted">Add the destination country, city, and delivery charge that should be reviewed by admin.</p>
                      </div>
                      <button onClick={resetAreaForm} className="rounded-xl border border-border px-3 py-1.5 text-xs font-semibold text-text-muted hover:text-text">New row</button>
                    </div>

                    <div className="mt-3 space-y-3">
                      <div>
                        <h3 className="text-xs font-bold text-text">Destination lane</h3>
                        <div className="mt-2 grid gap-3 md:grid-cols-2">
                          {[
                            ["Country name", "country_name"],
                            ["Country code", "country_code"],
                            ["Delivery City", "city_name"],
                            ["Pickup City (origin)", "origin_city"],
                            ["Zone label", "zone_label"],
                          ].map(([label, field]) => (
                            <div key={String(field)}>
                              <label className="mb-1 block text-xs font-semibold text-text-muted">{label}</label>
                              <input
                                value={String(areaForm[field as keyof typeof areaForm])}
                                onChange={(event) => handleAreaField(field as keyof typeof areaForm, event.target.value)}
                                className="theme-input w-full rounded-xl border px-3 py-2 text-xs"
                              />
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h3 className="text-xs font-bold text-text">Pricing and promise</h3>
                        <div className="mt-2 grid gap-3 md:grid-cols-3">
                          {[
                            ["Base charge", "charge_amount"],
                            ["Min charge (floor)", "minimum_charge"],
                            ["Per kg rate", "per_kg_rate"],
                            ["Per km rate", "per_km_rate"],
                            ["Runtime surcharge factor", "fuel_multiplier"],
                            ["Pickup fee per stop", "pickup_charge"],
                            ["Dropoff fee per stop", "dropoff_charge"],
                            ["Currency", "currency"],
                            ["Delivery days min", "delivery_days_min"],
                            ["Delivery days max", "delivery_days_max"],
                          ].map(([label, field]) => (
                            <div key={String(field)}>
                              <label className="mb-1 block text-xs font-semibold text-text-muted">{label}</label>
                              <input
                                value={String(areaForm[field as keyof typeof areaForm])}
                                onChange={(event) => handleAreaField(field as keyof typeof areaForm, event.target.value)}
                                className="theme-input w-full rounded-xl border px-3 py-2 text-xs"
                              />
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h3 className="text-xs font-bold text-text">Routing coordinates</h3>
                        <div className="mt-2 grid gap-3 md:grid-cols-2">
                          {[
                            ["Latitude", "latitude"],
                            ["Longitude", "longitude"],
                          ].map(([label, field]) => (
                            <div key={String(field)}>
                              <label className="mb-1 block text-xs font-semibold text-text-muted">{label}</label>
                              <input
                                value={String(areaForm[field as keyof typeof areaForm])}
                                onChange={(event) => handleAreaField(field as keyof typeof areaForm, event.target.value)}
                                className="theme-input w-full rounded-xl border px-3 py-2 text-xs"
                              />
                            </div>
                          ))}
                        </div>
                      </div>

                      <label className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs font-medium text-text">
                        <input type="checkbox" checked={areaForm.is_active} onChange={(event) => handleAreaField("is_active", event.target.checked)} />
                        Keep this service area active once approved
                      </label>
                    </div>

                    <button
                      onClick={handleSaveArea}
                      disabled={savingArea}
                      className="mt-4 inline-flex items-center gap-2 rounded-xl theme-btn-primary px-3 py-1.5 text-xs font-semibold disabled:opacity-50"
                    >
                      {savingArea ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                      {editingAreaId ? "Update charge row" : "Add charge row"}
                    </button>
                  </div>

                  <div className="rounded-2xl border border-border bg-surface p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <h2 className="text-base font-bold text-text">Submitted Service Areas</h2>
                        <p className="text-xs text-text-muted">Review rows by country, city, or approval status before editing them.</p>
                      </div>
                      <div className="flex w-full flex-wrap gap-2 sm:w-auto">
                        <div className="relative min-w-45 flex-1 sm:flex-none">
                          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                          <input
                            value={coverageSearch}
                            onChange={(event) => setCoverageSearch(event.target.value)}
                            placeholder="Search lanes"
                            className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs"
                          />
                        </div>
                        <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)} className="theme-input rounded-xl border px-3 py-2 text-xs">
                          <option value="all">All statuses</option>
                          <option value="approved">Approved</option>
                          <option value="pending">Pending</option>
                          <option value="rejected">Rejected</option>
                        </select>
                      </div>
                    </div>

                    <div className="mt-4 space-y-3">
                      {filteredAreas.length === 0 ? (
                        <div className="rounded-xl border border-dashed border-border px-3 py-4 text-xs text-text-muted">No service areas match the current filters.</div>
                      ) : filteredAreas.map((area) => (
                        <div key={area.id} className="rounded-xl border border-border bg-surface-2 p-3">
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className={`rounded-xl px-2 py-1 text-[10px] font-bold ${STATUS_CHIP[area.approval_status] ?? "theme-chip-muted"}`}>{titleCase(area.approval_status)}</span>
                                <span className="text-xs font-semibold text-text">{area.zone_label || area.city_name || area.country_name}</span>
                              </div>
                              <p className="mt-1 text-xs text-text-muted">{describeAreaLocation(area)}</p>
                              <p className="mt-0.5 text-xs text-text">{describeServiceArea(area)}</p>
                              <p className="mt-2 text-xs text-text-faint">{area.review_note || "Awaiting admin review."}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <button onClick={() => handleEditArea(area)} className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-text-muted hover:text-text">Edit</button>
                              <button onClick={() => handleDeleteArea(area.id)} className="rounded-xl border border-danger/30 px-3 py-2 text-xs font-semibold text-danger">
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="grid gap-3 xl:grid-cols-[1fr,1fr]">
                  <div className="rounded-2xl border border-border bg-surface p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h2 className="text-base font-bold text-text">Pricing Profile Submission</h2>
                        <p className="text-xs text-text-muted">Create partner-wide defaults or target one service area with a reviewed pricing override.</p>
                      </div>
                      <button onClick={resetPricingProfileForm} className="rounded-xl border border-border px-3 py-1.5 text-xs font-semibold text-text-muted hover:text-text">New profile</button>
                    </div>

                    <div className="mt-3 space-y-3">
                      <div className="grid gap-3 md:grid-cols-2">
                        <div>
                          <label className="mb-1 block text-xs font-semibold text-text-muted">Profile name</label>
                          <input value={pricingProfileForm.profile_name} onChange={(event) => handlePricingProfileField("profile_name", event.target.value)} className="theme-input w-full rounded-xl border px-3 py-2 text-xs" />
                        </div>
                        <div>
                          <label className="mb-1 block text-xs font-semibold text-text-muted">Service area override</label>
                          <select value={pricingProfileForm.service_area_id} onChange={(event) => handlePricingProfileField("service_area_id", event.target.value)} className="theme-input w-full rounded-xl border px-3 py-2 text-xs">
                            <option value="">Partner default</option>
                            {serviceAreas.map((area) => (
                              <option key={area.id} value={String(area.id)}>{area.zone_label || area.city_name || area.country_name}</option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <div className="grid gap-3 md:grid-cols-3">
                        {[
                          ["Base in-city fee", "base_in_city_fee"],
                          ["Base inter-city fee", "base_inter_city_fee"],
                          ["Per km rate", "per_km_rate"],
                          ["Per kg rate", "per_kg_rate"],
                          ["Minimum charge", "minimum_charge"],
                          ["Runtime surcharge factor", "fuel_multiplier"],
                          ["Weight discount threshold (kg)", "bulk_discount_threshold_kg"],
                          ["Weight discount %", "bulk_discount_percent"],
                          ["Currency", "currency"],
                        ].map(([label, field]) => (
                          <div key={field}>
                            <label className="mb-1 block text-xs font-semibold text-text-muted">{label}</label>
                            <input
                              value={String(pricingProfileForm[field as keyof typeof pricingProfileForm])}
                              onChange={(event) => handlePricingProfileField(field as keyof typeof pricingProfileForm, event.target.value)}
                              className="theme-input w-full rounded-xl border px-3 py-2 text-xs"
                            />
                          </div>
                        ))}
                      </div>

                      <label className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs font-medium text-text">
                        <input type="checkbox" checked={pricingProfileForm.is_active} onChange={(event) => handlePricingProfileField("is_active", event.target.checked)} />
                        Keep this pricing profile active once approved
                      </label>
                    </div>

                    <button
                      onClick={handleSavePricingProfile}
                      disabled={savingPricingProfile}
                      className="mt-4 inline-flex items-center gap-2 rounded-xl theme-btn-primary px-3 py-1.5 text-xs font-semibold disabled:opacity-50"
                    >
                      {savingPricingProfile ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                      {editingPricingProfileId ? "Update pricing profile" : "Add pricing profile"}
                    </button>
                  </div>

                  <div className="rounded-2xl border border-border bg-surface p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h2 className="text-base font-bold text-text">Submitted Pricing Profiles</h2>
                        <p className="text-xs text-text-muted">{approvedPricingProfiles} approved · {pendingPricingProfiles} pending. Approved profiles override service-area pricing where values are provided, and weight discounts apply to weight fee only.</p>
                      </div>
                    </div>

                    <div className="mt-4 space-y-3">
                      {pricingProfiles.length === 0 ? (
                        <div className="rounded-xl border border-dashed border-border px-3 py-4 text-xs text-text-muted">No pricing profiles submitted yet.</div>
                      ) : pricingProfiles.map((pricingProfile) => {
                        const linkedArea = serviceAreas.find((area) => area.id === pricingProfile.service_area_id);
                        return (
                          <div key={pricingProfile.id} className="rounded-xl border border-border bg-surface-2 p-3">
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <div className="min-w-0">
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className={`rounded-xl px-2 py-1 text-[10px] font-bold ${STATUS_CHIP[pricingProfile.approval_status] ?? "theme-chip-muted"}`}>{titleCase(pricingProfile.approval_status)}</span>
                                  <span className="text-xs font-semibold text-text">{pricingProfile.profile_name || linkedArea?.zone_label || linkedArea?.city_name || "Partner default profile"}</span>
                                </div>
                                <p className="mt-1 text-xs text-text-muted">{linkedArea ? `Targets ${linkedArea.zone_label || linkedArea.city_name || linkedArea.country_name}` : "Applies to all approved service areas for this partner"}</p>
                                <p className="mt-0.5 text-xs text-text">{describePricingProfile(pricingProfile)}</p>
                                <p className="mt-2 text-xs text-text-faint">{pricingProfile.review_note || "Awaiting admin review."}</p>
                              </div>
                              <div className="flex items-center gap-2">
                                <button onClick={() => handleEditPricingProfile(pricingProfile)} className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-text-muted hover:text-text">Edit</button>
                                <button onClick={() => handleDeletePricingProfile(pricingProfile.id)} className="rounded-xl border border-danger/30 px-3 py-2 text-xs font-semibold text-danger">
                                  <Trash2 className="h-3.5 w-3.5" />
                                </button>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                <div className="grid gap-3 xl:grid-cols-[1fr,1fr]">
                  <div className="rounded-2xl border border-border bg-surface p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h2 className="text-base font-bold text-text">Handling Rule Submission</h2>
                        <p className="text-xs text-text-muted">Add one shipment-level handling amount. Only the highest applicable approved handling rule is used per grouped shipment.</p>
                      </div>
                      <button onClick={resetCategoryRuleForm} className="rounded-xl border border-border px-3 py-1.5 text-xs font-semibold text-text-muted hover:text-text">New rule</button>
                    </div>

                    <div className="mt-3 space-y-3">
                      <div className="grid gap-3 md:grid-cols-2">
                        <div>
                          <label className="mb-1 block text-xs font-semibold text-text-muted">Handling match label</label>
                          <input value={categoryRuleForm.category_name} onChange={(event) => handleCategoryRuleField("category_name", event.target.value)} className="theme-input w-full rounded-xl border px-3 py-2 text-xs" />
                        </div>
                        <div>
                          <label className="mb-1 block text-xs font-semibold text-text-muted">Service area override</label>
                          <select value={categoryRuleForm.service_area_id} onChange={(event) => handleCategoryRuleField("service_area_id", event.target.value)} className="theme-input w-full rounded-xl border px-3 py-2 text-xs">
                            <option value="">Partner default</option>
                            {serviceAreas.map((area) => (
                              <option key={area.id} value={String(area.id)}>{area.zone_label || area.city_name || area.country_name}</option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <div className="grid gap-3 md:grid-cols-3">
                        {[
                          ["Handling amount", "special_handling_fee"],
                          ["Currency", "currency"],
                        ].map(([label, field]) => (
                          <div key={field}>
                            <label className="mb-1 block text-xs font-semibold text-text-muted">{label}</label>
                            <input
                              value={String(categoryRuleForm[field as keyof typeof categoryRuleForm])}
                              onChange={(event) => handleCategoryRuleField(field as keyof typeof categoryRuleForm, event.target.value)}
                              className="theme-input w-full rounded-xl border px-3 py-2 text-xs"
                            />
                          </div>
                        ))}
                      </div>

                      <label className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs font-medium text-text">
                        <input type="checkbox" checked={categoryRuleForm.is_active} onChange={(event) => handleCategoryRuleField("is_active", event.target.checked)} />
                        Keep this handling rule active once approved
                      </label>
                    </div>

                    <button
                      onClick={handleSaveCategoryRule}
                      disabled={savingCategoryRule}
                      className="mt-4 inline-flex items-center gap-2 rounded-xl theme-btn-primary px-3 py-1.5 text-xs font-semibold disabled:opacity-50"
                    >
                      {savingCategoryRule ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                      {editingCategoryRuleId ? "Update handling rule" : "Add handling rule"}
                    </button>
                  </div>

                  <div className="rounded-2xl border border-border bg-surface p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h2 className="text-base font-bold text-text">Submitted Handling Rules</h2>
                        <p className="text-xs text-text-muted">{approvedCategoryRules} approved · {pendingCategoryRules} pending. Approved rules apply one shipment-level handling amount inside quote breakdowns.</p>
                      </div>
                    </div>

                    <div className="mt-4 space-y-3">
                      {categoryRules.length === 0 ? (
                        <div className="rounded-xl border border-dashed border-border px-3 py-4 text-xs text-text-muted">No handling rules submitted yet.</div>
                      ) : categoryRules.map((rule) => {
                        const linkedArea = serviceAreas.find((area) => area.id === rule.service_area_id);
                        return (
                          <div key={rule.id} className="rounded-xl border border-border bg-surface-2 p-3">
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <div className="min-w-0">
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className={`rounded-xl px-2 py-1 text-[10px] font-bold ${STATUS_CHIP[rule.approval_status] ?? "theme-chip-muted"}`}>{titleCase(rule.approval_status)}</span>
                                  <span className="text-xs font-semibold text-text">{rule.category_name}</span>
                                </div>
                                <p className="mt-1 text-xs text-text-muted">{linkedArea ? `Targets ${linkedArea.zone_label || linkedArea.city_name || linkedArea.country_name}` : "Applies to all approved service areas for this partner"}</p>
                                <p className="mt-0.5 text-xs text-text">{describeCategoryRule(rule)}</p>
                                <p className="mt-2 text-xs text-text-faint">{rule.review_note || "Awaiting admin review."}</p>
                              </div>
                              <div className="flex items-center gap-2">
                                <button onClick={() => handleEditCategoryRule(rule)} className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-text-muted hover:text-text">Edit</button>
                                <button onClick={() => handleDeleteCategoryRule(rule.id)} className="rounded-xl border border-danger/30 px-3 py-2 text-xs font-semibold text-danger">
                                  <Trash2 className="h-3.5 w-3.5" />
                                </button>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                <div className="grid gap-3 xl:grid-cols-[1fr,1fr]">
                  <div className="rounded-2xl border border-border bg-surface p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h2 className="text-base font-bold text-text">Load-fit Rule Submission</h2>
                        <p className="text-xs text-text-muted">Define route-aware load-fit selection so heavy or bulky shipments pick the right approved compatibility rule.</p>
                      </div>
                      <button onClick={resetVehicleRuleForm} className="rounded-xl border border-border px-3 py-1.5 text-xs font-semibold text-text-muted hover:text-text">New rule</button>
                    </div>

                    <div className="mt-3 space-y-3">
                      <div className="grid gap-3 md:grid-cols-2">
                        <div>
                          <label className="mb-1 block text-xs font-semibold text-text-muted">Load-fit label</label>
                          <input value={vehicleRuleForm.vehicle_type} onChange={(event) => handleVehicleRuleField("vehicle_type", event.target.value)} className="theme-input w-full rounded-xl border px-3 py-2 text-xs" />
                        </div>
                        <div>
                          <label className="mb-1 block text-xs font-semibold text-text-muted">Service area override</label>
                          <select value={vehicleRuleForm.service_area_id} onChange={(event) => handleVehicleRuleField("service_area_id", event.target.value)} className="theme-input w-full rounded-xl border px-3 py-2 text-xs">
                            <option value="">Partner default</option>
                            {serviceAreas.map((area) => (
                              <option key={area.id} value={String(area.id)}>{area.zone_label || area.city_name || area.country_name}</option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <div className="grid gap-3 md:grid-cols-3">
                        <div>
                          <label className="mb-1 block text-xs font-semibold text-text-muted">Route scope</label>
                          <select value={vehicleRuleForm.route_scope} onChange={(event) => handleVehicleRuleField("route_scope", event.target.value)} className="theme-input w-full rounded-xl border px-3 py-2 text-xs">
                            <option value="any">Any route</option>
                            <option value="in_city">In-city only</option>
                            <option value="inter_city">Inter-city only</option>
                          </select>
                        </div>
                        {[
                          ["Max weight (kg)", "max_weight_kg"],
                          ["Max volume (cm3)", "max_volume_cm3"],
                          ["Compatibility factor", "cost_multiplier"],
                          ["Priority rank", "priority_rank"],
                        ].map(([label, field]) => (
                          <div key={field}>
                            <label className="mb-1 block text-xs font-semibold text-text-muted">{label}</label>
                            <input
                              value={String(vehicleRuleForm[field as keyof typeof vehicleRuleForm])}
                              onChange={(event) => handleVehicleRuleField(field as keyof typeof vehicleRuleForm, event.target.value)}
                              className="theme-input w-full rounded-xl border px-3 py-2 text-xs"
                            />
                          </div>
                        ))}
                      </div>

                      <label className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs font-medium text-text">
                        <input type="checkbox" checked={vehicleRuleForm.is_active} onChange={(event) => handleVehicleRuleField("is_active", event.target.checked)} />
                        Keep this load-fit rule active once approved
                      </label>
                    </div>

                    <button
                      onClick={handleSaveVehicleRule}
                      disabled={savingVehicleRule}
                      className="mt-4 inline-flex items-center gap-2 rounded-xl theme-btn-primary px-3 py-1.5 text-xs font-semibold disabled:opacity-50"
                    >
                      {savingVehicleRule ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                      {editingVehicleRuleId ? "Update load-fit rule" : "Add load-fit rule"}
                    </button>
                  </div>

                  <div className="rounded-2xl border border-border bg-surface p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <h2 className="text-base font-bold text-text">Submitted Load-fit Rules</h2>
                        <p className="text-xs text-text-muted">{approvedVehicleRules} approved · {pendingVehicleRules} pending. Approved rules decide load-fit labels and compatibility factors in route-aware quote breakdowns.</p>
                      </div>
                    </div>

                    <div className="mt-4 space-y-3">
                      {vehicleRules.length === 0 ? (
                        <div className="rounded-xl border border-dashed border-border px-3 py-4 text-xs text-text-muted">No load-fit rules submitted yet.</div>
                      ) : vehicleRules.map((rule) => {
                        const linkedArea = serviceAreas.find((area) => area.id === rule.service_area_id);
                        return (
                          <div key={rule.id} className="rounded-xl border border-border bg-surface-2 p-3">
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <div className="min-w-0">
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className={`rounded-xl px-2 py-1 text-[10px] font-bold ${STATUS_CHIP[rule.approval_status] ?? "theme-chip-muted"}`}>{titleCase(rule.approval_status)}</span>
                                  <span className="text-xs font-semibold text-text">{rule.vehicle_type}</span>
                                </div>
                                <p className="mt-1 text-xs text-text-muted">{linkedArea ? `Targets ${linkedArea.zone_label || linkedArea.city_name || linkedArea.country_name}` : "Applies to all approved service areas for this partner"}</p>
                                <p className="mt-0.5 text-xs text-text">{describeVehicleRule(rule)}</p>
                                <p className="mt-2 text-xs text-text-faint">{rule.review_note || "Awaiting admin review."}</p>
                              </div>
                              <div className="flex items-center gap-2">
                                <button onClick={() => handleEditVehicleRule(rule)} className="rounded-xl border border-border px-3 py-2 text-xs font-semibold text-text-muted hover:text-text">Edit</button>
                                <button onClick={() => handleDeleteVehicleRule(rule.id)} className="rounded-xl border border-danger/30 px-3 py-2 text-xs font-semibold text-danger">
                                  <Trash2 className="h-3.5 w-3.5" />
                                </button>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {tab === "operations" && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="theme-card rounded-2xl border p-5">
                <h2 className="text-base font-bold text-text">Change Password</h2>
                <p className="mt-1 text-xs text-text-muted">Your current password is required to set a new one.</p>
                <form onSubmit={changeLpPassword} className="mt-4 space-y-3 max-w-md">
                  {[
                    { label: "Current Password", value: currentPw, setter: setCurrentPw },
                    { label: "New Password", value: newPw, setter: setNewPw },
                    { label: "Confirm New Password", value: confirmPw, setter: setConfirmPw },
                  ].map((field) => (
                    <div key={field.label}>
                      <label className="mb-1 block text-xs font-semibold text-text-muted">{field.label}</label>
                      <div className="relative">
                        <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                        <input type="password" value={field.value} onChange={(event) => field.setter(event.target.value)} required className="theme-input w-full rounded-xl border py-2 pl-9 pr-3 text-xs" />
                      </div>
                    </div>
                  ))}
                  <button type="submit" disabled={pwSaving} className="inline-flex items-center gap-2 rounded-xl theme-btn-primary px-3 py-1.5 text-xs font-semibold disabled:opacity-50">
                    {pwSaving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Shield className="h-4 w-4" />}
                    {pwSaving ? "Changing..." : "Change password"}
                  </button>
                </form>
              </motion.div>
            )}

            {tab === "operations" && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-3">
                <div className="rounded-2xl border border-border bg-surface p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <h2 className="text-base font-bold text-text">KYC Documents</h2>
                      <p className="mt-1 text-xs text-text-muted">{lpDocs.length} document{lpDocs.length !== 1 ? "s" : ""} on file · {lpDocs.filter((d) => d.status === "approved").length} approved</p>
                    </div>
                    <button type="button" onClick={fetchLpDocuments} className="inline-flex items-center gap-1 rounded-xl border border-border px-3 py-1.5 text-xs font-semibold text-text-muted hover:text-text">
                      <RefreshCw className={`h-3.5 w-3.5 ${lpDocsLoading ? "animate-spin" : ""}`} /> Refresh
                    </button>
                  </div>

                  <form onSubmit={handleLpDocUpload} className="mt-4 grid gap-3 sm:grid-cols-2">
                    <div>
                      <label className="mb-1 block text-xs font-semibold text-text-muted">Document Type</label>
                      <select value={lpDocForm.document_type} onChange={(event) => setLpDocForm((current) => ({ ...current, document_type: event.target.value }))} className="theme-input w-full rounded-xl border px-3 py-2 text-xs">
                        {LP_DOC_TYPES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-xs font-semibold text-text-muted">Document Name</label>
                      <input value={lpDocForm.document_name} onChange={(event) => setLpDocForm((current) => ({ ...current, document_name: event.target.value }))} placeholder="e.g. Trade License 2026" className="theme-input w-full rounded-xl border px-3 py-2 text-xs" />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs font-semibold text-text-muted">Expiry Date</label>
                      <input type="date" value={lpDocForm.expires_at} onChange={(event) => setLpDocForm((current) => ({ ...current, expires_at: event.target.value }))} className="theme-input w-full rounded-xl border px-3 py-2 text-xs" />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs font-semibold text-text-muted">File (PDF, JPG, PNG)</label>
                      <input type="file" accept=".pdf,.jpg,.jpeg,.png,.webp" onChange={(event) => {
                        const file = event.target.files?.[0] ?? null;
                        setSelectedLpDocFile(file);
                        if (file && !lpDocForm.document_name) setLpDocForm((current) => ({ ...current, document_name: file.name.replace(/\.[^.]+$/, "") }));
                      }} className="theme-input w-full rounded-xl border px-3 py-2 text-xs file:mr-3 file:rounded-xl file:border-0 file:bg-surface-3 file:px-3 file:py-1 file:text-xs file:font-semibold file:text-text" />
                    </div>
                    <div className="sm:col-span-2">
                      <button type="submit" disabled={lpDocUploading || !selectedLpDocFile} className="inline-flex items-center gap-2 rounded-xl theme-btn-primary px-3 py-1.5 text-xs font-semibold disabled:opacity-50">
                        {lpDocUploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                        {lpDocUploading ? "Uploading..." : "Upload document"}
                      </button>
                    </div>
                  </form>
                </div>

                <div className="rounded-xl border border-border bg-surface overflow-hidden">
                  <div className="border-b border-border px-3 py-2.5">
                    <p className="text-xs font-bold text-text">Submitted Documents</p>
                  </div>
                  <div className="divide-y divide-border">
                    {lpDocs.length === 0 ? (
                      <p className="px-3 py-5 text-xs text-text-muted">No documents uploaded yet.</p>
                    ) : lpDocs.map((doc) => (
                      <div key={doc.id} className="flex flex-wrap items-center justify-between gap-2 px-3 py-3">
                        <div>
                          <a href={doc.file_url || "#"} target="_blank" rel="noreferrer" className="text-xs font-semibold text-text hover:text-primary">
                            {doc.document_name || `Document #${doc.id}`}
                          </a>
                          <p className="text-xs text-text-muted capitalize">{String(doc.document_type || "other").replace(/_/g, " ")}</p>
                          {doc.expires_at ? <p className="text-[11px] text-text-faint">Expires {new Date(doc.expires_at).toLocaleDateString()}</p> : null}
                          {doc.review_note ? <p className="mt-1 text-[11px] italic text-text-muted">Note: {doc.review_note}</p> : null}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`rounded-xl px-2.5 py-0.5 text-xs font-semibold ${STATUS_CHIP[doc.status] || "theme-chip-muted"}`}>{String(doc.status).replace(/_/g, " ")}</span>
                          {(doc.status === "pending" || doc.status === "rejected") ? (
                            <Button variant="danger" className="rounded-xl p-1.5 text-danger transition-colors disabled:opacity-50" type="button" onClick={() => handleLpDocDelete(doc.id)} disabled={lpDocDeleteId === doc.id}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          ) : null}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}

            {tab === "operations" && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="theme-card rounded-2xl border p-5">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <h2 className="text-base font-bold text-text flex items-center gap-2">
                      <Building2 className="h-4 w-4 text-primary" />
                      Delivery Payout Bank Account
                    </h2>
                    <p className="mt-1 text-xs text-text-muted">Submit the bank account used for delivery-fee payouts and logistics-side finance reconciliation. COD collection review and payout activation both depend on the verified account shown here.</p>
                  </div>
                  {lpBankAccount?.verification_status === "verified" && (
                    <span className="inline-flex items-center gap-1 rounded-xl border border-success/40 bg-success/10 px-2 py-1 text-[10px] font-bold text-success"><CheckCircle className="h-3 w-3" /> verified</span>
                  )}
                  {lpBankAccount?.verification_status === "pending" && (
                    <span className="inline-flex items-center gap-1 rounded-xl border border-warning/40 bg-warning/10 px-2 py-1 text-[10px] font-bold text-warning"><Clock className="h-3 w-3" /> pending review</span>
                  )}
                  {lpBankAccount?.verification_status === "rejected" && (
                    <span className="inline-flex items-center gap-1 rounded-xl border border-danger/40 bg-danger/10 px-2 py-1 text-[10px] font-bold text-danger"><XCircle className="h-3 w-3" /> rejected</span>
                  )}
                  {!lpBankAccount?.id && (
                    <span className="rounded-xl border border-border bg-surface-2 px-2 py-1 text-[10px] font-bold text-text-muted">not configured</span>
                  )}
                </div>

                {lpBankAccount?.verification_status === "rejected" && lpBankAccount.verification_note && (
                  <div className="mt-3 rounded-xl border border-danger/30 bg-danger/5 px-3 py-2 text-xs text-danger">
                    Rejection reason: {lpBankAccount.verification_note}
                  </div>
                )}

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  {(
                    [
                      { key: "beneficiary_name", label: "Beneficiary Name", placeholder: "As shown on bank account" },
                      { key: "bank_name", label: "Bank Name", placeholder: "e.g. First Abu Dhabi Bank" },
                      { key: "branch_name", label: "Branch Name", placeholder: "e.g. Main Branch" },
                      { key: "account_number", label: "Account Number", placeholder: "12-digit account number" },
                      { key: "iban", label: "IBAN", placeholder: "e.g. AE07 0331 2345 6789 0123 456" },
                      { key: "swift_code", label: "SWIFT / BIC", placeholder: "e.g. FABEAEADXXX" },
                      { key: "routing_number", label: "Routing Number", placeholder: "Optional" },
                      { key: "bank_country", label: "Bank Country", placeholder: "e.g. United Arab Emirates" },
                    ] as { key: keyof typeof EMPTY_LP_BANK_FORM; label: string; placeholder: string }[]
                  ).map(({ key, label, placeholder }) => (
                    <div key={key}>
                      <label className="mb-1 block text-xs font-semibold text-text-muted">{label}</label>
                      <input
                        className="theme-input w-full rounded-xl border px-3 py-2 text-xs"
                        value={lpBankForm[key]}
                        placeholder={placeholder}
                        onChange={(event) => setLpBankForm((current) => ({ ...current, [key]: event.target.value }))}
                      />
                    </div>
                  ))}
                  <div>
                    <label className="mb-1 block text-xs font-semibold text-text-muted">Currency</label>
                    <select
                      className="theme-input w-full rounded-xl border px-3 py-2 text-xs"
                      value={lpBankForm.currency}
                      onChange={(event) => setLpBankForm((current) => ({ ...current, currency: event.target.value }))}
                    >
                      {["AED", "OMR", "SAR", "QAR", "KWD", "BHD", "USD", "EUR", "GBP"].map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <button
                  disabled={lpBankSaving}
                  onClick={handleSaveBankAccount}
                  className="mt-4 inline-flex items-center gap-2 rounded-xl theme-btn-primary px-3 py-1.5 text-xs font-semibold disabled:opacity-50"
                >
                  {lpBankSaving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                  {lpBankSaving ? "Saving..." : "Save bank account"}
                </button>
              </motion.div>
            )}

            {tab === "operations" && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="grid gap-3 lg:grid-cols-[1fr,0.9fr]">
                <div className="rounded-2xl border border-border bg-surface p-4">
                  <h2 className="text-base font-bold text-text">Terms and Approval Rules</h2>
                  <div className="mt-3 space-y-2 text-xs text-text-muted">
                    {TERMS.map((line) => (
                      <div key={line} className="flex items-start gap-3 rounded-xl border border-border bg-surface-2 px-3 py-2">
                        <ShieldCheck className="mt-0.5 h-4 w-4 text-primary" />
                        <p>{line}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-2xl border border-border bg-surface p-4">
                  <h2 className="text-base font-bold text-text">Approval Actions</h2>
                  <div className="mt-3 space-y-3">
                    <div className="rounded-xl border border-border bg-surface-2 p-3 text-xs text-text-muted">
                      <p className="font-semibold text-text">Current review state</p>
                      <p className="mt-2 capitalize">{titleCase(profile.verification_status)}</p>
                      <p className="mt-2">{profile.verification_note || "No admin note yet."}</p>
                    </div>
                    <button
                      onClick={handleAcceptTerms}
                      disabled={reviewSubmitting || profile.is_terms_accepted}
                      className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-border px-3 py-2 text-xs font-semibold text-text disabled:opacity-50"
                    >
                      <Globe className="h-4 w-4" />
                      {profile.is_terms_accepted ? "Terms accepted" : "Accept logistics terms"}
                    </button>
                    <button
                      onClick={handleSubmitReview}
                      disabled={reviewSubmitting}
                      className="inline-flex w-full items-center justify-center gap-2 rounded-xl theme-btn-primary px-3 py-2 text-xs font-semibold disabled:opacity-50"
                    >
                      {reviewSubmitting ? <RefreshCw className="h-4 w-4 animate-spin" /> : <AlertCircle className="h-4 w-4" />}
                      Submit profile for approval
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

            {tab === "operations" && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="grid gap-3 lg:grid-cols-[1fr,0.9fr]">
                <div className="rounded-2xl border border-border bg-surface p-4">
                  <h2 className="text-base font-bold text-text">Partner Guide</h2>
                  <div className="mt-3 space-y-2">
                    {GUIDE_CHECKLIST.map((item) => (
                      <div key={item} className="flex items-start gap-3 rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs text-text-muted">
                        <CheckCircle className="mt-0.5 h-4 w-4 text-primary" />
                        <p>{item}</p>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="rounded-2xl border border-border bg-surface p-4">
                  <h2 className="text-base font-bold text-text">What To Fix First</h2>
                  <div className="mt-3 space-y-2 text-xs text-text-muted">
                    <div className="rounded-xl border border-border bg-surface-2 p-3">
                      <p className="font-semibold text-text">If rates are not appearing in cart</p>
                      <p className="mt-2">Check that the row is approved, active, and uses the same country and city the customer enters during checkout.</p>
                    </div>
                    <div className="rounded-xl border border-border bg-surface-2 p-3">
                      <p className="font-semibold text-text">If prepared shipments do not appear</p>
                      <p className="mt-2">Check your profile approval status first, then confirm that the order destination is covered by an approved service area.</p>
                    </div>
                    <div className="rounded-xl border border-border bg-surface-2 p-3">
                      <p className="font-semibold text-text">If admin keeps rejecting updates</p>
                      <p className="mt-2">Use clear city names, accurate country codes, and realistic charge plus ETA values so the review is easy to validate.</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        </div>

        <div className="space-y-4 lg:sticky lg:top-6 lg:self-start">
          <div className="rounded-2xl border border-border bg-surface p-4">
            <h2 className="mb-3 text-sm font-bold text-text">Workspace Snapshot</h2>
            <div className="space-y-2 text-xs text-text-muted">
              <div className="flex items-start gap-2 rounded-xl border border-border bg-surface-2 px-3 py-2">
                <Building2 className="mt-0.5 h-4 w-4 text-primary" />
                <div>
                  <p className="font-semibold text-text">{profile.name || "Add company name"}</p>
                  <p>{profile.code || "Partner code will appear here"}</p>
                </div>
              </div>
              <div className="flex items-start gap-2 rounded-xl border border-border bg-surface-2 px-3 py-2">
                <MapPin className="mt-0.5 h-4 w-4 text-primary" />
                <div>
                  <p className="font-semibold text-text">Base location</p>
                  <p>{[profile.city, profile.region, profile.country].filter(Boolean).join(", ") || "Set city and country"}</p>
                </div>
              </div>
              <div className="flex items-start gap-2 rounded-xl border border-border bg-surface-2 px-3 py-2">
                <Phone className="mt-0.5 h-4 w-4 text-primary" />
                <div>
                  <p className="font-semibold text-text">Primary contact</p>
                  <p>{profile.contact_name || profile.contact_email || profile.contact_phone || "Add contact info"}</p>
                </div>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <div className="rounded-xl border border-border bg-surface-2 p-3">
                  <p className="font-semibold text-text">Portal status</p>
                  <p className="mt-2 capitalize">{titleCase(profile.status)}</p>
                </div>
                <div className="rounded-xl border border-border bg-surface-2 p-3">
                  <p className="font-semibold text-text">Profile approval</p>
                  <p className="mt-2 capitalize">{titleCase(profile.verification_status)}</p>
                </div>
              </div>
              <div className="rounded-xl border border-border bg-surface-2 p-3">
                <p className="font-semibold text-text">Admin note</p>
                <p className="mt-2">{profile.verification_note || "No admin note yet."}</p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-surface p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-text-faint">Readiness & Rate Queue</p>
            <p className="mt-2 text-xl font-bold text-text">{readiness.completed}/{readiness.total}</p>
            <p className="mt-1 text-xs text-text-muted">Core checkpoints before review, plus live queue totals.</p>
            <div className="mt-3 space-y-1.5">
              {readiness.checks.map((check) => (
                <div key={check.label} className="flex items-center gap-2 text-xs">
                  <CheckCircle className={`h-4 w-4 ${check.done ? "text-success" : "text-text-faint"}`} />
                  <span className={check.done ? "text-text" : "text-text-muted"}>{check.label}</span>
                </div>
              ))}
            </div>
            <div className="mt-4 space-y-1.5">
              {[
                { label: "Approved areas", value: approvedAreas, tone: "text-success" },
                { label: "Pending areas", value: pendingAreas, tone: "text-warning" },
                { label: "Rejected areas", value: rejectedAreas, tone: "text-danger" },
                { label: "Pricing profiles live", value: approvedPricingProfiles, tone: "text-success" },
                { label: "Handling rules live", value: approvedCategoryRules, tone: "text-success" },
                { label: "Load-fit rules live", value: approvedVehicleRules, tone: "text-success" },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs">
                  <span className="text-text-muted">{item.label}</span>
                  <span className={`font-bold ${item.tone}`}>{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      </PanelContent>
    </LogisticsPartnerLayout>
  );
}


