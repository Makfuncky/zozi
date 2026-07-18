"use client";

import { Button } from "@/components/ui/Button";

import { type ComponentType, Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Globe,
  Percent,
  Truck,
  Compass,
  CreditCard,
  Scale,
  Map,
  FileCheck,
  DollarSign,
  Layers,
  Tags,
  History,
  Plus,
  Trash2,
  Edit3,
  X,
  Check,
  Building2,
  Eye,
  Globe2,
  RefreshCw,
  Save,
  ShieldCheck,
  UploadCloud,
  ChevronDown,
  ChevronRight,
  Users,
  BarChart3,
  Bell,
  Tag,
  Lock,
  FileText,
  Calendar,
  MapPin,
  MessageCircle,
  MapPinOff,
} from "@/lib/icons";
import CountryMapView from "@/components/country/CountryMapView";
import InternalCommunicationsSystem from "@/components/country/InternalCommunicationsSystem";
import { apiFetch, getErrorMessage, parseJsonResponse } from "@/lib/api";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { isAdminStaffRole } from "@shared/adminPermissions";
import { formatNumber, PieChartComponent, BarChartComponent } from "@/components/ChartComponents";
import CountryLedgerTable from "./CountryLedgerTable";

type ConfigTab =
  | "overview"
  | "tax"
  | "logistics_model"
  | "logistics_providers"
  | "payment_gateways"
  | "legal_rules"
  | "regions"
  | "map"
  | "kyc"
  | "payout_settings"
  | "commission_tiers"
  | "category_commissions"
  | "feature_flags"
  | "analytics"
  | "staff"
  | "communications"
  | "promotions"
  | "localization"
  | "versions";

type VersionStatus = "draft" | "approved" | "published" | "rolled_back" | string;

type FeatureFlag = {
  feature_key: string;
  enabled: boolean;
  config?: Record<string, any>;
};

type CountryStaffAssignment = {
  user_id: number;
  user_name: string;
  email: string;
  role: "country_head" | "country_manager" | "country_finance";
  assigned_at: string;
};

type PromotionRule = {
  slug: string;
  name: string;
  discount_type: "percentage" | "fixed";
  discount_value: number;
  min_order_value?: number | null;
  is_active: boolean;
};

type City = {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  population?: number;
  is_capital?: boolean;
};

type LocalizationConfig = {
  default_language: string;
  supported_languages: string[];
  rtl_enabled: boolean;
  number_format: "western" | "eastern";
  calendar_type: "gregorian" | "hijri";
};

type CountryConfig = {
  code: string;
  name: string;
  currency: string;
  currency_symbol: string | null;
  phone_code: string | null;
  language: string;
  timezone: string;
  tax_type: string;
  tax_rate: number;
  tax_name: string;
  tax_inclusive: boolean;
  tax_exempt_categories: string[];
  tax_reduced_rates: Record<string, number>;
  logistics_model: string;
  default_vehicle_type: string | null;
  base_rate: number | null;
  per_km_rate: number | null;
  minimum_charge: number | null;
  weight_surcharge_rate: number | null;
  weight_surcharge_threshold_kg: number | null;
  payment_methods: string[];
  payment_gateways?: PaymentGatewayItem[];
  logistics_providers?: LogisticsProviderItem[];
  legal_rules?: LegalRules;
  regions?: RegionItem[];
  supplier_requirements?: SupplierRequirements;
  payout_settings?: PayoutSettings;
  commission_tiers?: CommissionTierItem[];
  feature_flags?: FeatureFlag[];
  staff_assignments?: CountryStaffAssignment[];
  promotion_rules?: PromotionRule[];
  localization?: LocalizationConfig;
  is_active: boolean;
};

type DeliveryZone = {
  zone_code: string;
  zone_name: string;
  description?: string | null;
  car_rate: number;
  van_rate: number;
  truck_rate: number;
  weight_surcharge_rate?: number | null;
  weight_surcharge_threshold_kg?: number | null;
  cities: string[];
  is_active: boolean;
  sort_order: number;
};

type CommissionRate = {
  category_slug: string;
  commission_rate: number;
  notes?: string | null;
  is_active: boolean;
};

type ConfigVersion = {
  id: number;
  country_code: string;
  config_type: string;
  version: number;
  status: VersionStatus;
  created_at?: string;
  published_at?: string | null;
};

type TaxPreviewResult = {
  country_code: string;
  tax_type: string;
  tax_name: string;
  tax_rate: number;
  tax_amount: number;
  net_amount: number;
  total_amount: number;
  is_inclusive: boolean;
  currency: string;
};

type PaymentGatewayItem = {
  gateway_id: string;
  name: string;
  type: string;
  enabled: boolean;
  credential_ref: string | null;
  supports_cod: boolean;
  supports_installments: boolean;
  fee_percentage: number;
  fee_fixed: number;
};

type LogisticsProviderItem = {
  provider_id: string;
  name: string;
  enabled: boolean;
  service_areas: string[];
  sla_standard_days: string;
  sla_express_days: string;
  base_rate: number;
  per_kg_rate: number;
  currency: string | null;
};

type LegalRules = {
  minimum_order_age: number;
  max_returns_allowed: number;
  return_window_days: number;
  refund_processing_days: number;
  requires_commercial_license: boolean;
  requires_vat_registration: boolean;
  product_restrictions: string[];
};

type RegionItem = {
  region_id: string;
  name: string;
  cities: string[];
};

type SupplierRequirements = {
  kyc_level: string;
  required_documents: string[];
  approval_required: boolean;
};

type PayoutSettings = {
  minimum_payout_amount: number;
  payout_schedule: string;
  payout_day: string;
  batch_size: number;
  currency: string | null;
};

type CommissionTierItem = {
  min_order_value: number;
  max_order_value: number | null;
  commission_percentage: number;
  fixed_fee: number;
};

const CONFIG_TABS: Array<{ key: ConfigTab; label: string; icon: ComponentType<{ className?: string }> }> = [
  { key: "overview", label: "Overview", icon: Globe },
  { key: "tax", label: "Tax & VAT", icon: Percent },
  { key: "logistics_model", label: "Internal Logistics", icon: Truck },
  { key: "logistics_providers", label: "Delivery Partners", icon: Compass },
  { key: "payment_gateways", label: "Payment Gateways", icon: CreditCard },
  { key: "legal_rules", label: "Legal & Rules", icon: Scale },
  { key: "regions", label: "Regions & Cities", icon: Map },
  { key: "map", label: "Interactive Map", icon: MapPin },
  { key: "kyc", label: "Supplier KYC", icon: FileCheck },
  { key: "payout_settings", label: "Payout Settings", icon: DollarSign },
  { key: "commission_tiers", label: "Value Commissions", icon: Layers },
  { key: "category_commissions", label: "Category Commissions", icon: Tags },
  { key: "feature_flags", label: "Feature Flags", icon: ShieldCheck },
  { key: "analytics", label: "Analytics", icon: BarChart3 },
  { key: "staff", label: "Staff Assignments", icon: Users },
  { key: "communications", label: "Communications", icon: MessageCircle },
  { key: "promotions", label: "Promotions", icon: Tag },
  { key: "localization", label: "Localization", icon: Globe2 },
  { key: "versions", label: "Version History", icon: History },
];

function toErrorMessage(status: number, payload: any, fallback: string): string {
  const detail = payload ? getErrorMessage(payload) : fallback;
  return `${fallback} (HTTP ${status})${detail ? `: ${detail}` : ""}`;
}

function toNumberOrNull(value: string): number | null {
  const normalized = value.trim();
  if (!normalized) return null;
  const parsed = Number(normalized);
  if (!Number.isFinite(parsed)) {
    throw new Error(`Invalid numeric value: ${value}`);
  }
  return parsed;
}

function formatIso(value?: string | null): string {
  if (!value) return "-";
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) return value;
  return new Date(parsed).toLocaleString();
}

