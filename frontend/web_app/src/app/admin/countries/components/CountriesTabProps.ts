"use client";

import type {
  ConfigTab, DeliveryZone, CommissionRate, ConfigVersion, City,
  FeatureFlag, CountryStaffAssignment, PromotionRule,
  LocalizationConfig, PaymentGatewayItem, LogisticsProviderItem,
  LegalRules, RegionItem, SupplierRequirements, PayoutSettings,
  CommissionTierItem, TaxPreviewResult, CountryConfig,
} from "../types";

export interface CountriesTabProps {
  // App state
  activeTab: ConfigTab;
  setActiveTab: (tab: ConfigTab) => void;
  busyAction: string | null;
  selectedCountryCode: string;
  canSubmit: boolean;
  loadingCountry: boolean;
  activityMessage: string;

  // Toast
  addToast: (msg: string, type: "success" | "error" | "warning" | "info") => void;

  // Country data
  country: CountryConfig | null;
  selectedCountry: CountryConfig | null;
  countries: CountryConfig[];
  deliveryZones: DeliveryZone[];
  setDeliveryZones: (zones: DeliveryZone[]) => void;
  categoryCommissions: CommissionRate[];
  setCategoryCommissions: (rates: CommissionRate[]) => void;
  versions: ConfigVersion[];
  cities: City[];
  allCategories: any[];
  setAllCategories: (cats: any[]) => void;

  // Overview
  name: string; setName: (v: string) => void;
  currencySymbol: string; setCurrencySymbol: (v: string) => void;
  phoneCode: string; setPhoneCode: (v: string) => void;
  language: string; setLanguage: (v: string) => void;
  isActive: boolean; setIsActive: (v: boolean) => void;

  // Tax
  taxType: string; setTaxType: (v: string) => void;
  taxRate: string; setTaxRate: (v: string) => void;
  taxName: string; setTaxName: (v: string) => void;
  taxInclusive: boolean; setTaxInclusive: (v: boolean) => void;
  taxExemptCategories: string; setTaxExemptCategories: (v: string) => void;
  reducedTaxRates: Array<{category: string; rate: string}>; setReducedTaxRates: (v: any) => void;
  newReducedCategory: string; setNewReducedCategory: (v: string) => void;
  newReducedRate: string; setNewReducedRate: (v: string) => void;
  previewAmount: string; setPreviewAmount: (v: string) => void;
  previewCategory: string; setPreviewCategory: (v: string) => void;
  previewInclusive: "auto" | "inclusive" | "exclusive"; setPreviewInclusive: (v: any) => void;
  previewResult: TaxPreviewResult | null; setPreviewResult: (v: any) => void;

  // Logistics Model
  logisticsModel: string; setLogisticsModel: (v: string) => void;
  defaultVehicleType: string; setDefaultVehicleType: (v: string) => void;
  baseRate: string; setBaseRate: (v: string) => void;
  perKmRate: string; setPerKmRate: (v: string) => void;
  minimumCharge: string; setMinimumCharge: (v: string) => void;
  weightSurchargeRate: string; setWeightSurchargeRate: (v: string) => void;
  weightThresholdKg: string; setWeightThresholdKg: (v: string) => void;
  newZoneCode: string; setNewZoneCode: (v: string) => void;
  newZoneName: string; setNewZoneName: (v: string) => void;
  newZoneDescription: string; setNewZoneDescription: (v: string) => void;
  newZoneCarRate: string; setNewZoneCarRate: (v: string) => void;
  newZoneVanRate: string; setNewZoneVanRate: (v: string) => void;
  newZoneTruckRate: string; setNewZoneTruckRate: (v: string) => void;
  newZoneWeightSurcharge: string; setNewZoneWeightSurcharge: (v: string) => void;
  newZoneWeightThreshold: string; setNewZoneWeightThreshold: (v: string) => void;
  newZoneCities: string; setNewZoneCities: (v: string) => void;

  // Logistics Providers
  providers: LogisticsProviderItem[]; setProviders: (v: LogisticsProviderItem[]) => void;
  newProviderId: string; setNewProviderId: (v: string) => void;
  newProviderName: string; setNewProviderName: (v: string) => void;
  newProviderServiceAreas: string; setNewProviderServiceAreas: (v: string) => void;
  newProviderSlaStd: string; setNewProviderSlaStd: (v: string) => void;
  newProviderSlaExp: string; setNewProviderSlaExp: (v: string) => void;
  newProviderBaseRate: string; setNewProviderBaseRate: (v: string) => void;
  newProviderPerKg: string; setNewProviderPerKg: (v: string) => void;
  newProviderCurrency: string; setNewProviderCurrency: (v: string) => void;

  // Payment Gateways
  gateways: PaymentGatewayItem[]; setGateways: (v: PaymentGatewayItem[]) => void;
  newGatewayId: string; setNewGatewayId: (v: string) => void;
  newGatewayName: string; setNewGatewayName: (v: string) => void;
  newGatewayType: string; setNewGatewayType: (v: string) => void;
  newGatewayCredRef: string; setNewGatewayCredRef: (v: string) => void;
  newGatewaySupportsCod: boolean; setNewGatewaySupportsCod: (v: boolean) => void;
  newGatewaySupportsInstall: boolean; setNewGatewaySupportsInstall: (v: boolean) => void;
  newGatewayFeePct: string; setNewGatewayFeePct: (v: string) => void;
  newGatewayFeeFixed: string; setNewGatewayFeeFixed: (v: string) => void;

