"use client";

export type ConfigTab =
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

export type VersionStatus = "draft" | "approved" | "published" | "rolled_back" | string;

export type FeatureFlag = {
  feature_key: string;
  enabled: boolean;
  config?: Record<string, any>;
};

export type CountryStaffAssignment = {
  user_id: number;
  user_name: string;
  email: string;
  role: "country_head" | "country_manager" | "country_finance";
  assigned_at: string;
};

export type PromotionRule = {
  slug: string;
  name: string;
  discount_type: "percentage" | "fixed";
  discount_value: number;
  min_order_value?: number | null;
  is_active: boolean;
};

export type City = {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  population?: number;
  is_capital?: boolean;
};

export type LocalizationConfig = {
  default_language: string;
  supported_languages: string[];
  rtl_enabled: boolean;
  number_format: "western" | "eastern";
  calendar_type: "gregorian" | "hijri";
};

export type PaymentGatewayItem = {
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

export type LogisticsProviderItem = {
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

export type LegalRules = {
  minimum_order_age: number;
  max_returns_allowed: number;
  return_window_days: number;
  refund_processing_days: number;
  requires_commercial_license: boolean;
  requires_vat_registration: boolean;
  product_restrictions: string[];
};

export type RegionItem = {
  region_id: string;
  name: string;
  cities: string[];
};

export type SupplierRequirements = {
  kyc_level: string;
  required_documents: string[];
  approval_required: boolean;
};

export type PayoutSettings = {
  minimum_payout_amount: number;
  payout_schedule: string;
  payout_day: string;
  batch_size: number;
  currency: string | null;
};

export type CommissionTierItem = {
  min_order_value: number;
  max_order_value: number | null;
  commission_percentage: number;
  fixed_fee: number;
};

export type DeliveryZone = {
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

export type CommissionRate = {
  category_slug: string;
  commission_rate: number;
  notes?: string | null;
  is_active: boolean;
};

export type ConfigVersion = {
  id: number;
  country_code: string;
  config_type: string;
  version: number;
  status: VersionStatus;
  created_at?: string;
  published_at?: string | null;
};

export type TaxPreviewResult = {
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

export type CountryConfig = {
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
