import { useMemo } from "react";
import { useAuth } from "@/lib/useAuth";
import { ConfigTab } from "@/components/country/CountryDetailWorkspace";

export interface CountryAccess {
  canView: boolean;
  canEdit: boolean;
  allowedTabs: ConfigTab[];
  restrictedTabs: ConfigTab[];
}

const ALL_TABS: ConfigTab[] = [
  "overview",
  "tax",
  "logistics_model",
  "logistics_providers",
  "payment_gateways",
  "legal_rules",
  "regions",
  "kyc",
  "payout_settings",
  "commission_tiers",
  "category_commissions",
  "feature_flags",
  "analytics",
  "staff",
  "promotions",
  "localization",
  "versions",
];

const MANAGER_RESTRICTED_TABS: ConfigTab[] = [
  "feature_flags",
  "analytics",
  "staff",
  "promotions",
  "localization",
  "versions",
];

export function useCountryAccess(countryCode?: string): CountryAccess {
  const { user } = useAuth();
  const userRole = user?.role;

  return useMemo(() => {
    // Default: no access
    if (!userRole) {
      return {
        canView: false,
        canEdit: false,
        allowedTabs: [],
        restrictedTabs: ALL_TABS,
      };
    }

    // Admin/Country Head - full access
    if (userRole === "admin" || userRole === "country_head") {
      return {
        canView: true,
        canEdit: true,
        allowedTabs: ALL_TABS,
        restrictedTabs: [],
      };
    }

// Country Manager - limited access
    if (userRole === "country_manager") {
      const allowedTabs = ALL_TABS.filter((tab) => !MANAGER_RESTRICTED_TABS.includes(tab));
      return {
        canView: true,
        canEdit: true,
        allowedTabs,
        restrictedTabs: MANAGER_RESTRICTED_TABS,
      };
    }

    // All other roles (sub_admin, etc.) have no access
    return {
      canView: false,
      canEdit: false,
      allowedTabs: [],
      restrictedTabs: ALL_TABS,
    };
  }, [userRole]);
}