  // Legal Rules
  minimumOrderAge: number; setMinimumOrderAge: (v: number) => void;
  maxReturnsAllowed: number; setMaxReturnsAllowed: (v: number) => void;
  returnWindowDays: number; setReturnWindowDays: (v: number) => void;
  refundProcessingDays: number; setRefundProcessingDays: (v: number) => void;
  requiresCommercialLicense: boolean; setRequiresCommercialLicense: (v: boolean) => void;
  requiresVatRegistration: boolean; setRequiresVatRegistration: (v: boolean) => void;
  productRestrictions: string; setProductRestrictions: (v: string) => void;

  // Regions
  regions: RegionItem[]; setRegions: (v: RegionItem[]) => void;
  newRegionName: string; setNewRegionName: (v: string) => void;
  newRegionCities: string; setNewRegionCities: (v: string) => void;
  expandedRegions: Record<string, boolean>; setExpandedRegions: (v: any) => void;

  // Supplier KYC
  kycLevel: string; setKycLevel: (v: string) => void;
  requiredDocuments: string[]; setRequiredDocuments: (v: string[]) => void;
  approvalRequired: boolean; setApprovalRequired: (v: boolean) => void;

  // Payout Settings
  minimumPayoutAmount: string; setMinimumPayoutAmount: (v: string) => void;
  payoutSchedule: string; setPayoutSchedule: (v: string) => void;
  payoutDay: string; setPayoutDay: (v: string) => void;
  batchSize: string; setBatchSize: (v: string) => void;
  payoutCurrency: string; setPayoutCurrency: (v: string) => void;
  catPayoutRules: any[]; setCatPayoutRules: (v: any[]) => void;
  prodPayoutRules: any[]; setProdPayoutRules: (v: any[]) => void;
  newCatPayoutSlug: string; setNewCatPayoutSlug: (v: string) => void;
  newCatPayoutRate: string; setNewCatPayoutRate: (v: string) => void;
  newProdPayoutId: string; setNewProdPayoutId: (v: string) => void;
  newProdPayoutRate: string; setNewProdPayoutRate: (v: string) => void;

  // Commission Tiers
  commissionTiers: CommissionTierItem[]; setCommissionTiers: (v: CommissionTierItem[]) => void;
  newTierMin: string; setNewTierMin: (v: string) => void;
  newTierMax: string; setNewTierMax: (v: string) => void;
  newTierPct: string; setNewTierPct: (v: string) => void;
  newTierFixed: string; setNewTierFixed: (v: string) => void;

  // Category Commissions
  newCategorySlug: string; setNewCategorySlug: (v: string) => void;
  bulkFillRate: string; setBulkFillRate: (v: string) => void;
  newCategoryRate: string; setNewCategoryRate: (v: string) => void;
  newCategoryNotes: string; setNewCategoryNotes: (v: string) => void;

  // Feature Flags
  featureFlags: FeatureFlag[]; setFeatureFlags: (v: FeatureFlag[]) => void;
  newFeatureKey: string; setNewFeatureKey: (v: string) => void;
  newFeatureEnabled: boolean; setNewFeatureEnabled: (v: boolean) => void;

  // Staff
  staffAssignments: CountryStaffAssignment[]; setStaffAssignments: (v: CountryStaffAssignment[]) => void;
  newStaffUserId: string; setNewStaffUserId: (v: string) => void;
  newStaffUserName: string; setNewStaffUserName: (v: string) => void;
  newStaffEmail: string; setNewStaffEmail: (v: string) => void;
  newStaffRole: "country_head" | "country_manager" | "country_finance"; setNewStaffRole: (v: any) => void;

  // Promotions
  promotionRules: PromotionRule[]; setPromotionRules: (v: PromotionRule[]) => void;
  newPromoSlug: string; setNewPromoSlug: (v: string) => void;
  newPromoName: string; setNewPromoName: (v: string) => void;
  newPromoType: "percentage" | "fixed"; setNewPromoType: (v: any) => void;
  newPromoValue: string; setNewPromoValue: (v: string) => void;
  newPromoMinOrder: string; setNewPromoMinOrder: (v: string) => void;

  // Localization
  localization: LocalizationConfig; setLocalization: (v: LocalizationConfig) => void;

  // Handlers
  submitIdentity: () => Promise<void>;
  submitTaxDraft: () => Promise<void>;
  previewTax: () => Promise<void>;
  submitLogisticsDraft: () => Promise<void>;
  submitLogisticsProvidersDraft: () => Promise<void>;
  submitPaymentGatewaysDraft: () => Promise<void>;
  submitLegalRulesDraft: () => Promise<void>;
  submitRegionsDraft: () => Promise<void>;
  submitSupplierRequirementsDraft: () => Promise<void>;
  submitPayoutSettingsDraft: () => Promise<void>;
  submitCommissionTiersDraft: () => Promise<void>;
  submitCategoryCommissionsDraft: () => Promise<void>;
  actOnVersion: (version: ConfigVersion, action: "approve" | "publish" | "rollback") => Promise<void>;
  loadPayoutRules: (countryCode: string) => Promise<void>;
  activeVersionType: string; setActiveVersionType: (v: string) => void;
  filteredVersions: ConfigVersion[];
  countrySummaries: any[];
  setBusyAction: (v: string | null) => void;
  setActivityMessage: (v: string) => void;
  setCities: (v: City[]) => void;
}
