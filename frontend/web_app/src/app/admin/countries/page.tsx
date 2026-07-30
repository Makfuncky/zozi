"use client";

import { Button } from "@/components/ui/Button";

import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Globe, Plus, Trash2, Edit3, X, Check, Building2, Eye, Globe2,
  RefreshCw, Save, UploadCloud, ChevronDown, ChevronRight,
  Users, Bell, Lock, FileText, Calendar, MapPin, MapPinOff,
} from "@/lib/icons";
import CountryMapView from "@/components/country/CountryMapView";
import InternalCommunicationsSystem from "@/components/country/InternalCommunicationsSystem";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import AdminLayout from "@/components/AdminLayout";
import { PanelContent, PanelLoadingState, PanelTabs } from "@/components/PanelPage";
import { useAuth } from "@/lib/useAuth";
import { useToastStore } from "@/lib/toastStore";
import { isAdminStaffRole } from "@shared/adminPermissions";
import { formatNumber, PieChartComponent, BarChartComponent } from "@/components/ChartComponents";
import CountryLedgerTable from "./CountryLedgerTable";
import type { ConfigTab, CountryConfig, DeliveryZone, CommissionRate, ConfigVersion, City, FeatureFlag, CountryStaffAssignment, PromotionRule, LocalizationConfig, PaymentGatewayItem, LogisticsProviderItem, LegalRules, RegionItem, SupplierRequirements, PayoutSettings, CommissionTierItem, TaxPreviewResult } from "./types";
import { CONFIG_TABS, toErrorMessage, toNumberOrNull, formatIso } from "./constants";
import OverviewTab from "./components/OverviewTab";
import TaxTab from "./components/TaxTab";
import LogisticsModelTab from "./components/LogisticsModelTab";
import LogisticsProvidersTab from "./components/LogisticsProvidersTab";
import PaymentGatewaysTab from "./components/PaymentGatewaysTab";
import LegalRulesTab from "./components/LegalRulesTab";
import RegionsTab from "./components/RegionsTab";
import MapTab from "./components/MapTab";
import KycTab from "./components/KycTab";
import PayoutSettingsTab from "./components/PayoutSettingsTab";
import CommissionTiersTab from "./components/CommissionTiersTab";
import CategoryCommissionsTab from "./components/CategoryCommissionsTab";
import FeatureFlagsTab from "./components/FeatureFlagsTab";
import StaffTab from "./components/StaffTab";
import CommunicationsTab from "./components/CommunicationsTab";
import PromotionsTab from "./components/PromotionsTab";
import AnalyticsTab from "./components/AnalyticsTab";
import LocalizationTab from "./components/LocalizationTab";
import VersionsTab from "./components/VersionsTab";


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

  const tabProps = {
    activeTab, setActiveTab, busyAction,
    selectedCountryCode, canSubmit, loadingCountry, activityMessage,
    addToast, country, selectedCountry, countries,
    deliveryZones, setDeliveryZones, categoryCommissions,
    setCategoryCommissions, versions, cities, allCategories,
    setAllCategories, name, setName, currencySymbol,
    setCurrencySymbol, phoneCode, setPhoneCode, language,
    setLanguage, isActive, setIsActive,
    taxType, setTaxType, taxRate, setTaxRate, taxName, setTaxName,
    taxInclusive, setTaxInclusive, taxExemptCategories,
    setTaxExemptCategories, reducedTaxRates, setReducedTaxRates,
    newReducedCategory, setNewReducedCategory, newReducedRate,
    setNewReducedRate, previewAmount, setPreviewAmount,
    previewCategory, setPreviewCategory, previewInclusive,
    setPreviewInclusive, previewResult, setPreviewResult,
    logisticsModel, setLogisticsModel, defaultVehicleType,
    setDefaultVehicleType, baseRate, setBaseRate, perKmRate,
    setPerKmRate, minimumCharge, setMinimumCharge,
    weightSurchargeRate, setWeightSurchargeRate, weightThresholdKg,
    setWeightThresholdKg,
    newZoneCode, setNewZoneCode, newZoneName, setNewZoneName,
    newZoneDescription, setNewZoneDescription,
    newZoneCarRate, setNewZoneCarRate, newZoneVanRate,
    setNewZoneVanRate, newZoneTruckRate, setNewZoneTruckRate,
    newZoneWeightSurcharge, setNewZoneWeightSurcharge,
    newZoneWeightThreshold, setNewZoneWeightThreshold,
    newZoneCities, setNewZoneCities,
    providers, setProviders,
    newProviderId, setNewProviderId, newProviderName,
    setNewProviderName, newProviderServiceAreas,
    setNewProviderServiceAreas, newProviderSlaStd,
    setNewProviderSlaStd, newProviderSlaExp, setNewProviderSlaExp,
    newProviderBaseRate, setNewProviderBaseRate, newProviderPerKg,
    setNewProviderPerKg, newProviderCurrency, setNewProviderCurrency,
    gateways, setGateways,
    newGatewayId, setNewGatewayId, newGatewayName,
    setNewGatewayName, newGatewayType, setNewGatewayType,
    newGatewayCredRef, setNewGatewayCredRef,
    newGatewaySupportsCod, setNewGatewaySupportsCod,
    newGatewaySupportsInstall, setNewGatewaySupportsInstall,
    newGatewayFeePct, setNewGatewayFeePct, newGatewayFeeFixed,
    setNewGatewayFeeFixed,
    minimumOrderAge, setMinimumOrderAge, maxReturnsAllowed,
    setMaxReturnsAllowed, returnWindowDays, setReturnWindowDays,
    refundProcessingDays, setRefundProcessingDays,
    requiresCommercialLicense, setRequiresCommercialLicense,
    requiresVatRegistration, setRequiresVatRegistration,
    productRestrictions, setProductRestrictions,
    regions, setRegions, newRegionName, setNewRegionName,
    newRegionCities, setNewRegionCities,
    expandedRegions, setExpandedRegions,
    kycLevel, setKycLevel, requiredDocuments, setRequiredDocuments,
    approvalRequired, setApprovalRequired,
    minimumPayoutAmount, setMinimumPayoutAmount,
    payoutSchedule, setPayoutSchedule, payoutDay, setPayoutDay,
    batchSize, setBatchSize, payoutCurrency, setPayoutCurrency,
    catPayoutRules, setCatPayoutRules, prodPayoutRules,
    setProdPayoutRules,
    newCatPayoutSlug, setNewCatPayoutSlug, newCatPayoutRate,
    setNewCatPayoutRate, newProdPayoutId, setNewProdPayoutId,
    newProdPayoutRate, setNewProdPayoutRate,
    commissionTiers, setCommissionTiers,
    newTierMin, setNewTierMin, newTierMax, setNewTierMax,
    newTierPct, setNewTierPct, newTierFixed, setNewTierFixed,
    newCategorySlug, setNewCategorySlug, bulkFillRate,
    setBulkFillRate, newCategoryRate, setNewCategoryRate,
    newCategoryNotes, setNewCategoryNotes,
    featureFlags, setFeatureFlags, newFeatureKey,
    setNewFeatureKey, newFeatureEnabled, setNewFeatureEnabled,
    staffAssignments, setStaffAssignments,
    newStaffUserId, setNewStaffUserId, newStaffUserName,
    setNewStaffUserName, newStaffEmail, setNewStaffEmail,
    newStaffRole, setNewStaffRole,
    promotionRules, setPromotionRules,
    newPromoSlug, setNewPromoSlug, newPromoName, setNewPromoName,
    newPromoType, setNewPromoType, newPromoValue,
    setNewPromoValue, newPromoMinOrder, setNewPromoMinOrder,
    localization, setLocalization,
    submitIdentity, submitTaxDraft, previewTax,
    submitLogisticsDraft, submitLogisticsProvidersDraft,
    submitPaymentGatewaysDraft, submitLegalRulesDraft,
    submitRegionsDraft, submitSupplierRequirementsDraft,
    submitPayoutSettingsDraft, submitCommissionTiersDraft,
    submitCategoryCommissionsDraft, actOnVersion, loadPayoutRules,
    activeVersionType, setActiveVersionType, filteredVersions,
    countrySummaries, setBusyAction, setActivityMessage, setCities,
  };

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
                  
              <OverviewTab {...tabProps} />

              {/* Tab 2: Tax & VAT */}
              <TaxTab {...tabProps} />

              {/* Tab 3: Internal Logistics Model */}
              <LogisticsModelTab {...tabProps} />

              {/* Tab 4: Delivery Partners (Logistics Providers) */}
              <LogisticsProvidersTab {...tabProps} />

              {/* Tab 5: Payment Gateways */}
              <PaymentGatewaysTab {...tabProps} />

              {/* Tab 6: Legal & Safety Rules */}
              <LegalRulesTab {...tabProps} />

              {/* Tab 7: Regions & Cities */}
              <RegionsTab {...tabProps} />

              {/* Tab 8: Interactive Map */}
              <MapTab {...tabProps} />

              {/* Tab 9: Supplier KYC Requirements */}
              <KycTab {...tabProps} />

              {/* Tab 9: Payout Settings */}
              <PayoutSettingsTab {...tabProps} />

              {/* Tab 10: Value Commissions (Tiers) */}
              <CommissionTiersTab {...tabProps} />

              {/* Tab 11: Category Commissions */}
              <CategoryCommissionsTab {...tabProps} />

              {/* Tab 12: Feature Flags */}
              <FeatureFlagsTab {...tabProps} />

              {/* Tab 13: Staff Assignments */}
              <StaffTab {...tabProps} />

              {/* Tab: Communications */}
              <CommunicationsTab {...tabProps} />

              {/* Tab 14: Promotions */}
              <PromotionsTab {...tabProps} />

              {/* Tab 15: Analytics */}
              <AnalyticsTab {...tabProps} />

              {/* Tab 16: Localization */}
              <LocalizationTab {...tabProps} />

              {/* Tab 12: Version History */}
              <VersionsTab {...tabProps} />
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