export default function AdminCountriesPage() {
  const router = useRouter();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const addToast = useToastStore((state) => state.addToast);

  const [loading, setLoading] = useState(true);
  const [loadingCountry, setLoadingCountry] = useState(false);
  const [activeTab, setActiveTab] = useState<ConfigTab>("overview");
  const [activeVersionType, setActiveVersionType] = useState<string>("all");
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [activityMessage, setActivityMessage] = useState<string>("");

  // Create Country Record State
  const [newCountryCode, setNewCountryCode] = useState("");
  const [newCountryName, setNewCountryName] = useState("");
  const [newCountryCurrency, setNewCountryCurrency] = useState("SAR");
  const [newCountryTimezone, setNewCountryTimezone] = useState("Asia/Riyadh");
  const [newCurrencySymbol, setNewCurrencySymbol] = useState("SR");
  const [newPhoneCode, setNewPhoneCode] = useState("+966");
  const [newLanguage, setNewLanguage] = useState("en");
  const [newCountryIsActive, setNewCountryIsActive] = useState(true);
  const [creatingCountry, setCreatingCountry] = useState(false);

  // Loaded Context Data
  const [countries, setCountries] = useState<CountryConfig[]>([]);
  const [selectedCountryCode, setSelectedCountryCode] = useState<string>("");
  const [country, setCountry] = useState<CountryConfig | null>(null);
  const [deliveryZones, setDeliveryZones] = useState<DeliveryZone[]>([]);
  const [categoryCommissions, setCategoryCommissions] = useState<CommissionRate[]>([]);
  const [versions, setVersions] = useState<ConfigVersion[]>([]);
  const [cities, setCities] = useState<City[]>([]);

  // 1. Overview Form State
  const [name, setName] = useState("");
  const [currencySymbol, setCurrencySymbol] = useState("");
  const [phoneCode, setPhoneCode] = useState("");
  const [language, setLanguage] = useState("en");
  const [isActive, setIsActive] = useState(true);

  // 2. Tax Form State
  const [taxType, setTaxType] = useState("VAT");
  const [taxRate, setTaxRate] = useState("0.15");
  const [taxName, setTaxName] = useState("VAT");
  const [taxInclusive, setTaxInclusive] = useState(false);
  const [taxExemptCategories, setTaxExemptCategories] = useState("");
  const [reducedTaxRates, setReducedTaxRates] = useState<Array<{ category: string; rate: string }>>([]);
  const [newReducedCategory, setNewReducedCategory] = useState("");
  const [newReducedRate, setNewReducedRate] = useState("0.05");

  // Tax Preview State
  const [previewAmount, setPreviewAmount] = useState("100");
  const [previewCategory, setPreviewCategory] = useState("");
  const [previewInclusive, setPreviewInclusive] = useState<"auto" | "inclusive" | "exclusive">("auto");
  const [previewResult, setPreviewResult] = useState<TaxPreviewResult | null>(null);

  // 3. Internal Logistics Form State
  const [logisticsModel, setLogisticsModel] = useState("fixed");
  const [defaultVehicleType, setDefaultVehicleType] = useState("van");
  const [baseRate, setBaseRate] = useState("15");
  const [perKmRate, setPerKmRate] = useState("1.5");
  const [minimumCharge, setMinimumCharge] = useState("15");
  const [weightSurchargeRate, setWeightSurchargeRate] = useState("2");
  const [weightThresholdKg, setWeightThresholdKg] = useState("10");

  // Delivery Zones Sub-Editor
  const [newZoneCode, setNewZoneCode] = useState("");
  const [newZoneName, setNewZoneName] = useState("");
  const [newZoneDescription, setNewZoneDescription] = useState("");
  const [newZoneCarRate, setNewZoneCarRate] = useState("15");
  const [newZoneVanRate, setNewZoneVanRate] = useState("20");
  const [newZoneTruckRate, setNewZoneTruckRate] = useState("40");
  const [newZoneWeightSurcharge, setNewZoneWeightSurcharge] = useState("2");
  const [newZoneWeightThreshold, setNewZoneWeightThreshold] = useState("10");
  const [newZoneCities, setNewZoneCities] = useState("");

  // 4. Delivery Partners Form State
  const [providers, setProviders] = useState<LogisticsProviderItem[]>([]);
  const [newProviderId, setNewProviderId] = useState("");
  const [newProviderName, setNewProviderName] = useState("");
  const [newProviderServiceAreas, setNewProviderServiceAreas] = useState("all_regions");
  const [newProviderSlaStd, setNewProviderSlaStd] = useState("2-3");
  const [newProviderSlaExp, setNewProviderSlaExp] = useState("1");
  const [newProviderBaseRate, setNewProviderBaseRate] = useState("15");
  const [newProviderPerKg, setNewProviderPerKg] = useState("2");
  const [newProviderCurrency, setNewProviderCurrency] = useState("SAR");

  // 5. Payment Gateways Form State
  const [gateways, setGateways] = useState<PaymentGatewayItem[]>([]);
  const [newGatewayId, setNewGatewayId] = useState("");
  const [newGatewayName, setNewGatewayName] = useState("");
  const [newGatewayType, setNewGatewayType] = useState("card");
  const [newGatewayCredRef, setNewGatewayCredRef] = useState("");
  const [newGatewaySupportsCod, setNewGatewaySupportsCod] = useState(false);
  const [newGatewaySupportsInstall, setNewGatewaySupportsInstall] = useState(false);
  const [newGatewayFeePct, setNewGatewayFeePct] = useState("2.5");
  const [newGatewayFeeFixed, setNewGatewayFeeFixed] = useState("1");

  // 6. Legal & Rules Form State
  const [minimumOrderAge, setMinimumOrderAge] = useState(18);
  const [maxReturnsAllowed, setMaxReturnsAllowed] = useState(3);
  const [returnWindowDays, setReturnWindowDays] = useState(14);
  const [refundProcessingDays, setRefundProcessingDays] = useState(7);
  const [requiresCommercialLicense, setRequiresCommercialLicense] = useState(false);
  const [requiresVatRegistration, setRequiresVatRegistration] = useState(false);
  const [productRestrictions, setProductRestrictions] = useState("");

  // 7. Regions Form State
  const [regions, setRegions] = useState<RegionItem[]>([]);
  const [newRegionName, setNewRegionName] = useState("");
  const [newRegionCities, setNewRegionCities] = useState("");
  const [expandedRegions, setExpandedRegions] = useState<Record<string, boolean>>({});

  // 8. Supplier Requirements State
  const [kycLevel, setKycLevel] = useState("standard");
  const [requiredDocuments, setRequiredDocuments] = useState<string[]>([]);
  const [approvalRequired, setApprovalRequired] = useState(true);

  // 9. Payout Settings Form State
  const [minimumPayoutAmount, setMinimumPayoutAmount] = useState("100");
  const [payoutSchedule, setPayoutSchedule] = useState("weekly");
  const [payoutDay, setPayoutDay] = useState("sunday");
  const [batchSize, setBatchSize] = useState("50");
  const [payoutCurrency, setPayoutCurrency] = useState("SAR");

  // 9b. Payout Rules State (category + product overrides)
  const [catPayoutRules, setCatPayoutRules] = useState<any[]>([]);
  const [prodPayoutRules, setProdPayoutRules] = useState<any[]>([]);
  const [newCatPayoutSlug, setNewCatPayoutSlug] = useState("");
  const [newCatPayoutRate, setNewCatPayoutRate] = useState("0.80");
  const [newProdPayoutId, setNewProdPayoutId] = useState("");
  const [newProdPayoutRate, setNewProdPayoutRate] = useState("0.85");

  // 10. Value Commissions Form State
  const [commissionTiers, setCommissionTiers] = useState<CommissionTierItem[]>([]);
  const [newTierMin, setNewTierMin] = useState("0");
  const [newTierMax, setNewTierMax] = useState("");
  const [newTierPct, setNewTierPct] = useState("5");
  const [newTierFixed, setNewTierFixed] = useState("0");

  // 12. Category Commissions Form State
  const [newCategorySlug, setNewCategorySlug] = useState("");
  const [bulkFillRate, setBulkFillRate] = useState("0.10");
  const [newCategoryRate, setNewCategoryRate] = useState("0.10");
  const [newCategoryNotes, setNewCategoryNotes] = useState("");

  // 13. All categories for commission section
  const [allCategories, setAllCategories] = useState<Array<{ id: number; slug: string; name: string; parent_id: number | null; commission_rate: number | null }>>([]);

  // 14. Feature Flags State
  const [featureFlags, setFeatureFlags] = useState<FeatureFlag[]>([]);
  const [newFeatureKey, setNewFeatureKey] = useState("");
  const [newFeatureEnabled, setNewFeatureEnabled] = useState(true);

  // 15. Staff Assignments State
  const [staffAssignments, setStaffAssignments] = useState<CountryStaffAssignment[]>([]);
  const [newStaffUserId, setNewStaffUserId] = useState("");
  const [newStaffUserName, setNewStaffUserName] = useState("");
  const [newStaffEmail, setNewStaffEmail] = useState("");
  const [newStaffRole, setNewStaffRole] = useState<"country_head" | "country_manager" | "country_finance">("country_manager");

  // 16. Promotions State
  const [promotionRules, setPromotionRules] = useState<PromotionRule[]>([]);
  const [newPromoSlug, setNewPromoSlug] = useState("");
  const [newPromoName, setNewPromoName] = useState("");
  const [newPromoType, setNewPromoType] = useState<"percentage" | "fixed">("percentage");
  const [newPromoValue, setNewPromoValue] = useState("10");
  const [newPromoMinOrder, setNewPromoMinOrder] = useState("");

  // 17. Localization State
  const [localization, setLocalization] = useState<LocalizationConfig>({
    default_language: "en",
    supported_languages: ["en", "ar"],
    rtl_enabled: false,
    number_format: "western",
    calendar_type: "gregorian",
  });

  // 18. Auto-populate search state (for debounced search)
  const [autoPopulateSearch, setAutoPopulateSearch] = useState("");
  const [searchingCountry, setSearchingCountry] = useState(false);
  const [autoPopulateResult, setAutoPopulateResult] = useState<any>(null);

  const selectedCountry = useMemo(
    () => countries.find((entry) => entry.code === selectedCountryCode) ?? country,
    [countries, selectedCountryCode, country],
  );

  // Role-based tab visibility
  // Country Managers can only see limited tabs
  const allowedTabs = useMemo(() => {
    const userRole = user?.role;
    const allTabs = CONFIG_TABS.map(t => t.key);
    
    if (userRole === "country_head") {
      return allTabs; // Full access
    }
    if (userRole === "country_manager") {
      // Limited access for country managers
      return [
        "overview",
        "tax",
        "logistics_model",
        "logistics_providers",
        "payment_gateways",
        "regions",
        "commission_tiers",
        "category_commissions",
      ];
    }
    // country_finance or admin - full access
    return allTabs;
  }, [user?.role]);

  const visibleTabs = useMemo(() => {
    return CONFIG_TABS.filter(tab => allowedTabs.includes(tab.key));
  }, [allowedTabs]);

  const canSubmit = selectedCountryCode.length > 0 && !loadingCountry;

  const hydrateCountryWorkspace = useCallback(
    async (countryCode: string) => {
      if (!countryCode) return;
      setLoadingCountry(true);
      try {
        const [countryResponse, zonesResponse, commissionsResponse, versionsResponse, catPayoutRes, prodPayoutRes, featureFlagsRes, staffRes, promotionsRes, localizationRes, citiesRes] = await Promise.all([
          apiFetch(`/admin/countries/${countryCode}`),
          apiFetch(`/admin/countries/${countryCode}/delivery-zones`),
          apiFetch(`/admin/countries/${countryCode}/commissions`),
          apiFetch(`/admin/countries/${countryCode}/versions`),
          apiFetch(`/admin/countries/${countryCode}/payout-rules/categories`),
          apiFetch(`/admin/countries/${countryCode}/payout-rules/products`),
          apiFetch(`/admin/countries/${countryCode}/feature-flags`),
          apiFetch(`/admin/countries/${countryCode}/staff`),
          apiFetch(`/admin/countries/${countryCode}/promotions`),
          apiFetch(`/admin/countries/${countryCode}/localization`),
          apiFetch(`/admin/countries/${countryCode}/cities`),
        ]);

        const [countryPayload, zonesPayload, commissionsPayload, versionsPayload, citiesPayload] = await Promise.all([
          parseJsonResponse(countryResponse),
          parseJsonResponse(zonesResponse),
          parseJsonResponse(commissionsResponse),
          parseJsonResponse(versionsResponse),
          parseJsonResponse(citiesRes),
        ]);

        if (!countryResponse.ok) {
          throw new Error(toErrorMessage(countryResponse.status, countryPayload, "Failed to load country config"));
        }
        if (!zonesResponse.ok) {
          throw new Error(toErrorMessage(zonesResponse.status, zonesPayload, "Failed to load delivery zones"));
        }
        if (!commissionsResponse.ok) {
          throw new Error(toErrorMessage(commissionsResponse.status, commissionsPayload, "Failed to load commissions"));
        }
        if (!versionsResponse.ok) {
          throw new Error(toErrorMessage(versionsResponse.status, versionsPayload, "Failed to load versions"));
        }

        const nextCountry = countryPayload as CountryConfig;
        const nextZones = Array.isArray(zonesPayload) ? (zonesPayload as DeliveryZone[]) : [];
        const nextCommissions = Array.isArray(commissionsPayload) ? (commissionsPayload as CommissionRate[]) : [];
        const nextVersions = Array.isArray(versionsPayload) ? (versionsPayload as ConfigVersion[]) : [];
        const nextCities = Array.isArray(citiesPayload) ? (citiesPayload as City[]) : [];

        setCountry(nextCountry);
        setDeliveryZones(nextZones);
        setCategoryCommissions(nextCommissions);
        setVersions(nextVersions);
        setCities(nextCities);

        if (catPayoutRes.ok) {
          const catData = await parseJsonResponse(catPayoutRes);
          setCatPayoutRules(Array.isArray(catData) ? catData : []);
        }
        if (prodPayoutRes.ok) {
          const prodData = await parseJsonResponse(prodPayoutRes);
          setProdPayoutRules(Array.isArray(prodData) ? prodData : []);
        }

        // Populate Form States
        // 1. Overview Form
        setName(nextCountry.name || "");
        setCurrencySymbol(nextCountry.currency_symbol || "");
        setPhoneCode(nextCountry.phone_code || "");
        setLanguage(nextCountry.language || "en");
        setIsActive(Boolean(nextCountry.is_active));

        // 2. Tax Form
        setTaxType(nextCountry.tax_type || "VAT");
        setTaxRate(String(nextCountry.tax_rate ?? "0"));
        setTaxName(nextCountry.tax_name || "Tax");
        setTaxInclusive(Boolean(nextCountry.tax_inclusive));
        setTaxExemptCategories((nextCountry.tax_exempt_categories || []).join(", "));
        const reducedArr = Object.entries(nextCountry.tax_reduced_rates || {}).map(([cat, rate]) => ({
          category: cat,
          rate: String(rate),
        }));
        setReducedTaxRates(reducedArr);

        // 3. Internal Logistics
        setLogisticsModel(nextCountry.logistics_model || "fixed");
        setDefaultVehicleType(nextCountry.default_vehicle_type || "van");
        setBaseRate(nextCountry.base_rate == null ? "" : String(nextCountry.base_rate));
        setPerKmRate(nextCountry.per_km_rate == null ? "" : String(nextCountry.per_km_rate));
        setMinimumCharge(nextCountry.minimum_charge == null ? "" : String(nextCountry.minimum_charge));
        setWeightSurchargeRate(nextCountry.weight_surcharge_rate == null ? "" : String(nextCountry.weight_surcharge_rate));
        setWeightThresholdKg(nextCountry.weight_surcharge_threshold_kg == null ? "" : String(nextCountry.weight_surcharge_threshold_kg));

        // 4. Delivery Partners
        setProviders(nextCountry.logistics_providers || []);

        // 5. Payment Gateways
        setGateways(nextCountry.payment_gateways || []);

        // 6. Legal & Rules
        setMinimumOrderAge(nextCountry.legal_rules?.minimum_order_age ?? 18);
        setMaxReturnsAllowed(nextCountry.legal_rules?.max_returns_allowed ?? 3);
        setReturnWindowDays(nextCountry.legal_rules?.return_window_days ?? 14);
        setRefundProcessingDays(nextCountry.legal_rules?.refund_processing_days ?? 7);
        setRequiresCommercialLicense(Boolean(nextCountry.legal_rules?.requires_commercial_license));
        setRequiresVatRegistration(Boolean(nextCountry.legal_rules?.requires_vat_registration));
        setProductRestrictions((nextCountry.legal_rules?.product_restrictions || []).join(", "));

        // 7. Regions
        setRegions(nextCountry.regions || []);

        // 8. Supplier Requirements
        setKycLevel(nextCountry.supplier_requirements?.kyc_level || "standard");
        setRequiredDocuments(nextCountry.supplier_requirements?.required_documents || []);
        setApprovalRequired(nextCountry.supplier_requirements?.approval_required ?? true);

        // 9. Payout Settings
        setMinimumPayoutAmount(String(nextCountry.payout_settings?.minimum_payout_amount ?? "100"));
        setPayoutSchedule(nextCountry.payout_settings?.payout_schedule || "weekly");
        setPayoutDay(nextCountry.payout_settings?.payout_day || "sunday");
        setBatchSize(String(nextCountry.payout_settings?.batch_size ?? "50"));
        setPayoutCurrency(nextCountry.payout_settings?.currency || nextCountry.currency || "");

        // 10. Value Commissions
        setCommissionTiers(nextCountry.commission_tiers || []);

        // 11. Feature Flags
        if (featureFlagsRes.ok) {
          const ffData = await parseJsonResponse(featureFlagsRes);
          setFeatureFlags(Array.isArray(ffData) ? ffData : []);
        }

        // 12. Staff Assignments
        if (staffRes.ok) {
          const staffData = await parseJsonResponse(staffRes);
          setStaffAssignments(Array.isArray(staffData) ? staffData : []);
        }

        // 13. Promotions
        if (promotionsRes.ok) {
          const promoData = await parseJsonResponse(promotionsRes);
          setPromotionRules(Array.isArray(promoData) ? promoData : []);
        }

        // 14. Localization
        if (localizationRes.ok) {
          const locData = await parseJsonResponse(localizationRes);
          setLocalization(locData || {
            default_language: "en",
            supported_languages: ["en", "ar"],
            rtl_enabled: false,
            number_format: "western",
            calendar_type: "gregorian",
          });
        }

        setPreviewResult(null);
      } finally {
        setLoadingCountry(false);
      }
    },
    [],
  );

  const loadAllCategories = useCallback(async () => {
    try {
      const response = await apiFetch("/categories/admin/flat");
      const payload = await parseJsonResponse(response);
      if (response.ok && Array.isArray(payload)) {
        setAllCategories(payload);
      }
    } catch {
      // non-critical; categories just won't show in dropdown
    }
  }, []);

  const loadPayoutRules = useCallback(async (countryCode: string) => {
    try {
      const [catRes, prodRes] = await Promise.all([
        apiFetch(`/admin/countries/${countryCode}/payout-rules/categories`),
        apiFetch(`/admin/countries/${countryCode}/payout-rules/products`),
      ]);
      if (catRes.ok) {
        const data = await parseJsonResponse(catRes);
        setCatPayoutRules(Array.isArray(data) ? data : []);
      }
      if (prodRes.ok) {
        const data = await parseJsonResponse(prodRes);
        setProdPayoutRules(Array.isArray(data) ? data : []);
      }
    } catch {
      // non-critical
    }
  }, []);

  const autoPopulateCountry = useCallback(async () => {
    const term = autoPopulateSearch.trim();
    if (!term) {
      addToast("Enter a country name or code to search", "warning");
      return;
    }
    setSearchingCountry(true);
    setAutoPopulateResult(null);
    try {
      const response = await apiFetch("/admin/countries/auto-populate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ search_term: term }),
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(data?.detail || "Auto-populate failed");
      }
      setAutoPopulateResult(data);
      // Fill form fields
      setNewCountryCode(data.code || "");
      setNewCountryName(data.name || "");
      setNewCountryCurrency(data.currency || "");
      setNewCurrencySymbol(data.currency_symbol || "");
      setNewPhoneCode(data.phone_code || "");
      setNewLanguage(data.language || "en");
      setNewCountryTimezone(data.timezone || "UTC");
      // Store enhanced suggestions for display in preview
      if (data.suggested_tax_rate != null) {
        setTaxRate(String((data.suggested_tax_rate * 100).toFixed(1)));
        if (data.suggested_tax_name) setTaxName(data.suggested_tax_name);
        if (data.suggested_tax_type) setTaxType(data.suggested_tax_type);
      }
      if (data.suggested_legal_rules) {
        setMinimumOrderAge(data.suggested_legal_rules.minimum_order_age ?? 18);
        setMaxReturnsAllowed(data.suggested_legal_rules.max_returns_allowed ?? 3);
        setReturnWindowDays(data.suggested_legal_rules.return_window_days ?? 7);
        setRefundProcessingDays(data.suggested_legal_rules.refund_processing_days ?? 7);
        if (data.suggested_legal_rules.product_restrictions) {
          setProductRestrictions(data.suggested_legal_rules.product_restrictions.join(", "));
        }
      }
      if (data.suggested_cities?.length > 0) {
        // Pre-fill first region with suggested cities
        setNewRegionName(data.name ? `${data.name} Region` : "");
        setNewRegionCities(data.suggested_cities.slice(0, 10).join(", "));
      }
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Auto-populate failed", "error");
      setAutoPopulateResult(null);
    } finally {
      setSearchingCountry(false);
    }
  }, [autoPopulateSearch, addToast]);

  const loadCountries = useCallback(async () => {
    const response = await apiFetch("/admin/countries");
    const payload = await parseJsonResponse(response);
    if (!response.ok) {
      throw new Error(toErrorMessage(response.status, payload, "Failed to load countries"));
    }

    let items = Array.isArray(payload) ? (payload as CountryConfig[]) : [];

    // If country_head or country_manager, filter to assigned countries only
    if (user?.role === "country_head" || user?.role === "country_manager") {
      const assigned = (user?.staff_country_codes ?? []).map((c: string) => c.toUpperCase());
      if (assigned.length > 0) {
        items = items.filter((c) => assigned.includes(c.code.toUpperCase()));
      }
    }

    setCountries(items);

    const preferredCode = selectedCountryCode || items[0]?.code || "";
    if (preferredCode) {
      setSelectedCountryCode(preferredCode);
      await hydrateCountryWorkspace(preferredCode);
    }
  }, [hydrateCountryWorkspace, selectedCountryCode, user?.role, user?.staff_country_codes]);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !isAdminStaffRole(user?.role)) {
      router.replace("/admin/login");
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        await Promise.all([loadCountries(), loadAllCategories()]);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to load country workspace";
        addToast(message, "error");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [addToast, authLoading, isLoggedIn, loadCountries, loadAllCategories, router, user?.role]);

  const createCountry = async () => {
    setCreatingCountry(true);
    try {
      const code = newCountryCode.trim().toUpperCase();
      const nameVal = newCountryName.trim();
      const currency = newCountryCurrency.trim().toUpperCase();
      const timezone = newCountryTimezone.trim();

      if (!code || !nameVal || !currency || !timezone) {
        throw new Error("Code, name, currency, and timezone are required to create a country.");
      }

      const response = await apiFetch("/admin/countries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code,
          name: nameVal,
          currency,
          timezone,
          currency_symbol: newCurrencySymbol.trim(),
          phone_code: newPhoneCode.trim(),
          language: newLanguage.trim(),
          is_active: newCountryIsActive
        }),
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(toErrorMessage(response.status, data, "Failed to create country"));
      }

      addToast(`Country ${code} created`, "success");
      setActivityMessage(`Created country ${code}.`);
      setNewCountryCode("");
      setNewCountryName("");
      setNewCountryCurrency("SAR");
      setNewCountryTimezone("Asia/Riyadh");
      setNewCurrencySymbol("SR");
      setNewPhoneCode("+966");
      setNewLanguage("en");
      setNewCountryIsActive(true);
      setSelectedCountryCode(code);
      await loadCountries();
      await hydrateCountryWorkspace(code);
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to create country", "error");
    } finally {
      setCreatingCountry(false);
    }
  };

  // Submit Handlers for individual draft tabs

  const submitIdentity = async () => {
    if (!selectedCountryCode) return;
    setBusyAction("identity");
    try {
      const response = await apiFetch(`/admin/countries/${selectedCountryCode}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          currency_symbol: currencySymbol.trim() || null,
          phone_code: phoneCode.trim() || null,
          language: language.trim() || "en",
          is_active: isActive
        })
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(toErrorMessage(response.status, data, "Failed to update country identity"));
      }
      addToast("Country identity updated", "success");
      setActivityMessage(`Country identity updated successfully.`);
      await loadCountries();
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to update country identity", "error");
    } finally {
      setBusyAction(null);
    }
  };

  const submitTaxDraft = async () => {
    if (!selectedCountryCode) return;
    setBusyAction("tax");
    try {
      const reducedMap: Record<string, number> = {};
      reducedTaxRates.forEach((item) => {
        const cat = item.category.trim();
        const rateVal = Number(item.rate);
        if (cat && !Number.isNaN(rateVal)) {
          reducedMap[cat] = rateVal;
        }
      });

      const payload = {
        tax_type: taxType.trim().toUpperCase(),
        tax_rate: Number(taxRate),
        tax_name: taxName.trim(),
        tax_inclusive: taxInclusive,
        tax_exempt_categories: taxExemptCategories
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
        tax_reduced_rates: reducedMap,
      };

      const response = await apiFetch(`/admin/countries/${selectedCountryCode}/tax`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(toErrorMessage(response.status, data, "Failed to create tax draft"));
      }

      addToast("Tax draft created", "success");
      setActivityMessage(`Tax draft created (version ${String(data?.version ?? "-")}).`);
      await hydrateCountryWorkspace(selectedCountryCode);
      setActiveTab("versions");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to create tax draft", "error");
    } finally {
      setBusyAction(null);
    }
  };

  const previewTax = async () => {
    if (!selectedCountryCode) return;
    setBusyAction("tax-preview");
    try {
      const parsedAmount = Number(previewAmount);
      if (!Number.isFinite(parsedAmount) || parsedAmount < 0) {
        throw new Error("Preview amount must be a valid non-negative number");
      }

      const payload: Record<string, unknown> = {
        amount: parsedAmount,
      };
      if (previewCategory.trim()) {
        payload.category = previewCategory.trim();
      }
      if (previewInclusive !== "auto") {
        payload.inclusive = previewInclusive === "inclusive";
      }

      const response = await apiFetch(`/admin/countries/${selectedCountryCode}/preview-tax`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(toErrorMessage(response.status, data, "Failed to preview tax"));
      }

      setPreviewResult(data as TaxPreviewResult);
      setActivityMessage("Tax preview completed.");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to preview tax", "error");
    } finally {
      setBusyAction(null);
    }
  };

  const submitLogisticsDraft = async () => {
    if (!selectedCountryCode) return;
    setBusyAction("logistics");
    try {
      const payload = {
        logistics_model: logisticsModel.trim().toLowerCase(),
        default_vehicle_type: defaultVehicleType.trim() || null,
        base_rate: toNumberOrNull(baseRate),
        per_km_rate: toNumberOrNull(perKmRate),
        minimum_charge: toNumberOrNull(minimumCharge),
        weight_surcharge_rate: toNumberOrNull(weightSurchargeRate),
        weight_surcharge_threshold_kg: toNumberOrNull(weightThresholdKg),
        delivery_zones: deliveryZones,
      };

      const response = await apiFetch(`/admin/countries/${selectedCountryCode}/logistics`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(toErrorMessage(response.status, data, "Failed to create logistics draft"));
      }

      addToast("Logistics draft created", "success");
      setActivityMessage(`Logistics draft created (version ${String(data?.version ?? "-")}).`);
      await hydrateCountryWorkspace(selectedCountryCode);
      setActiveTab("versions");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to create logistics draft", "error");
    } finally {
      setBusyAction(null);
    }
  };

  const submitLogisticsProvidersDraft = async () => {
    if (!selectedCountryCode) return;
    setBusyAction("logistics_providers");
    try {
      const response = await apiFetch(`/admin/countries/${selectedCountryCode}/logistics-providers`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ providers })
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(toErrorMessage(response.status, data, "Failed to create logistics partners draft"));
      }
      addToast("Logistics partners draft created", "success");
      setActivityMessage(`Logistics partners draft created (version ${String(data?.version ?? "-")}).`);
      await hydrateCountryWorkspace(selectedCountryCode);
      setActiveTab("versions");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to create logistics partners draft", "error");
    } finally {
      setBusyAction(null);
    }
  };

  const submitPaymentGatewaysDraft = async () => {
    if (!selectedCountryCode) return;
    setBusyAction("payment_gateways");
    try {
      const response = await apiFetch(`/admin/countries/${selectedCountryCode}/payment-gateways`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ gateways })
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(toErrorMessage(response.status, data, "Failed to create payment gateways draft"));
      }
      addToast("Payment gateways draft created", "success");
      setActivityMessage(`Payment gateways draft created (version ${String(data?.version ?? "-")}).`);
      await hydrateCountryWorkspace(selectedCountryCode);
      setActiveTab("versions");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to create payment gateways draft", "error");
    } finally {
      setBusyAction(null);
    }
  };

  const submitLegalRulesDraft = async () => {
    if (!selectedCountryCode) return;
    setBusyAction("legal_rules");
    try {
      const payload = {
        minimum_order_age: Number(minimumOrderAge),
        max_returns_allowed: Number(maxReturnsAllowed),
        return_window_days: Number(returnWindowDays),
        refund_processing_days: Number(refundProcessingDays),
        requires_commercial_license: requiresCommercialLicense,
        requires_vat_registration: requiresVatRegistration,
        product_restrictions: productRestrictions
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
      };

      const response = await apiFetch(`/admin/countries/${selectedCountryCode}/legal-rules`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(toErrorMessage(response.status, data, "Failed to create legal rules draft"));
      }

      addToast("Legal rules draft created", "success");
      setActivityMessage(`Legal rules draft created (version ${String(data?.version ?? "-")}).`);
      await hydrateCountryWorkspace(selectedCountryCode);
      setActiveTab("versions");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to create legal rules draft", "error");
    } finally {
      setBusyAction(null);
    }
  };

  const submitRegionsDraft = async () => {
    if (!selectedCountryCode) return;
    setBusyAction("regions");
    try {
      const response = await apiFetch(`/admin/countries/${selectedCountryCode}/regions`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ regions })
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(toErrorMessage(response.status, data, "Failed to create regions draft"));
      }
      addToast("Regions draft created", "success");
      setActivityMessage(`Regions draft created (version ${String(data?.version ?? "-")}).`);
      await hydrateCountryWorkspace(selectedCountryCode);
      setActiveTab("versions");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to create regions draft", "error");
    } finally {
      setBusyAction(null);
    }
  };

  const submitSupplierRequirementsDraft = async () => {
    if (!selectedCountryCode) return;
    setBusyAction("supplier_requirements");
    try {
      const payload = {
        kyc_level: kycLevel,
        required_documents: requiredDocuments,
        approval_required: approvalRequired
      };
      const response = await apiFetch(`/admin/countries/${selectedCountryCode}/supplier-requirements`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(toErrorMessage(response.status, data, "Failed to create supplier requirements draft"));
      }
      addToast("Supplier requirements draft created", "success");
      setActivityMessage(`Supplier requirements draft created (version ${String(data?.version ?? "-")}).`);
      await hydrateCountryWorkspace(selectedCountryCode);
      setActiveTab("versions");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to create supplier requirements draft", "error");
    } finally {
      setBusyAction(null);
    }
  };

  const submitPayoutSettingsDraft = async () => {
    if (!selectedCountryCode) return;
    setBusyAction("payout_settings");
    try {
      const payload = {
        minimum_payout_amount: Number(minimumPayoutAmount),
        payout_schedule: payoutSchedule,
        payout_day: payoutDay,
        batch_size: Number(batchSize),
        currency: payoutCurrency.trim() || null
      };
      const response = await apiFetch(`/admin/countries/${selectedCountryCode}/payout-settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(toErrorMessage(response.status, data, "Failed to create payout settings draft"));
      }
      addToast("Payout settings draft created", "success");
      setActivityMessage(`Payout settings draft created (version ${String(data?.version ?? "-")}).`);
      await hydrateCountryWorkspace(selectedCountryCode);
      setActiveTab("versions");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to create payout settings draft", "error");
    } finally {
      setBusyAction(null);
    }
  };

  const submitCommissionTiersDraft = async () => {
    if (!selectedCountryCode) return;
    setBusyAction("commission_tiers");
    try {
      const response = await apiFetch(`/admin/countries/${selectedCountryCode}/commission-tiers`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tiers: commissionTiers })
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(toErrorMessage(response.status, data, "Failed to create commission tiers draft"));
      }
      addToast("Commission tiers draft created", "success");
      setActivityMessage(`Commission tiers draft created (version ${String(data?.version ?? "-")}).`);
      await hydrateCountryWorkspace(selectedCountryCode);
      setActiveTab("versions");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to create commission tiers draft", "error");
    } finally {
      setBusyAction(null);
    }
  };

  const submitCategoryCommissionsDraft = async () => {
    if (!selectedCountryCode) return;
    setBusyAction("category_commissions");
    try {
      const response = await apiFetch(`/admin/countries/${selectedCountryCode}/commissions`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rates: categoryCommissions })
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(toErrorMessage(response.status, data, "Failed to create category commissions draft"));
      }
      addToast("Category commissions draft created", "success");
      setActivityMessage(`Category commissions draft created (version ${String(data?.version ?? "-")}).`);
      await hydrateCountryWorkspace(selectedCountryCode);
      setActiveTab("versions");
    } catch (error) {
      addToast(error instanceof Error ? error.message : "Failed to create category commissions draft", "error");
    } finally {
      setBusyAction(null);
    }
  };

  const actOnVersion = async (version: ConfigVersion, action: "approve" | "publish" | "rollback") => {
    if (!selectedCountryCode) return;
    setBusyAction(`${action}-${version.id}`);
    try {
      const response = await apiFetch(`/admin/countries/${selectedCountryCode}/versions/${version.id}/${action}`, {
        method: "POST",
      });
      const data = await parseJsonResponse(response);
      if (!response.ok) {
        throw new Error(toErrorMessage(response.status, data, `Failed to ${action} version`));
      }

      addToast(`Version ${action} completed`, "success");
      setActivityMessage(`Version v${version.version} (${version.config_type}) ${action} completed.`);
      await hydrateCountryWorkspace(selectedCountryCode);
    } catch (error) {
      addToast(error instanceof Error ? error.message : `Failed to ${action} version`, "error");
    } finally {
      setBusyAction(null);
    }
  };

  const filteredVersions = useMemo(() => {
    if (activeVersionType === "all") return versions;
    return versions.filter((row) => row.config_type === activeVersionType);
  }, [activeVersionType, versions]);

  // Build country summaries for the ledger
  const countrySummaries = useMemo(() => countries.map((c) => ({
    code: c.code,
    name: c.name,
    currency: c.currency,
    currency_symbol: c.currency_symbol,
    tax_rate: ((c.tax_rate ?? 0) * 100),
    tax_name: c.tax_name || "Tax",
    is_active: c.is_active,
    city_count: (c as any).city_count ?? (Array.isArray(c.regions) ? c.regions.reduce((acc: number, r: RegionItem) => acc + (r.cities?.length || 0), 0) : 0),
    commission_count: categoryCommissions.filter((cc) => cc.is_active).length,
    flag_url: (c as any).flag_url,
    region: (c as any).region,
    economic_tier: (c as any).economic_tier,
    population: (c as any).population,
    internet_penetration_pct: (c as any).internet_penetration_pct,
  })), [countries, categoryCommissions]);

  // Track which country row is expanded (only one at a time)
  const [expandedCountryCode, setExpandedCountryCode] = useState<string | null>(null);

  const handleCountryChange = useCallback(async (code: string) => {
    setSelectedCountryCode(code);
    setActivityMessage("");
    await hydrateCountryWorkspace(code);
  }, [hydrateCountryWorkspace]);

  // When expand/collapse toggles, call handleCountryChange for the new country
  const handleToggleExpand = useCallback(async (code: string) => {
    if (expandedCountryCode === code) {
      setExpandedCountryCode(null);
    } else {
      setExpandedCountryCode(code);
      await handleCountryChange(code);
    }
  }, [expandedCountryCode, handleCountryChange]);

  if (authLoading || loading) {
    return (
      <AdminLayout title="Countries">
        <PanelLoadingState count={5} />
      </AdminLayout>
    );
  }

  if (!isLoggedIn || !isAdminStaffRole(user?.role)) {
    return null;
  }

  return (
    <AdminLayout title="Countries" headerMode="compact">
      <PanelContent width="full" className="space-y-4">
        {/* Single Ledger — all countries, expandable rows */}
        <section className="theme-card rounded-xl border p-4">
          <CountryLedgerTable
            countries={countrySummaries}
            expandedCode={expandedCountryCode}
            onToggleExpand={handleToggleExpand}
            onRefresh={() => { loadCountries(); setExpandedCountryCode(null); }}
            loading={loading}
            onAutoPopulateResult={(result) => {
              // Auto-populate search result is already applied to ghost form
              // This callback can be used for additional side effects if needed
            }}
          >
            {/* Full country configuration workspace (shown inside expanded row) */}
            {expandedCountryCode && country && !loadingCountry ? (
              <>
                {/* Activity Message */}
                {activityMessage && (
                  <div data-testid="country-activity-message" className="rounded-lg border border-info/30 bg-info/5 px-4 py-2 text-xs text-info flex items-center gap-2">
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    {activityMessage}
                  </div>
                )}

                {/* Section: Selected Country + Tabs */}
                <div data-testid="country-config-workspace">
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
                    <div className="flex items-center gap-1">
                      <Globe className="h-5 w-5 text-primary" />
                      <h2 className="text-sm font-bold text-text">
                        {country.name} <span className="text-text-faint font-normal">({country.code})</span>
                      </h2>
                      <span className={`ml-2 inline-block px-1.5 py-0.5 rounded text-[9px] font-bold ${
                        country.is_active ? "bg-success/10 text-success" : "bg-text-faint/10 text-text-muted"
                      }`}>
                        {country.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                    <button
                      type="button"
                      className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-xs font-semibold text-text transition hover:bg-surface-2"
                      onClick={() => selectedCountryCode && hydrateCountryWorkspace(selectedCountryCode)}
                      disabled={loadingCountry}
                      data-testid="reload-country-workspace"
                    >
                      <RefreshCw className={`h-3.5 w-3.5 ${loadingCountry ? "animate-spin" : ""}`} />
                      Reload
                    </button>
                  </div>

                  <PanelTabs
                    items={visibleTabs}
                    value={activeTab}
                    onChange={(tab: string) => setActiveTab(tab as ConfigTab)}
                  />

                  {/* Tab 1: Overview */}
              {activeTab === "overview" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
                  <h3 className="text-sm font-bold text-text">Overview & Identity</h3>
                  <p className="text-xs text-text-muted">Configure the static identification details of this country (updates immediately on save).</p>
                  
                  <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                    <label className="space-y-1 text-xs text-text-muted">
                      Display Name
                      <input
                        className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                      />
                    </label>
                    <label className="space-y-1 text-xs text-text-muted">
                      Currency Symbol
                      <input
                        className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
                        value={currencySymbol}
                        onChange={(e) => setCurrencySymbol(e.target.value)}
                      />
                    </label>
                    <label className="space-y-1 text-xs text-text-muted">
                      Phone Code
                      <input
                        className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
                        value={phoneCode}
                        onChange={(e) => setPhoneCode(e.target.value)}
                      />
                    </label>
                    <label className="space-y-1 text-xs text-text-muted">
                      Language
                      <select
                        className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                      >
                        <option value="en">English (en)</option>
                        <option value="ar">Arabic (ar)</option>
                      </select>
                    </label>
                    <div className="flex items-end pb-2">
                      <label className="inline-flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
                        <input
                          type="checkbox"
                          checked={isActive}
                          onChange={(e) => setIsActive(e.target.checked)}
                        />
                        Active / Enabled
                      </label>
                    </div>
                  </div>

                  <div className="flex justify-end pt-2">
                    <Button variant="primary" type="button"
                      onClick={submitIdentity}
                      disabled={busyAction === "identity"}>
                      <Save className="h-3.5 w-3.5" />
                      {busyAction === "identity" ? "Updating..." : "Update Identity"}
                    </Button>
                  </div>
                </section>
              )}

              {/* Tab 2: Tax & VAT */}
              {activeTab === "tax" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1" data-testid="country-tax-panel">
                  <h3 className="text-sm font-bold text-text">Tax & VAT Configuration</h3>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <label className="space-y-1 text-xs text-text-muted">
                      Tax Type
                      <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={taxType} onChange={(event) => setTaxType(event.target.value)} />
                    </label>
                    <label className="space-y-1 text-xs text-text-muted">
                      Tax Rate (0 to 1)
                      <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={taxRate} onChange={(event) => setTaxRate(event.target.value)} />
                    </label>
                    <label className="space-y-1 text-xs text-text-muted">
                      Tax Name
                      <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={taxName} onChange={(event) => setTaxName(event.target.value)} />
                    </label>
                  </div>

                  <label className="inline-flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
                    <input type="checkbox" checked={taxInclusive} onChange={(event) => setTaxInclusive(event.target.checked)} />
                    Tax is inclusive in retail prices
                  </label>

                  <label className="block space-y-1 text-xs text-text-muted">
                    Tax Exempt Categories (comma-separated slugs)
                    <input
                      className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
                      value={taxExemptCategories}
                      onChange={(event) => setTaxExemptCategories(event.target.value)}
                      placeholder="books, medicine, exports"
                    />
                  </label>

                  {/* Reduced tax rates interactive editor */}
                  <div className="space-y-2">
                    <span className="block text-xs font-semibold text-text-muted">Reduced Tax Rates by Category</span>
                    <div className="grid gap-2 sm:grid-cols-3 items-end">
                      <label className="space-y-1 text-[11px] text-text-muted">
                        Category Slug
                        <input
                          className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
                          value={newReducedCategory}
                          onChange={(e) => setNewReducedCategory(e.target.value)}
                          placeholder="e.g. basic_foods"
                        />
                      </label>
                      <label className="space-y-1 text-[11px] text-text-muted">
                        Rate (0 to 1)
                        <input
                          className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
                          value={newReducedRate}
                          onChange={(e) => setNewReducedRate(e.target.value)}
                          placeholder="0.05"
                        />
                      </label>
                      <button
                        type="button"
                        onClick={() => {
                          const cat = newReducedCategory.trim().toLowerCase();
                          const r = newReducedRate.trim();
                          if (cat && r) {
                            setReducedTaxRates([...reducedTaxRates, { category: cat, rate: r }]);
                            setNewReducedCategory("");
                          }
                        }}
                        className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface px-3 text-xs font-semibold text-text hover:bg-surface-2"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Add Category Rate
                      </button>
                    </div>

                    <div className="overflow-x-auto rounded-lg border border-border mt-2 bg-surface">
                      <table className="w-full border-collapse text-left text-xs">
                        <thead className="bg-surface-2 text-text-muted">
                          <tr>
                            <th className="px-3 py-2 font-semibold">Category Slug</th>
                            <th className="px-3 py-2 font-semibold">Reduced Rate</th>
                            <th className="px-3 py-2 font-semibold w-16 text-center">Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {reducedTaxRates.map((item, idx) => (
                            <tr key={idx} className="border-t border-border">
                              <td className="px-3 py-2 text-text font-mono">{item.category}</td>
                              <td className="px-3 py-2 text-text font-medium">{(Number(item.rate) * 100).toFixed(1)}% ({item.rate})</td>
                              <td className="px-3 py-2 text-center">
                                <Button variant="danger" className="p-1 rounded transition" type="button"
                                  onClick={() => setReducedTaxRates(reducedTaxRates.filter((_, i) => i !== idx))}
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </Button>
                              </td>
                            </tr>
                          ))}
                          {reducedTaxRates.length === 0 && (
                            <tr>
                              <td colSpan={3} className="px-3 py-3 text-center text-text-faint italic">No reduced categories defined.</td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Simulator */}
                  <div className="grid gap-3 rounded-lg border border-border bg-surface p-3 md:grid-cols-4">
                    <label className="space-y-1 text-[11px] text-text-muted">
                      Preview Price Amount
                      <input
                        className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
                        value={previewAmount}
                        onChange={(event) => setPreviewAmount(event.target.value)}
                      />
                    </label>
                    <label className="space-y-1 text-[11px] text-text-muted">
                      Preview Category Slug
                      <input
                        className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
                        value={previewCategory}
                        onChange={(event) => setPreviewCategory(event.target.value)}
                        placeholder="e.g. food"
                      />
                    </label>
                    <label className="space-y-1 text-[11px] text-text-muted">
                      Pricing Mode
                      <select
                        className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-xs text-text"
                        value={previewInclusive}
                        onChange={(event) => setPreviewInclusive(event.target.value as "auto" | "inclusive" | "exclusive")}
                      >
                        <option value="auto">Auto (Default)</option>
                        <option value="inclusive">Inclusive</option>
                        <option value="exclusive">Exclusive</option>
                      </select>
                    </label>
                    <div className="flex items-end">
                      <button
                        type="button"
                        onClick={previewTax}
                        className="inline-flex h-9 w-full items-center justify-center gap-2 rounded-lg border border-border bg-surface px-3 text-xs font-semibold text-text transition hover:bg-surface-2"
                        disabled={!canSubmit || busyAction === "tax-preview"}
                        data-testid="preview-tax-button"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        {busyAction === "tax-preview" ? "Previewing..." : "Simulate VAT"}
                      </button>
                    </div>
                  </div>

                  {previewResult ? (
                    <div className="rounded-lg border border-border bg-surface p-3 text-xs text-text grid grid-cols-2 gap-2" data-testid="tax-preview-result">
                      <div><span className="font-semibold text-text-muted">Tax Applied:</span> {previewResult.tax_name}</div>
                      <div><span className="font-semibold text-text-muted">Rate Applied:</span> {(previewResult.tax_rate * 100).toFixed(1)}%</div>
                      <div><span className="font-semibold text-text-muted">Tax Amount:</span> {previewResult.tax_amount.toFixed(2)} {previewResult.currency}</div>
                      <div><span className="font-semibold text-text-muted">Net Price:</span> {previewResult.net_amount.toFixed(2)} {previewResult.currency}</div>
                      <div className="col-span-2 border-t border-border pt-1 font-bold text-primary">
                        Total Checkout Price: {previewResult.total_amount.toFixed(2)} {previewResult.currency}
                      </div>
                    </div>
                  ) : null}

                  <div className="flex justify-end pt-2">
                    <Button variant="primary" type="button"
                      onClick={submitTaxDraft}
                      disabled={!canSubmit || busyAction === "tax"}
                      data-testid="create-tax-draft-button">
                      <Save className="h-3.5 w-3.5" />
                      {busyAction === "tax" ? "Creating draft..." : "Save Tax Draft"}
                    </Button>
                  </div>
                </section>
              )}

              {/* Tab 3: Internal Logistics Model */}
              {activeTab === "logistics_model" && (
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
              )}

              {/* Tab 4: Delivery Partners (Logistics Providers) */}
              {activeTab === "logistics_providers" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
                  <h3 className="text-sm font-bold text-text">Delivery Partners & Logistics Integrations</h3>
                  <p className="text-xs text-text-muted">Manage active global delivery providers (e.g. Aramex, SMSA, J&T) with standard SLAs and custom tier-pricing rules.</p>

                  <div className="grid gap-2 grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 p-3 rounded-lg border border-border bg-surface">
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Provider ID
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderId} onChange={(e) => setNewProviderId(e.target.value)} placeholder="aramex" />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Provider Name
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderName} onChange={(e) => setNewProviderName(e.target.value)} placeholder="Aramex Express" />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Standard SLA (Days)
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderSlaStd} onChange={(e) => setNewProviderSlaStd(e.target.value)} placeholder="2-3" />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Express SLA (Days)
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderSlaExp} onChange={(e) => setNewProviderSlaExp(e.target.value)} placeholder="1" />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Base Rate
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderBaseRate} onChange={(e) => setNewProviderBaseRate(e.target.value)} />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Per KG Rate
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderPerKg} onChange={(e) => setNewProviderPerKg(e.target.value)} />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Currency Override
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderCurrency} onChange={(e) => setNewProviderCurrency(e.target.value)} placeholder="SAR" />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted sm:col-span-2">
                      Service Areas (comma-separated)
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newProviderServiceAreas} onChange={(e) => setNewProviderServiceAreas(e.target.value)} placeholder="riyadh, jeddah, dammam" />
                    </label>
                    <div className="flex items-end sm:col-span-4 lg:col-span-5 justify-end mt-2">
                      <button
                        type="button"
                        onClick={() => {
                          const pid = newProviderId.trim().toLowerCase();
                          const pname = newProviderName.trim();
                          if (!pid || !pname) return;
                          setProviders([
                            ...providers,
                            {
                              provider_id: pid,
                              name: pname,
                              enabled: true,
                              service_areas: newProviderServiceAreas.split(",").map((s) => s.trim()).filter(Boolean),
                              sla_standard_days: newProviderSlaStd.trim(),
                              sla_express_days: newProviderSlaExp.trim(),
                              base_rate: Number(newProviderBaseRate) || 0,
                              per_kg_rate: Number(newProviderPerKg) || 0,
                              currency: newProviderCurrency.trim() || null
                            }
                          ]);
                          setNewProviderId("");
                          setNewProviderName("");
                          setNewProviderServiceAreas("all_regions");
                        }}
                        className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface-2 px-4 text-xs font-semibold text-text hover:bg-surface-3 transition"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Add Integration Partner
                      </button>
                    </div>
                  </div>

                  <div className="grid gap-3 md:grid-cols-2 mt-2">
                    {providers.map((prov, index) => (
                      <div key={index} className="rounded-xl border border-border bg-surface p-3 space-y-2 relative shadow-sm hover:shadow transition">
                        <div className="flex items-center justify-between">
                          <div>
                            <span className="font-bold text-text block text-sm">{prov.name}</span>
                            <span className="text-[10px] font-mono text-text-faint uppercase">{prov.provider_id}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <label className="inline-flex items-center gap-1 text-[11px] font-semibold text-text-muted cursor-pointer">
                              <input
                                type="checkbox"
                                checked={prov.enabled}
                                onChange={(e) => {
                                  const updated = [...providers];
                                  updated[index].enabled = e.target.checked;
                                  setProviders(updated);
                                }}
                              />
                              Enabled
                            </label>
                            <Button variant="danger" className="p-1.5 rounded transition" type="button"
                              onClick={() => setProviders(providers.filter((_, i) => i !== index))}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-xs border-t border-border/60 pt-2">
                          <div><span className="text-text-muted font-semibold">Standard SLA:</span> {prov.sla_standard_days} days</div>
                          <div><span className="text-text-muted font-semibold">Express SLA:</span> {prov.sla_express_days} days</div>
                          <div><span className="text-text-muted font-semibold">Base Rate:</span> {prov.base_rate} {prov.currency || selectedCountry?.currency}</div>
                          <div><span className="text-text-muted font-semibold">Weight rate:</span> +{prov.per_kg_rate}/KG</div>
                          <div className="col-span-2 max-w-full truncate">
                            <span className="text-text-muted font-semibold">Service Coverage:</span> <span className="font-mono">{prov.service_areas.join(", ")}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                    {providers.length === 0 && (
                      <div className="col-span-2 text-center py-6 text-text-faint italic border rounded-xl bg-surface">No external delivery partners integrated yet.</div>
                    )}
                  </div>

                  <div className="flex justify-end pt-2">
                    <Button variant="primary" type="button"
                      onClick={submitLogisticsProvidersDraft}
                      disabled={!canSubmit || busyAction === "logistics_providers"}>
                      <Save className="h-3.5 w-3.5" />
                      {busyAction === "logistics_providers" ? "Creating draft..." : "Save Delivery Partners Draft"}
                    </Button>
                  </div>
                </section>
              )}

              {/* Tab 5: Payment Gateways */}
              {activeTab === "payment_gateways" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
                  <h3 className="text-sm font-bold text-text">Payment Gateways & Transaction Rules</h3>
                  <p className="text-xs text-text-muted">Dynamic payment options configured in the checkout pipeline. Note that credential variables must match backend environment naming.</p>

                  <div className="grid gap-2 grid-cols-2 md:grid-cols-3 lg:grid-cols-4 p-3 rounded-lg border border-border bg-surface">
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Gateway ID
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newGatewayId} onChange={(e) => setNewGatewayId(e.target.value)} placeholder="mada" />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Display Name
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newGatewayName} onChange={(e) => setNewGatewayName(e.target.value)} placeholder="Mada Credit/Debit" />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Integration Type
                      <select className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newGatewayType} onChange={(e) => setNewGatewayType(e.target.value)}>
                        <option value="card">Card Payment</option>
                        <option value="wallet">Digital Wallet</option>
                        <option value="cod">Cash on Delivery (COD)</option>
                        <option value="bank_transfer">Bank Transfer</option>
                        <option value="other">Other</option>
                      </select>
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Credential Env Reference Key
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newGatewayCredRef} onChange={(e) => setNewGatewayCredRef(e.target.value)} placeholder="MADA_API_KEY" />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Fee Percentage
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newGatewayFeePct} onChange={(e) => setNewGatewayFeePct(e.target.value)} />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Fee Fixed Amount
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newGatewayFeeFixed} onChange={(e) => setNewGatewayFeeFixed(e.target.value)} />
                    </label>
                    <div className="flex items-center gap-4 col-span-2 pt-2">
                      <label className="inline-flex items-center gap-1 text-[10px] font-semibold text-text cursor-pointer">
                        <input type="checkbox" checked={newGatewaySupportsCod} onChange={(e) => setNewGatewaySupportsCod(e.target.checked)} />
                        Supports Cash On Delivery (COD)
                      </label>
                      <label className="inline-flex items-center gap-1 text-[10px] font-semibold text-text cursor-pointer">
                        <input type="checkbox" checked={newGatewaySupportsInstall} onChange={(e) => setNewGatewaySupportsInstall(e.target.checked)} />
                        Supports Installments / BNPL
                      </label>
                    </div>
                    <div className="flex items-end justify-end col-span-2 md:col-span-3 lg:col-span-4 mt-2">
                      <button
                        type="button"
                        onClick={() => {
                          const gid = newGatewayId.trim().toLowerCase();
                          const gname = newGatewayName.trim();
                          if (!gid || !gname) return;
                          setGateways([
                            ...gateways,
                            {
                              gateway_id: gid,
                              name: gname,
                              type: newGatewayType,
                              enabled: true,
                              credential_ref: newGatewayCredRef.trim() || null,
                              supports_cod: newGatewaySupportsCod,
                              supports_installments: newGatewaySupportsInstall,
                              fee_percentage: Number(newGatewayFeePct) || 0,
                              fee_fixed: Number(newGatewayFeeFixed) || 0
                            }
                          ]);
                          setNewGatewayId("");
                          setNewGatewayName("");
                          setNewGatewayCredRef("");
                          setNewGatewaySupportsCod(false);
                          setNewGatewaySupportsInstall(false);
                        }}
                        className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface-2 px-4 text-xs font-semibold text-text hover:bg-surface-3 transition"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Add Gateway Option
                      </button>
                    </div>
                  </div>

                  <div className="grid gap-3 md:grid-cols-2 mt-2">
                    {gateways.map((gw, index) => (
                      <div key={index} className="rounded-xl border border-border bg-surface p-3 space-y-2 relative shadow-sm hover:shadow transition">
                        <div className="flex items-center justify-between">
                          <div>
                            <span className="font-bold text-text block text-sm">{gw.name}</span>
                            <span className="text-[10px] font-mono text-text-faint uppercase">{gw.gateway_id} | {gw.type}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <label className="inline-flex items-center gap-1 text-[11px] font-semibold text-text-muted cursor-pointer">
                              <input
                                type="checkbox"
                                checked={gw.enabled}
                                onChange={(e) => {
                                  const updated = [...gateways];
                                  updated[index].enabled = e.target.checked;
                                  setGateways(updated);
                                }}
                              />
                              Active
                            </label>
                            <Button variant="danger" className="p-1.5 rounded transition" type="button"
                              onClick={() => setGateways(gateways.filter((_, i) => i !== index))}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-xs border-t border-border/60 pt-2">
                          <div><span className="text-text-muted font-semibold">Cred Variable:</span> <span className="font-mono text-[10px] bg-surface-2 px-1 rounded">{gw.credential_ref || "None Required"}</span></div>
                          <div><span className="text-text-muted font-semibold">Tx Cost:</span> {gw.fee_percentage}% + {gw.fee_fixed}</div>
                          <div><span className="text-text-muted font-semibold">Allow COD:</span> {gw.supports_cod ? "Yes" : "No"}</div>
                          <div><span className="text-text-muted font-semibold">Allow Installment:</span> {gw.supports_installments ? "Yes" : "No"}</div>
                        </div>
                      </div>
                    ))}
                    {gateways.length === 0 && (
                      <div className="col-span-2 text-center py-6 text-text-faint italic border rounded-xl bg-surface">No gateways configured. Customers will only be able to use standard Cash on Delivery if active.</div>
                    )}
                  </div>

                  <div className="flex justify-end pt-2">
                    <Button variant="primary" type="button"
                      onClick={submitPaymentGatewaysDraft}
                      disabled={!canSubmit || busyAction === "payment_gateways"}>
                      <Save className="h-3.5 w-3.5" />
                      {busyAction === "payment_gateways" ? "Creating draft..." : "Save Payment Gateways Draft"}
                    </Button>
                  </div>
                </section>
              )}

              {/* Tab 6: Legal & Safety Rules */}
              {activeTab === "legal_rules" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
                  <h3 className="text-sm font-bold text-text">Legal Constraints & Return Operations</h3>
                  <p className="text-xs text-text-muted">General regulatory and legal requirements including minimum consumer age, refund timelines, and commercial registration rules.</p>

                  <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4">
                    <label className="space-y-1 text-xs text-text-muted">
                      Minimum Order Age
                      <input type="number" className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={minimumOrderAge} onChange={(e) => setMinimumOrderAge(Number(e.target.value))} />
                    </label>
                    <label className="space-y-1 text-xs text-text-muted">
                      Max Returns Allowed per Order
                      <input type="number" className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={maxReturnsAllowed} onChange={(e) => setMaxReturnsAllowed(Number(e.target.value))} />
                    </label>
                    <label className="space-y-1 text-xs text-text-muted">
                      Return Window (Days)
                      <input type="number" className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={returnWindowDays} onChange={(e) => setReturnWindowDays(Number(e.target.value))} />
                    </label>
                    <label className="space-y-1 text-xs text-text-muted">
                      Refund SLA (Processing Days)
                      <input type="number" className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={refundProcessingDays} onChange={(e) => setRefundProcessingDays(Number(e.target.value))} />
                    </label>
                  </div>

                  <div className="flex flex-wrap gap-4 pt-2">
                    <label className="inline-flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
                      <input type="checkbox" checked={requiresCommercialLicense} onChange={(e) => setRequiresCommercialLicense(e.target.checked)} />
                      Requires valid Commercial Registration (CR) from Suppliers
                    </label>
                    <label className="inline-flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
                      <input type="checkbox" checked={requiresVatRegistration} onChange={(e) => setRequiresVatRegistration(e.target.checked)} />
                      Requires explicit VAT Certificate from Suppliers
                    </label>
                  </div>

                  <label className="block space-y-1 text-xs text-text-muted">
                    Restricted Products & Categories (comma-separated slugs to block import / sale)
                    <input
                      className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
                      value={productRestrictions}
                      onChange={(e) => setProductRestrictions(e.target.value)}
                      placeholder="e.g. alcohol, tobacco, pork_products"
                    />
                  </label>

                  <div className="flex justify-end pt-2">
                    <Button variant="primary" type="button"
                      onClick={submitLegalRulesDraft}
                      disabled={!canSubmit || busyAction === "legal_rules"}>
                      <Save className="h-3.5 w-3.5" />
                      {busyAction === "legal_rules" ? "Creating draft..." : "Save Legal Rules Draft"}
                    </Button>
                  </div>
                </section>
              )}

              {/* Tab 7: Regions & Cities */}
              {activeTab === "regions" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
                  <h3 className="text-sm font-bold text-text">Regions & Cities Coverage</h3>
                  <p className="text-xs text-text-muted">Set up regional hubs and map specific cities inside this country's delivery footprint.</p>

                  <div className="grid gap-2 sm:grid-cols-3 items-end p-3 rounded-lg border border-border bg-surface">
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Region / Governorate Name
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newRegionName} onChange={(e) => setNewRegionName(e.target.value)} placeholder="e.g. Riyadh Province" />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Cities (comma-separated list)
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newRegionCities} onChange={(e) => setNewRegionCities(e.target.value)} placeholder="Riyadh, Diriyah, Kharj" />
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        const rname = newRegionName.trim();
                        if (!rname) return;
                        const rid = rname.toLowerCase().replace(/\s+/g, "_");
                        const citiesArr = newRegionCities.split(",").map((c) => c.trim()).filter(Boolean);
                        setRegions([
                          ...regions,
                          {
                            region_id: rid,
                            name: rname,
                            cities: citiesArr
                          }
                        ]);
                        setNewRegionName("");
                        setNewRegionCities("");
                      }}
                      className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface-2 px-3 text-xs font-semibold text-text hover:bg-surface-3 transition"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      Add Region Hub
                    </button>
                  </div>

                  <div className="space-y-2 mt-2">
                    {regions.map((reg, index) => {
                      const isExpanded = expandedRegions[reg.region_id] ?? true;
                      return (
                        <div key={index} className="rounded-lg border border-border bg-surface overflow-hidden">
                          <div className="flex items-center justify-between px-3 py-2 bg-surface-2">
                            <button
                              type="button"
                              onClick={() => setExpandedRegions({ ...expandedRegions, [reg.region_id]: !isExpanded })}
                              className="flex items-center gap-2 text-xs font-bold text-text text-left"
                            >
                              {isExpanded ? <ChevronDown className="h-4 w-4 shrink-0 text-text-muted" /> : <ChevronRight className="h-4 w-4 shrink-0 text-text-muted" />}
                              <span>{reg.name}</span>
                              <span className="text-[10px] text-text-faint font-mono font-normal">({reg.region_id})</span>
                              <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded font-normal">{reg.cities.length} cities</span>
                            </button>
                            <Button variant="danger" className="p-1 rounded transition" type="button"
                              onClick={() => setRegions(regions.filter((_, i) => i !== index))}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>

                          {isExpanded && (
                            <div className="p-3 text-xs border-t border-border/60">
                              <div className="flex flex-wrap gap-1">
                                {reg.cities.map((city, cidx) => (
                                  <span key={cidx} className="inline-flex items-center gap-1 bg-surface-2 px-2 py-1 rounded border border-border font-mono text-[10px] text-text">
                                    {city}
                                    <button
                                      type="button"
                                      onClick={() => {
                                        const updated = [...regions];
                                        updated[index].cities = reg.cities.filter((_, i) => i !== cidx);
                                        setRegions(updated);
                                      }}
                                      className="text-text-faint hover:text-danger transition"
                                    >
                                      &times;
                                    </button>
                                  </span>
                                ))}
                                <span className="inline-flex gap-1 items-center">
                                  <input
                                    type="text"
                                    placeholder="Add city..."
                                    onKeyDown={(e) => {
                                      if (e.key === "Enter") {
                                        const val = e.currentTarget.value.trim();
                                        if (val && !reg.cities.includes(val)) {
                                          const updated = [...regions];
                                          updated[index].cities = [...reg.cities, val];
                                          setRegions(updated);
                                          e.currentTarget.value = "";
                                        }
                                      }
                                    }}
                                    className="border rounded bg-surface px-1.5 py-0.5 text-[10px] text-text w-24 outline-none"
                                  />
                                </span>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                    {regions.length === 0 && (
                      <div className="text-center py-6 text-text-faint italic border rounded-lg bg-surface">No regions or hubs mapped. Add a region to setup regional logistics rules.</div>
                    )}
                  </div>

                  <div className="flex justify-end pt-2">
                    <Button variant="primary" type="button"
                      onClick={submitRegionsDraft}
                      disabled={!canSubmit || busyAction === "regions"}>
                      <Save className="h-3.5 w-3.5" />
                      {busyAction === "regions" ? "Creating draft..." : "Save Regions Draft"}
                    </Button>
                  </div>
                </section>
              )}

              {/* Tab 8: Interactive Map */}
              {activeTab === "map" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
                  <h3 className="text-sm font-bold text-text">Interactive Country Map</h3>
                  <p className="text-xs text-text-muted">Visual management of cities and key locations. Click on the map to add new cities or select existing ones to edit.</p>
                  
                  <CountryMapView
                    countryCode={selectedCountryCode}
                    cities={cities}
                    onCitiesChange={setCities}
                  />
                  
                  <div className="flex justify-end pt-2">
                    <Button variant="primary" className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition hover:opacity-90 disabled:opacity-60 shadow" type="button"
                      onClick={async () => {
                      if (!selectedCountryCode) return;
                      setBusyAction("map");
                      try {
                        const response = await apiFetch(`/admin/countries/${selectedCountryCode}/cities`, {
                          method: "PUT",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ cities }),
                        });
                        const data = await parseJsonResponse(response);
                        if (!response.ok) {
                          throw new Error(toErrorMessage(response.status, data, "Failed to save cities"));
                        }
                        addToast("Cities map saved", "success");
                        setActivityMessage("Interactive map updated successfully.");
                      } catch (error) {
                        addToast(error instanceof Error ? error.message : "Failed to save cities", "error");
                      } finally {
                        setBusyAction(null);
                      }
                    }}
                      disabled={busyAction === "map"}
                      data-testid="save-cities-map-button"
                    >
                      <Save className="h-3.5 w-3.5" />
                      {busyAction === "map" ? "Saving..." : "Save Map"}
                    </Button>
                  </div>
                </section>
              )}

              {/* Tab 9: Supplier KYC Requirements */}
              {activeTab === "kyc" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
                  <h3 className="text-sm font-bold text-text">Supplier Onboarding & Compliance</h3>
                  <p className="text-xs text-text-muted">Define the level of validation and documentary evidence required from suppliers requesting to sell in this country.</p>

                  <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                    <label className="space-y-1 text-xs text-text-muted">
                      KYC Clearance Level
                      <select className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={kycLevel} onChange={(e) => setKycLevel(e.target.value)}>
                        <option value="basic">Basic (Self-verification)</option>
                        <option value="standard">Standard (Business ID & Bank verification)</option>
                        <option value="enhanced">Enhanced (Fully-audited KYC and corporate verification)</option>
                      </select>
                    </label>
                    <div className="flex items-end pb-2">
                      <label className="inline-flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
                        <input type="checkbox" checked={approvalRequired} onChange={(e) => setApprovalRequired(e.target.checked)} />
                        Require manual ops approval before listing products
                      </label>
                    </div>
                  </div>

                  <div className="space-y-2 border-t border-border pt-4">
                    <span className="block text-xs font-bold text-text-muted">Required Documents Checklist</span>
                    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                      {[
                        { id: "commercial_license", label: "Commercial Registration (CR)" },
                        { id: "vat_certificate", label: "VAT Certificate" },
                        { id: "owner_id", label: "Authorized Signatory ID" },
                        { id: "bank_statement", label: "Bank Account Ownership (IBAN)" },
                        { id: "brand_auth", label: "Brand Authorization / Dealer Certificate" },
                        { id: "import_permit", label: "Import Permit / Customs Registration" },
                        { id: "saudi_fda", label: "SFDA / Local FDA License Certificate" }
                      ].map((doc) => {
                        const isChecked = requiredDocuments.includes(doc.id);
                        return (
                          <label key={doc.id} className="flex items-center gap-2 border border-border/80 bg-surface rounded-lg p-2.5 text-xs text-text cursor-pointer hover:bg-surface-2 transition select-none">
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setRequiredDocuments([...requiredDocuments, doc.id]);
                                } else {
                                  setRequiredDocuments(requiredDocuments.filter((d) => d !== doc.id));
                                }
                              }}
                            />
                            <span>{doc.label}</span>
                          </label>
                        );
                      })}
                    </div>
                  </div>

                  <div className="flex justify-end pt-2">
                    <Button variant="primary" type="button"
                      onClick={submitSupplierRequirementsDraft}
                      disabled={!canSubmit || busyAction === "supplier_requirements"}>
                      <Save className="h-3.5 w-3.5" />
                      {busyAction === "supplier_requirements" ? "Creating draft..." : "Save Supplier Rules Draft"}
                    </Button>
                  </div>
                </section>
              )}

              {/* Tab 9: Payout Settings */}
              {activeTab === "payout_settings" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
                  <h3 className="text-sm font-bold text-text">Supplier Settlement & Payout Rules</h3>
                  <p className="text-xs text-text-muted">Manage standard payment intervals and transaction batch sizes for suppliers in this country.</p>

                  <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-5">
                    <label className="space-y-1 text-xs text-text-muted">
                      Minimum Payout Amount
                      <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={minimumPayoutAmount} onChange={(e) => setMinimumPayoutAmount(e.target.value)} />
                    </label>
                    <label className="space-y-1 text-xs text-text-muted">
                      Settlement Cycle
                      <select className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={payoutSchedule} onChange={(e) => setPayoutSchedule(e.target.value)}>
                        <option value="daily">Daily Settlements</option>
                        <option value="weekly">Weekly Cycle</option>
                        <option value="biweekly">Bi-weekly (Fortnightly)</option>
                        <option value="monthly">Monthly Settlements</option>
                      </select>
                    </label>
                    <label className="space-y-1 text-xs text-text-muted">
                      Weekly Payout Day
                      <select className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={payoutDay} onChange={(e) => setPayoutDay(e.target.value)}>
                        <option value="sunday">Sunday</option>
                        <option value="monday">Monday</option>
                        <option value="tuesday">Tuesday</option>
                        <option value="wednesday">Wednesday</option>
                        <option value="thursday">Thursday</option>
                      </select>
                    </label>
                    <label className="space-y-1 text-xs text-text-muted">
                      Settlement Batch Size
                      <input type="number" className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={batchSize} onChange={(e) => setBatchSize(e.target.value)} />
                    </label>
                    <label className="space-y-1 text-xs text-text-muted">
                      Payout Currency Override
                      <input className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text" value={payoutCurrency} onChange={(e) => setPayoutCurrency(e.target.value)} placeholder="SAR" />
                    </label>
                  </div>

                  <div className="flex justify-end pt-2">
                    <Button variant="primary" type="button"
                      onClick={submitPayoutSettingsDraft}
                      disabled={!canSubmit || busyAction === "payout_settings"}>
                      <Save className="h-3.5 w-3.5" />
                      {busyAction === "payout_settings" ? "Creating draft..." : "Save Payout Settings Draft"}
                    </Button>
                  </div>

                  {/* ── Category Payout Rules ── */}
                  <div className="pt-4 border-t border-border/60">
                    <h4 className="text-xs font-bold text-text mb-2">Category-Level Payout Overrides</h4>
                    <p className="text-[10px] text-text-muted mb-3">
                      Override the country-level payout rate for specific product categories.
                      Higher priority than the default payout rate but lower than per-product rules.
                    </p>

                    <div className="flex items-center gap-2 mb-3">
                      <select
                        className="rounded border border-border bg-surface px-2 py-1.5 text-xs text-text max-w-[200px] flex-1"
                        value={newCatPayoutSlug}
                        onChange={(e) => setNewCatPayoutSlug(e.target.value)}
                      >
                        <option value="">Select category...</option>
                        {allCategories
                          .filter((c) => !catPayoutRules.some((r) => r.category_slug === c.slug))
                          .map((c) => (
                            <option key={c.slug} value={c.slug}>{c.name}</option>
                          ))}
                      </select>
                      <label className="text-[10px] text-text-muted flex items-center gap-1">
                        Rate:
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          max="1"
                          className="w-16 rounded border border-border bg-surface px-1.5 py-1.5 text-xs text-text"
                          value={newCatPayoutRate}
                          onChange={(e) => setNewCatPayoutRate(e.target.value)}
                        />
                      </label>
                      <Button variant="primary" className="rounded text-primary px-2.5 py-1.5 text-[10px] font-semibold transition" type="button"
                        disabled={!newCatPayoutSlug || !newCatPayoutRate}
                        onClick={async () => {
                          const slug = newCatPayoutSlug;
                          const rate = Number(newCatPayoutRate);
                          if (!slug || Number.isNaN(rate)) return;
                          try {
                            const res = await apiFetch(`/admin/countries/${selectedCountryCode}/payout-rules/categories`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ category_slug: slug, payout_rate: rate, is_active: true }),
                            });
                            const data = await parseJsonResponse(res);
                            if (!res.ok) throw new Error(data?.detail || "Failed to create rule");
                            addToast("Category payout rule created", "success");
                            setNewCatPayoutSlug("");
                            setNewCatPayoutRate("0.80");
                            loadPayoutRules(selectedCountryCode);
                          } catch (err: any) {
                            addToast(err.message, "error");
                          }
                        }}
                      >
                        Add Rule
                      </Button>
                    </div>

                    {catPayoutRules.length > 0 && (
                      <div className="space-y-1">
                        {catPayoutRules.map((rule) => (
                          <div key={rule.id} className="flex items-center justify-between rounded border border-border/50 bg-surface px-3 py-2 text-xs">
                            <span className="font-medium text-text">{rule.category_slug}</span>
                            <div className="flex items-center gap-3">
                              <span className="text-text-muted">Rate: <strong className="text-text">{(rule.payout_rate * 100).toFixed(1)}%</strong></span>
                              <button
                                type="button"
                                onClick={async () => {
                                  try {
                                    const res = await apiFetch(`/admin/countries/${selectedCountryCode}/payout-rules/categories/${rule.id}`, { method: "DELETE" });
                                    if (!res.ok) throw new Error("Failed to delete");
                                    addToast("Rule deleted", "success");
                                    loadPayoutRules(selectedCountryCode);
                                  } catch (err: any) {
                                    addToast(err.message, "error");
                                  }
                                }}
                                className="text-danger hover:text-danger/80 transition"
                              >
                                <Trash2 className="h-3 w-3" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    {catPayoutRules.length === 0 && (
                      <p className="text-[10px] text-text-muted italic">No category-level payout overrides configured.</p>
                    )}
                  </div>

                  {/* ── Product Payout Rules ── */}
                  <div className="pt-4 border-t border-border/60">
                    <h4 className="text-xs font-bold text-text mb-2">Product-Level Payout Overrides</h4>
                    <p className="text-[10px] text-text-muted mb-3">
                      Override the payout rate for individual products.
                      These take the highest precedence in the payout resolution chain.
                    </p>

                    <div className="flex items-center gap-2 mb-3">
                      <input
                        type="number"
                        className="rounded border border-border bg-surface px-2 py-1.5 text-xs text-text w-28"
                        placeholder="Product ID"
                        value={newProdPayoutId}
                        onChange={(e) => setNewProdPayoutId(e.target.value)}
                      />
                      <label className="text-[10px] text-text-muted flex items-center gap-1">
                        Rate:
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          max="1"
                          className="w-16 rounded border border-border bg-surface px-1.5 py-1.5 text-xs text-text"
                          value={newProdPayoutRate}
                          onChange={(e) => setNewProdPayoutRate(e.target.value)}
                        />
                      </label>
                      <Button variant="primary" className="rounded text-primary px-2.5 py-1.5 text-[10px] font-semibold transition" type="button"
                        disabled={!newProdPayoutId || !newProdPayoutRate}
                        onClick={async () => {
                          const pid = Number(newProdPayoutId);
                          const rate = Number(newProdPayoutRate);
                          if (!pid || Number.isNaN(rate)) return;
                          try {
                            const res = await apiFetch(`/admin/countries/${selectedCountryCode}/payout-rules/products`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ product_id: pid, payout_rate: rate, is_active: true }),
                            });
                            const data = await parseJsonResponse(res);
                            if (!res.ok) throw new Error(data?.detail || "Failed to create rule");
                            addToast("Product payout rule created", "success");
                            setNewProdPayoutId("");
                            setNewProdPayoutRate("0.85");
                            loadPayoutRules(selectedCountryCode);
                          } catch (err: any) {
                            addToast(err.message, "error");
                          }
                        }}
                      >
                        Add Rule
                      </Button>
                    </div>

                    {prodPayoutRules.length > 0 && (
                      <div className="space-y-1">
                        {prodPayoutRules.map((rule) => (
                          <div key={rule.id} className="flex items-center justify-between rounded border border-border/50 bg-surface px-3 py-2 text-xs">
                            <span className="font-medium text-text">Product #{rule.product_id}</span>
                            <div className="flex items-center gap-3">
                              <span className="text-text-muted">Rate: <strong className="text-text">{(rule.payout_rate * 100).toFixed(1)}%</strong></span>
                              <button
                                type="button"
                                onClick={async () => {
                                  try {
                                    const res = await apiFetch(`/admin/countries/${selectedCountryCode}/payout-rules/products/${rule.id}`, { method: "DELETE" });
                                    if (!res.ok) throw new Error("Failed to delete");
                                    addToast("Rule deleted", "success");
                                    loadPayoutRules(selectedCountryCode);
                                  } catch (err: any) {
                                    addToast(err.message, "error");
                                  }
                                }}
                                className="text-danger hover:text-danger/80 transition"
                              >
                                <Trash2 className="h-3 w-3" />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    {prodPayoutRules.length === 0 && (
                      <p className="text-[10px] text-text-muted italic">No product-level payout overrides configured.</p>
                    )}
                  </div>
                </section>
              )}

              {/* Tab 10: Value Commissions (Tiers) */}
              {activeTab === "commission_tiers" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
                  <h3 className="text-sm font-bold text-text">Value-Based Commission Tiers</h3>
                  <p className="text-xs text-text-muted">Configure order value thresholds where commission rates change based on target sales volume (overrides base category rates).</p>

                  <div className="grid gap-2 grid-cols-2 md:grid-cols-5 items-end p-3 rounded-lg border border-border bg-surface">
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Min Order Value ({selectedCountry?.currency})
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newTierMin} onChange={(e) => setNewTierMin(e.target.value)} />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Max Order Value (Leave empty for &infin;)
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newTierMax} onChange={(e) => setNewTierMax(e.target.value)} placeholder="Unlimited" />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Commission Percentage
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newTierPct} onChange={(e) => setNewTierPct(e.target.value)} />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Fixed Transaction Fee
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newTierFixed} onChange={(e) => setNewTierFixed(e.target.value)} />
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        const min = Number(newTierMin);
                        const max = newTierMax.trim() ? Number(newTierMax) : null;
                        const pct = Number(newTierPct);
                        const fixed = Number(newTierFixed);
                        if (Number.isNaN(min) || Number.isNaN(pct)) return;
                        setCommissionTiers([
                          ...commissionTiers,
                          {
                            min_order_value: min,
                            max_order_value: max,
                            commission_percentage: pct,
                            fixed_fee: fixed
                          }
                        ]);
                        setNewTierMin("0");
                        setNewTierMax("");
                      }}
                      className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface-2 px-3 text-xs font-semibold text-text hover:bg-surface-3 transition"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      Add Value Tier
                    </button>
                  </div>

                  <div className="overflow-x-auto rounded-lg border border-border bg-surface mt-2">
                    <table className="w-full border-collapse text-left text-xs">
                      <thead className="bg-surface-2 text-text-muted">
                        <tr>
                          <th className="px-3 py-2 font-semibold">Order Volume Range</th>
                          <th className="px-3 py-2 font-semibold">Commission Rate</th>
                          <th className="px-3 py-2 font-semibold">Fixed Fee Override</th>
                          <th className="px-3 py-2 font-semibold w-16 text-center">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {commissionTiers.map((tier, idx) => (
                          <tr key={idx} className="border-t border-border">
                            <td className="px-3 py-2 text-text font-medium">
                              {tier.min_order_value.toFixed(2)} {selectedCountry?.currency} &ndash;{" "}
                              {tier.max_order_value != null ? `${tier.max_order_value.toFixed(2)} ${selectedCountry?.currency}` : "Unlimited"}
                            </td>
                            <td className="px-3 py-2 text-text font-bold text-primary">{tier.commission_percentage}%</td>
                            <td className="px-3 py-2 text-text">{tier.fixed_fee.toFixed(2)} {selectedCountry?.currency}</td>
                            <td className="px-3 py-2 text-center">
                              <Button variant="danger" className="p-1 rounded transition" type="button"
                                onClick={() => setCommissionTiers(commissionTiers.filter((_, i) => i !== idx))}
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                        {commissionTiers.length === 0 && (
                          <tr>
                            <td colSpan={4} className="px-3 py-3 text-center text-text-faint italic">No value-based commission tiers created. Category commission rates will apply uniformly.</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>

                  <div className="flex justify-end pt-2">
                    <Button variant="primary" type="button"
                      onClick={submitCommissionTiersDraft}
                      disabled={!canSubmit || busyAction === "commission_tiers"}>
                      <Save className="h-3.5 w-3.5" />
                      {busyAction === "commission_tiers" ? "Creating draft..." : "Save Commission Tiers Draft"}
                    </Button>
                  </div>
                </section>
              )}

              {/* Tab 11: Category Commissions */}
              {activeTab === "category_commissions" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1" data-testid="country-commission-panel">
                  <h3 className="text-sm font-bold text-text">Category Specific Commissions</h3>
                  <p className="text-xs text-text-muted">Override base commission rates for specific category slugs (e.g. smartphones, fashion, home_appliances).</p>

                  <div className="grid gap-2 grid-cols-2 md:grid-cols-4 items-end p-3 rounded-lg border border-border bg-surface">
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Category
                      <select
                        className="w-full rounded border bg-surface px-2 py-1 text-xs text-text"
                        value={newCategorySlug}
                        onChange={(e) => setNewCategorySlug(e.target.value)}
                      >
                        <option value="">-- Select category --</option>
                        {allCategories.map((cat) => (
                          <option key={cat.id} value={cat.slug}>{cat.name} ({cat.slug})</option>
                        ))}
                      </select>
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted">
                      Commission Rate (0 to 1)
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newCategoryRate} onChange={(e) => setNewCategoryRate(e.target.value)} />
                    </label>
                    <label className="space-y-1 text-[10px] text-text-muted md:col-span-2">
                      Internal Notes
                      <input className="w-full rounded border bg-surface px-2 py-1 text-xs text-text" value={newCategoryNotes} onChange={(e) => setNewCategoryNotes(e.target.value)} placeholder="Low margin category" />
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        const slug = newCategorySlug.trim().toLowerCase();
                        const rate = Number(newCategoryRate);
                        if (!slug || Number.isNaN(rate)) return;
                        setCategoryCommissions([
                          ...categoryCommissions,
                          {
                            category_slug: slug,
                            commission_rate: rate,
                            notes: newCategoryNotes.trim() || null,
                            is_active: true
                          }
                        ]);
                        setNewCategorySlug("");
                        setNewCategoryNotes("");
                      }}
                      className="inline-flex h-9 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface-2 px-3 text-xs font-semibold text-text hover:bg-surface-3 transition"
                    >
                      <Plus className="h-3.5 w-3.5" />
                      Add Category Rule
                    </button>
                  </div>

                  {/* Coverage Summary + Bulk Set */}
                  {allCategories.length > 0 && (
                    <div className="flex flex-wrap items-center gap-3 text-xs text-text-muted p-3 rounded-lg border border-border/60 bg-surface">
                      <span>Total: <strong className="text-text">{allCategories.length}</strong></span>
                      <span>Override: <strong className="text-text">{categoryCommissions.length}</strong></span>
                      <span>Missing: <strong className="text-text">{allCategories.length - categoryCommissions.length}</strong></span>
                      <span className="text-text-faint">
                        Coverage: <strong className={categoryCommissions.length >= allCategories.length ? "text-success" : "text-warning"}>
                          {allCategories.length > 0 ? ((categoryCommissions.length / allCategories.length) * 100).toFixed(0) : 0}%
                        </strong>
                      </span>
                      <span className="ml-auto flex items-center gap-2">
                        <span className="text-text-faint text-[10px]">Bulk fill missing:</span>
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          max="1"
                          value={bulkFillRate}
                          onChange={(e) => setBulkFillRate(e.target.value)}
                          className="w-16 rounded border border-border bg-surface px-1.5 py-1 text-xs text-text"
                          placeholder="0.10"
                        />
                        <button
                          type="button"
                          onClick={() => {
                            const rate = Number(bulkFillRate);
                            if (Number.isNaN(rate) || rate < 0 || rate > 1) return;
                            const existingSlugs = new Set(categoryCommissions.map((c) => c.category_slug));
                            const newRates = allCategories
                              .filter((cat) => !existingSlugs.has(cat.slug))
                              .map((cat) => ({
                                category_slug: cat.slug,
                                commission_rate: rate,
                                notes: "Bulk default",
                                is_active: true,
                              }));
                            setCategoryCommissions([...categoryCommissions, ...newRates]);
                          }}
                          className="rounded bg-primary/10 text-primary px-2 py-1 text-[10px] font-semibold hover:bg-primary/20 transition"
                        >
                          Apply
                        </button>
                      </span>
                    </div>
                  )}

                  <div className="overflow-x-auto rounded-lg border border-border bg-surface mt-2">
                    <table className="w-full border-collapse text-left text-xs">
                      <thead className="bg-surface-2 text-text-muted">
                        <tr>
                          <th className="px-3 py-2 font-semibold">Category</th>
                          <th className="px-3 py-2 font-semibold">Commission Rate</th>
                          <th className="px-3 py-2 font-semibold">Internal Notes</th>
                          <th className="px-3 py-2 font-semibold w-16 text-center">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {categoryCommissions.map((row, idx) => {
                          const cat = allCategories.find((c) => c.slug === row.category_slug);
                          return (
                          <tr key={idx} className="border-t border-border">
                            <td className="px-3 py-2 text-text font-bold">{cat ? `${cat.name} ` : ""}<span className="font-mono text-text-muted">{row.category_slug}</span></td>
                            <td className="px-3 py-2 text-text font-bold text-primary">{(row.commission_rate * 100).toFixed(1)}%</td>
                            <td className="px-3 py-2 text-text-muted italic">{row.notes || "-"}</td>
                            <td className="px-3 py-2 text-center">
                              <Button variant="danger" className="p-1 rounded transition" type="button"
                                onClick={() => setCategoryCommissions(categoryCommissions.filter((_, i) => i !== idx))}
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
                            </td>
                          </tr>
                        );
                      })}
                      {categoryCommissions.length === 0 && (
                        <tr>
                          <td colSpan={4} className="px-3 py-3 text-center text-text-faint italic">No custom category rates defined. Default store commission applies.</td>
                        </tr>
                      )}
                      </tbody>
                    </table>
                  </div>

                  <div className="flex justify-end pt-2">
                    <Button variant="primary" type="button"
                      onClick={submitCategoryCommissionsDraft}
                      disabled={!canSubmit || busyAction === "category_commissions"}>
                      <Save className="h-3.5 w-3.5" />
                      {busyAction === "category_commissions" ? "Creating draft..." : "Save Category Commissions Draft"}
                    </Button>
                  </div>
                </section>
              )}

              {/* Tab 12: Feature Flags */}
              {activeTab === "feature_flags" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
                  <h3 className="text-sm font-bold text-text">Feature Flags & Platform Toggles</h3>
                  <p className="text-xs text-text-muted">Enable or disable platform features per country (e.g., BNPL, AI Chatbot, COD).</p>

                  <div className="space-y-3">
                    {featureFlags.length === 0 ? (
                      <p className="text-sm text-text-muted italic">No feature flags configured. Using default platform settings.</p>
                    ) : (
                      featureFlags.map((ff, idx) => (
                        <div key={idx} className="flex items-center justify-between rounded-lg border border-border bg-surface p-3">
                          <div>
                            <span className="font-medium text-text">{ff.feature_key}</span>
                            {ff.config && Object.keys(ff.config).length > 0 && (
                              <div className="text-[10px] text-text-faint mt-1">
                                Config: <span className="font-mono">{JSON.stringify(ff.config)}</span>
                              </div>
                            )}
                          </div>
                          <label className="inline-flex items-center gap-2 text-xs font-semibold cursor-pointer">
                            <input
                              type="checkbox"
                              checked={ff.enabled}
                              onChange={async (e) => {
                                const updated = [...featureFlags];
                                updated[idx].enabled = e.target.checked;
                                setFeatureFlags(updated);
                                // Auto-save on toggle
                                try {
                                  await apiFetch(`/admin/countries/${selectedCountryCode}/feature-flags/${ff.feature_key}`, {
                                    method: "PATCH",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ enabled: e.target.checked }),
                                  });
                                  addToast(`Feature flag updated`, "success");
                                } catch {
                                  addToast("Failed to save feature flag", "error");
                                }
                              }}
                            />
                            Enabled
                          </label>
                        </div>
                      ))
                    )}
                  </div>

                  <div className="border-t border-border pt-4">
                    <h4 className="text-xs font-bold text-text mb-2">Add New Feature Flag</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 items-end">
                      <label className="space-y-1 text-[10px] text-text-muted">
                        Feature Key
                        <input
                          type="text"
                          className="w-full rounded border border-border bg-surface px-2 py-1 text-xs text-text"
                          value={newFeatureKey}
                          onChange={(e) => setNewFeatureKey(e.target.value)}
                          placeholder="ai_chatbot"
                        />
                      </label>
                      <div className="flex items-end pb-2">
                        <label className="inline-flex items-center gap-1 text-xs font-semibold text-text cursor-pointer">
                          <input type="checkbox" checked={newFeatureEnabled} onChange={(e) => setNewFeatureEnabled(e.target.checked)} />
                          Enabled
                        </label>
                      </div>
                      <button
                        type="button"
                        disabled={!newFeatureKey}
                        onClick={async () => {
                          try {
                            const res = await apiFetch(`/admin/countries/${selectedCountryCode}/feature-flags`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ feature_key: newFeatureKey, enabled: newFeatureEnabled, config: {} }),
                            });
                            if (!res.ok) throw new Error("Failed to create");
                            addToast("Feature flag created", "success");
                            setNewFeatureKey("");
                            setNewFeatureEnabled(true);
                            if (res.ok) {
                              const data = await parseJsonResponse(res);
                              setFeatureFlags(Array.isArray(data) ? data : []);
                            }
                          } catch (err: any) {
                            addToast(err.message, "error");
                          }
                        }}
                        className="inline-flex h-8 items-center justify-center gap-1.5 rounded-lg border border-border bg-surface-2 px-3 text-xs font-semibold text-text hover:bg-surface-3 transition disabled:opacity-40"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Add Flag
                      </button>
                    </div>
                  </div>
                </section>
              )}

              {/* Tab 13: Staff Assignments */}
              {activeTab === "staff" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
                  <h3 className="text-sm font-bold text-text">Staff Assignments & Role Management</h3>
                  <p className="text-xs text-text-muted">Assign country-specific roles to users (Country Head, Country Manager, Country Finance).</p>

                  <div className="space-y-4">
                    <div className="border-t border-border pt-4">
                      <h4 className="text-xs font-bold text-text mb-2">Assign New Staff</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                        <label className="space-y-1 text-[10px] text-text-muted">
                          User ID
                          <input
                            type="text"
                            className="w-full rounded border border-border bg-surface px-2 py-1 text-xs text-text"
                            value={newStaffUserId}
                            onChange={(e) => setNewStaffUserId(e.target.value)}
                            placeholder="12345"
                          />
                        </label>
                        <label className="space-y-1 text-[10px] text-text-muted">
                          User Name
                          <input
                            type="text"
                            className="w-full rounded border border-border bg-surface px-2 py-1 text-xs text-text"
                            value={newStaffUserName}
                            onChange={(e) => setNewStaffUserName(e.target.value)}
                            placeholder="John Doe"
                          />
                        </label>
                        <label className="space-y-1 text-[10px] text-text-muted">
                          Email
                          <input
                            type="email"
                            className="w-full rounded border border-border bg-surface px-2 py-1 text-xs text-text"
                            value={newStaffEmail}
                            onChange={(e) => setNewStaffEmail(e.target.value)}
                            placeholder="john@example.com"
                          />
                        </label>
                        <label className="space-y-1 text-[10px] text-text-muted">
                          Role
                          <select
                            className="w-full rounded border border-border bg-surface px-2 py-1 text-xs text-text"
                            value={newStaffRole}
                            onChange={(e) => setNewStaffRole(e.target.value as any)}
                          >
                            <option value="country_manager">Country Manager</option>
                            <option value="country_head">Country Head</option>
                            <option value="country_finance">Country Finance</option>
                          </select>
                        </label>
                      </div>
                      <Button variant="primary" className="mt-2 inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold hover:opacity-90 transition disabled:opacity-60" type="button"
                        disabled={!newStaffUserId || !newStaffUserName}
                        onClick={async () => {
                          try {
                            const res = await apiFetch(`/admin/countries/${selectedCountryCode}/staff`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({
                                user_id: Number(newStaffUserId),
                                user_name: newStaffUserName,
                                email: newStaffEmail,
                                role: newStaffRole,
                              }),
                            });
                            if (!res.ok) throw new Error("Failed to assign");
                            addToast("Staff assigned", "success");
                            setNewStaffUserId("");
                            setNewStaffUserName("");
                            setNewStaffEmail("");
                            if (res.ok) {
                              const data = await parseJsonResponse(res);
                              setStaffAssignments(Array.isArray(data) ? data : []);
                            }
                          } catch (err: any) {
                            addToast(err.message, "error");
                          }
                        }}
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Assign Staff
                      </Button>
                    </div>

                    <div className="border-t border-border pt-4">
                      <h4 className="text-xs font-bold text-text mb-2">Assigned Staff</h4>
                      {staffAssignments.length === 0 ? (
                        <p className="text-sm text-text-muted italic">No staff assigned to this country.</p>
                      ) : (
                        <div className="space-y-2">
                          {staffAssignments.map((staff) => (
                            <div key={staff.user_id} className="flex items-center justify-between rounded-lg border border-border bg-surface p-3 text-xs">
                              <div>
                                <span className="font-medium text-text">{staff.user_name}</span>
                                <span className="text-text-muted ml-2">({staff.email})</span>
                                <div className="text-text-faint mt-1">Role: <span className="font-medium">{staff.role.replace("_", " ")}</span></div>
                              </div>
                              <Button variant="danger" className="p-1 rounded transition" type="button"
                                onClick={async () => {
                                  try {
                                    await apiFetch(`/admin/countries/${selectedCountryCode}/staff/${staff.user_id}`, { method: "DELETE" });
                                    addToast("Staff removed", "success");
                                    setStaffAssignments(staffAssignments.filter((s) => s.user_id !== staff.user_id));
                                  } catch {
                                    addToast("Failed to remove staff", "error");
                                  }
                                }}
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </section>
              )}

              {/* Tab: Communications */}
              {activeTab === "communications" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
                  <h3 className="text-sm font-bold text-text">Internal Communications</h3>
                  <p className="text-xs text-text-muted">Country-specific internal messaging between Admin, Country Head, and Country Manager teams.</p>
                  {selectedCountryCode && (
                    <InternalCommunicationsSystem countryCode={selectedCountryCode} />
                  )}
                </section>
              )}

              {/* Tab 14: Promotions */}
              {activeTab === "promotions" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1" data-testid="country-promotions-panel">
                  <h3 className="text-sm font-bold text-text">Promotion Rules & Discounts</h3>
                  <p className="text-xs text-text-muted">Configure country-specific promotion rules and discount policies.</p>

                  {/* Add Promotion Form */}
                  <div className="border border-border rounded-lg p-4 bg-surface space-y-3">
                    <h4 className="text-xs font-bold text-text">Create New Promotion Rule</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <label className="space-y-1 text-[10px] text-text-muted">
                        Slug (URL-safe ID)
                        <input
                          type="text"
                          className="w-full rounded border border-border bg-surface px-2 py-1.5 text-xs text-text"
                          value={newPromoSlug}
                          onChange={(e) => setNewPromoSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '').replace(/-/g, '-').replace(/^-+|-+$/g, ''))}
                          placeholder="summer-sale-2024"
                        />
                      </label>
                      <label className="space-y-1 text-[10px] text-text-muted">
                        Promotion Name
                        <input
                          type="text"
                          className="w-full rounded border border-border bg-surface px-2 py-1.5 text-xs text-text"
                          value={newPromoName}
                          onChange={(e) => setNewPromoName(e.target.value)}
                          placeholder="Summer Festival Sale"
                        />
                      </label>
                      <label className="space-y-1 text-[10px] text-text-muted">
                        Discount Type
                        <select
                          className="w-full rounded border border-border bg-surface px-2 py-1.5 text-xs text-text"
                          value={newPromoType}
                          onChange={(e) => setNewPromoType(e.target.value as "percentage" | "fixed")}
                        >
                          <option value="percentage">Percentage (%)</option>
                          <option value="fixed">Fixed Amount</option>
                        </select>
                      </label>
                      <label className="space-y-1 text-[10px] text-text-muted">
                        Discount Value
                        <input
                          type="number"
                          step="0.01"
                          className="w-full rounded border border-border bg-surface px-2 py-1.5 text-xs text-text"
                          value={newPromoValue}
                          onChange={(e) => setNewPromoValue(e.target.value)}
                          placeholder={newPromoType === "percentage" ? "10" : "50"}
                        />
                      </label>
                      <label className="space-y-1 text-[10px] text-text-muted md:col-span-2">
                        Minimum Order Value (Optional)
                        <input
                          type="number"
                          step="0.01"
                          className="w-full rounded border border-border bg-surface px-2 py-1.5 text-xs text-text"
                          value={newPromoMinOrder}
                          onChange={(e) => setNewPromoMinOrder(e.target.value)}
                          placeholder="100.00"
                        />
                      </label>
                      <div className="flex items-end">
                        <Button variant="primary" className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold hover:opacity-90 transition disabled:opacity-40" type="button"
                          disabled={!newPromoSlug || !newPromoName || !newPromoValue}
                          onClick={async () => {
                            if (!selectedCountryCode) return;
                            try {
                              const res = await apiFetch(`/admin/countries/${selectedCountryCode}/promotions`, {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({
                                  slug: newPromoSlug,
                                  name: newPromoName,
                                  discount_type: newPromoType,
                                  discount_value: Number(newPromoValue),
                                  min_order_value: newPromoMinOrder ? Number(newPromoMinOrder) : null,
                                  is_active: true,
                                }),
                              });
                              if (!res.ok) throw new Error("Failed to create promotion");
                              addToast("Promotion created", "success");
                              setNewPromoSlug("");
                              setNewPromoName("");
                              setNewPromoType("percentage");
                              setNewPromoValue("10");
                              setNewPromoMinOrder("");
                              if (res.ok) {
                                const data = await parseJsonResponse(res);
                                setPromotionRules(Array.isArray(data) ? data : []);
                              }
                            } catch (err: any) {
                              addToast(err.message, "error");
                            }
                          }}
                        >
                          <Plus className="h-3.5 w-3.5" />
                          Create Promotion
                        </Button>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    {promotionRules.length === 0 ? (
                      <p className="text-sm text-text-muted italic">No promotion rules configured for this country.</p>
                    ) : (
                      <div className="space-y-2">
                        {promotionRules.map((promo) => (
                          <div key={promo.slug} className="rounded-lg border border-border bg-surface p-3 text-xs" data-testid={`promotion-rule-${promo.slug}`}>
                            <div className="flex items-center justify-between">
                              <span className="font-medium text-text">{promo.name}</span>
                              <div className="flex items-center gap-2">
                                <span className="text-text-muted">
                                  {promo.discount_type === "percentage" 
                                    ? `${promo.discount_value}% off` 
                                    : `${promo.discount_value} ${selectedCountry?.currency} off`}
                                </span>
                                {promo.min_order_value && (
                                  <span className="text-text-faint">
                                    (min: {promo.min_order_value})
                                  </span>
                                )}
                                <Button variant="danger" className="p-1 rounded transition" type="button"
                                  onClick={async () => {
                                    try {
                                      await apiFetch(`/admin/countries/${selectedCountryCode}/promotions/${promo.slug}`, { method: "DELETE" });
                                      addToast("Promotion deleted", "success");
                                      setPromotionRules(promotionRules.filter(p => p.slug !== promo.slug));
                                    } catch {
                                      addToast("Failed to delete promotion", "error");
                                    }
                                  }}
                                  title="Delete promotion"
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </Button>
                              </div>
                            </div>
                            <div className="text-text-faint mt-1 text-[10px]">
                              Slug: <span className="font-mono">{promo.slug}</span> | 
                              Type: <span className="font-mono">{promo.discount_type}</span> | 
                              Status: <span className={promo.is_active ? "text-success" : "text-danger"}>{promo.is_active ? "Active" : "Inactive"}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </section>
              )}

              {/* Tab 15: Analytics */}
              {activeTab === "analytics" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1" data-testid="country-analytics-panel">
                  <h3 className="text-sm font-bold text-text">Analytics & Performance Metrics</h3>
                  <p className="text-xs text-text-muted">View country configuration analytics and performance indicators.</p>

                  {/* Key Metrics Grid */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="rounded-lg border border-border bg-surface p-3 text-center">
                      <div className="text-2xl font-bold text-primary">{country?.regions?.reduce((acc, r) => acc + (r.cities?.length || 0), 0) || 0}</div>
                      <div className="text-[10px] text-text-muted uppercase">Cities Covered</div>
                    </div>
                    <div className="rounded-lg border border-border bg-surface p-3 text-center">
                      <div className="text-2xl font-bold text-primary">{country?.payment_gateways?.filter(g => g.enabled).length || 0}</div>
                      <div className="text-[10px] text-text-muted uppercase">Active Gateways</div>
                    </div>
                    <div className="rounded-lg border border-border bg-surface p-3 text-center">
                      <div className="text-2xl font-bold text-primary">{country?.logistics_providers?.filter(p => p.enabled).length || 0}</div>
                      <div className="text-[10px] text-text-muted uppercase">Delivery Partners</div>
                    </div>
                    <div className="rounded-lg border border-border bg-surface p-3 text-center">
                      <div className="text-2xl font-bold text-primary">{promotionRules.length}</div>
                      <div className="text-[10px] text-text-muted uppercase">Active Promotions</div>
                    </div>
                  </div>

                  {/* Chart Visualizations */}
                  <div className="grid gap-4 md:grid-cols-2">
                    {/* Tax Configuration Pie Chart */}
                    <div className="rounded-lg border border-border bg-surface p-4">
                      <h4 className="text-xs font-bold text-text mb-3">Tax Configuration</h4>
                      <div className="h-56">
                        <PieChartComponent
                          data={[
                            { label: "Standard Rate", value: country?.tax_rate ? (country.tax_rate * 100) : 0 },
                            { label: "Exempt Categories", value: country?.tax_exempt_categories?.length || 0 },
                            { label: "Reduced Rates", value: country?.tax_reduced_rates ? Object.keys(country.tax_reduced_rates).length : 0 },
                          ]}
                          title={`Tax Rate: ${country?.tax_rate ? (country.tax_rate * 100).toFixed(1) : 0}%`}
                          colors={["#22c55e", "#6366f1", "#f59e0b"]}
                        />
                      </div>
                    </div>

                    {/* Payment Gateway Distribution */}
                    <div className="rounded-lg border border-border bg-surface p-4">
                      <h4 className="text-xs font-bold text-text mb-3">Payment Gateway Distribution</h4>
                      <div className="h-56">
                        <BarChartComponent
                          data={country?.payment_gateways?.map(g => ({
                            label: g.name.length > 10 ? g.name.substring(0, 10) + "..." : g.name,
                            value: g.fee_percentage,
                            enabled: g.enabled
                          })) || []}
                          title="Fees %"
                          yKeys={["value"]}
                          color="#3b82f6"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Commission Overview */}
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-text">Commission Structure</h4>
                      <div className="text-[10px] space-y-1">
                        <div className="flex justify-between">
                          <span className="text-text-faint">Value-based Tiers:</span>
                          <span className="text-text font-medium">{commissionTiers.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-faint">Category Overrides:</span>
                          <span className="text-text font-medium">{categoryCommissions.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-faint">Avg. Commission Rate:</span>
                          <span className="text-text font-medium">
                            {categoryCommissions.length > 0 
                              ? (categoryCommissions.reduce((sum, c) => sum + c.commission_rate, 0) / categoryCommissions.length * 100).toFixed(1) + "%"
                              : "N/A"}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <h4 className="text-xs font-bold text-text">Regional Coverage</h4>
                      <div className="text-[10px] space-y-1">
                        <div className="flex justify-between">
                          <span className="text-text-faint">Regions/Hubs:</span>
                          <span className="text-text font-medium">{regions.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-faint">Staff Assignments:</span>
                          <span className="text-text font-medium">{staffAssignments.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-text-faint">Active Status:</span>
                          <span className={`font-medium ${country?.is_active ? "text-success" : "text-danger"}`}>
                            {country?.is_active ? "Active" : "Inactive"}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="text-[10px] text-text-muted italic border-t border-border pt-2">
                    Advanced analytics dashboard with sales trends, conversion rates, and performance KPIs coming soon.
                  </div>
                </section>
              )}

              {/* Tab 16: Localization */}
              {activeTab === "localization" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1">
                  <h3 className="text-sm font-bold text-text">Localization & Regional Settings</h3>
                  <p className="text-xs text-text-muted">Configure language, currency, and regional display settings for this country.</p>

                  <div className="grid gap-4">
                    <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">
                      <label className="space-y-1 text-xs text-text-muted">
                        Default Language
                        <select
                          className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
                          value={localization.default_language}
                          onChange={(e) => setLocalization({ ...localization, default_language: e.target.value })}
                        >
                          <option value="en">English</option>
                          <option value="ar">Arabic</option>
                          <option value="fr">French</option>
                          <option value="es">Spanish</option>
                        </select>
                      </label>
                      <label className="space-y-1 text-xs text-text-muted">
                        Number Format
                        <select
                          className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
                          value={localization.number_format}
                          onChange={(e) => setLocalization({ ...localization, number_format: e.target.value as any })}
                        >
                          <option value="western">Western (1,234.56)</option>
                          <option value="eastern">Eastern (1٬234٫56)</option>
                        </select>
                      </label>
                      <label className="space-y-1 text-xs text-text-muted">
                        Calendar Type
                        <select
                          className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text"
                          value={localization.calendar_type}
                          onChange={(e) => setLocalization({ ...localization, calendar_type: e.target.value as any })}
                        >
                          <option value="gregorian">Gregorian</option>
                          <option value="hijri">Hijri</option>
                        </select>
                      </label>
                    </div>

                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
                        <input
                          type="checkbox"
                          checked={localization.rtl_enabled}
                          onChange={(e) => setLocalization({ ...localization, rtl_enabled: e.target.checked })}
                        />
                        Enable RTL Layout
                      </label>
                      <label className="flex items-center gap-2 text-xs font-semibold text-text cursor-pointer">
                        <input
                          type="checkbox"
                          checked={localization.supported_languages.includes("ar")}
                          onChange={(e) => {
                            const langs = e.target.checked
                              ? [...localization.supported_languages, "ar"]
                              : localization.supported_languages.filter((l) => l !== "ar");
                            setLocalization({ ...localization, supported_languages: langs });
                          }}
                        />
                        Support Arabic
                      </label>
                    </div>

                    <div className="text-[10px] text-text-muted">
                      <div className="font-semibold mb-1">Supported Languages</div>
                      <div className="flex flex-wrap gap-1">
                        {localization.supported_languages.map((lang) => (
                          <span key={lang} className="bg-surface-2 px-2 py-0.5 rounded font-mono">
                            {lang === "en" ? "English" : lang === "ar" ? "Arabic" : lang === "fr" ? "French" : lang}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end pt-2">
                    <Button variant="primary" className="inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition hover:opacity-90 shadow" type="button"
                      onClick={async () => {
                        try {
                          const res = await apiFetch(`/admin/countries/${selectedCountryCode}/localization`, {
                            method: "PUT",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify(localization),
                          });
                          if (!res.ok) throw new Error("Failed to save");
                          addToast("Localization settings saved", "success");
                        } catch (err: any) {
                          addToast(err.message, "error");
                        }
                      }}
                    >
                      <Save className="h-3.5 w-3.5" />
                      Save Localization
                    </Button>
                  </div>
                </section>
              )}

              {/* Tab 12: Version History */}
              {activeTab === "versions" && (
                <section className="theme-card rounded-xl border p-4 space-y-4 bg-surface-1" data-testid="country-versions-panel">
                  <h3 className="text-sm font-bold text-text">Version History & Draft Pipelines</h3>
                  <p className="text-xs text-text-muted">GCC configs follow a draft-approve-publish workflow. Approved versions can be published instantly or rolled back to previous states.</p>

                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold text-text-muted">Filter By Config:</span>
                    {[
                      { key: "all", label: "All Configs" },
                      { key: "tax", label: "Tax" },
                      { key: "logistics", label: "Internal Logistics" },
                      { key: "logistics_providers", label: "Delivery Partners" },
                      { key: "payment_gateways", label: "Payment Gateways" },
                      { key: "legal_rules", label: "Legal Rules" },
                      { key: "regions", label: "Regions" },
                      { key: "supplier_requirements", label: "Supplier KYC" },
                      { key: "payout_settings", label: "Payouts" },
                      { key: "commission_tiers", label: "Value Commissions" },
                      { key: "commission", label: "Category Commissions" },
                    ].map((filter) => (
                      <button
                        key={filter.key}
                        type="button"
                        onClick={() => setActiveVersionType(filter.key)}
                        className={`rounded-full border px-3 py-1 text-[11px] font-semibold transition ${
                          activeVersionType === filter.key
                            ? "border-primary bg-primary/10 text-primary"
                            : "border-border bg-surface text-text-muted hover:text-text"
                        }`}
                      >
                        {filter.label}
                      </button>
                    ))}
                  </div>

                  <div className="overflow-x-auto rounded-lg border border-border bg-surface">
                    <table className="w-full min-w-[860px] border-collapse text-xs">
                      <thead className="bg-surface-2 text-left text-text-muted">
                        <tr>
                          <th className="px-3 py-2 font-semibold">Config Type</th>
                          <th className="px-3 py-2 font-semibold">Version Number</th>
                          <th className="px-3 py-2 font-semibold">Current State</th>
                          <th className="px-3 py-2 font-semibold">Created Date</th>
                          <th className="px-3 py-2 font-semibold">Published Date</th>
                          <th className="px-3 py-2 font-semibold w-[220px]">Workflow Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredVersions.map((version) => (
                          <tr key={version.id} className="border-t border-border/80 hover:bg-surface-2/40 transition" data-version-id={version.id}>
                            <td className="px-3 py-2.5 font-bold uppercase tracking-wide text-text font-mono text-[10px]">
                              {version.config_type.replace("_", " ")}
                            </td>
                            <td className="px-3 py-2.5 text-text font-semibold">v{version.version}</td>
                            <td className="px-3 py-2.5">
                              <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                version.status === "published"
                                  ? "bg-success/15 text-success border border-success/30"
                                  : version.status === "approved"
                                  ? "bg-primary/15 text-primary border border-primary/30"
                                  : version.status === "draft"
                                  ? "bg-warning/15 text-warning border border-warning/30"
                                  : "bg-text-faint/15 text-text-muted border"
                              }`}>
                                {version.status.toUpperCase()}
                              </span>
                            </td>
                            <td className="px-3 py-2.5 text-text-muted">{formatIso(version.created_at)}</td>
                            <td className="px-3 py-2.5 text-text-muted">{formatIso(version.published_at)}</td>
                            <td className="px-3 py-2.5">
                              <div className="flex flex-wrap gap-1.5">
                                <button
                                  type="button"
                                  onClick={() => actOnVersion(version, "approve")}
                                  disabled={busyAction === `approve-${version.id}` || version.status !== "draft"}
                                  className="inline-flex items-center gap-1 rounded bg-surface border border-border px-2 py-1 text-[10px] font-bold text-text hover:bg-surface-3 transition disabled:opacity-40"
                                  data-testid={`approve-version-${version.id}`}
                                >
                                  <Check className="h-3 w-3 text-success" />
                                  Approve
                                </button>
                                <Button variant="primary" className="inline-flex items-center gap-1 rounded px-2 py-1 text-[10px] font-bold transition disabled:opacity-40" type="button"
                                  onClick={() => actOnVersion(version, "publish")}
                                  disabled={busyAction === `publish-${version.id}` || !["draft", "approved"].includes(version.status)}
                                  data-testid={`publish-version-${version.id}`}
                                >
                                  <UploadCloud className="h-3 w-3" />
                                  Publish
                                </Button>
                                <Button variant="danger" className="inline-flex items-center gap-1 rounded bg-surface border border-border px-2 py-1 text-[10px] font-bold hover:bg-danger/10 hover:border-danger/20 transition disabled:opacity-40" type="button"
                                  onClick={() => actOnVersion(version, "rollback")}
                                  disabled={busyAction === `rollback-${version.id}` || version.status !== "published"}
                                  data-testid={`rollback-version-${version.id}`}
                                >
                                  <RefreshCw className="h-3 w-3" />
                                  Rollback
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                        {filteredVersions.length === 0 ? (
                          <tr>
                            <td className="px-3 py-4 text-center text-text-muted" colSpan={6}>
                              No version control ledgers recorded for this configuration filter.
                            </td>
                          </tr>
                        ) : null}
                      </tbody>
                    </table>
                  </div>
                </section>
              )}
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center py-8 text-sm text-text-muted">
            {loadingCountry ? "Loading country configuration..." : "Click a country row above to configure."}
          </div>
        )}
        </CountryLedgerTable>
        </section>
      </PanelContent>

    </AdminLayout>
  );
}
