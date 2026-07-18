"use client";

import { type ComponentType, useMemo } from "react";
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
  ShieldCheck,
  BarChart3,
  Users,
  Tag,
  Globe2,
  FileText,
  Calendar,
  Lock,
} from "@/lib/icons";
import { useCountryAccess } from "@/hooks/useCountryAccess";

export type ConfigTab =
  | "overview"
  | "tax"
  | "logistics_model"
  | "logistics_providers"
  | "payment_gateways"
  | "legal_rules"
  | "regions"
  | "kyc"
  | "payout_settings"
  | "commission_tiers"
  | "category_commissions"
  | "feature_flags"
  | "analytics"
  | "staff"
  | "promotions"
  | "localization"
  | "versions";

export const CONFIG_TABS: Array<{ key: ConfigTab; label: string; icon: ComponentType<{ className?: string }> }> = [
  { key: "overview", label: "Overview", icon: Globe },
  { key: "tax", label: "Tax & VAT", icon: Percent },
  { key: "logistics_model", label: "Internal Logistics", icon: Truck },
  { key: "logistics_providers", label: "Delivery Partners", icon: Compass },
  { key: "payment_gateways", label: "Payment Gateways", icon: CreditCard },
  { key: "legal_rules", label: "Legal & Rules", icon: Scale },
  { key: "regions", label: "Regions & Cities", icon: Map },
  { key: "kyc", label: "Supplier KYC", icon: FileCheck },
  { key: "payout_settings", label: "Payout Settings", icon: DollarSign },
  { key: "commission_tiers", label: "Value Commissions", icon: Layers },
  { key: "category_commissions", label: "Category Commissions", icon: Tags },
  { key: "feature_flags", label: "Feature Flags", icon: ShieldCheck },
  { key: "analytics", label: "Analytics", icon: BarChart3 },
  { key: "staff", label: "Staff Assignments", icon: Users },
  { key: "promotions", label: "Promotions", icon: Tag },
  { key: "localization", label: "Localization", icon: Globe2 },
  { key: "versions", label: "Version History", icon: History },
];

interface CountryDetailWorkspaceProps {
  activeTab: ConfigTab;
  onTabChange: (tab: ConfigTab) => void;
}

export function useVisibleTabs(): ConfigTab[] {
  const { allowedTabs } = useCountryAccess();
  return useMemo(() => allowedTabs, [allowedTabs]);
}

export default function CountryDetailWorkspace({
  activeTab,
  onTabChange,
}: CountryDetailWorkspaceProps) {
  const visibleTabs = useVisibleTabs();

  return (
    <div className="space-y-4">
      {/* Tab Navigation */}
      <div className="border-b border-border">
        <nav className="-mb-px flex flex-wrap gap-1" aria-label="Country configuration tabs">
          {visibleTabs.map((tab) => {
            const tabConfig = CONFIG_TABS.find((t) => t.key === tab);
            if (!tabConfig) return null;
            const Icon = tabConfig.icon;
            const isActive = activeTab === tab;

            return (
              <button
                key={tab}
                onClick={() => onTabChange(tab)}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-t-lg border-b-2 transition-colors ${
                  isActive
                    ? "border-primary text-primary bg-primary/5"
                    : "border-transparent text-text-muted hover:text-text hover:bg-surface-2/50"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{tabConfig.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content Placeholder */}
      <div className="min-h-[400px]">
        <div className="text-center py-8 text-text-muted">
          <Lock className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">Tab content for "{activeTab}" will be rendered here.</p>
          <p className="text-xs mt-1">This is a placeholder for the detailed tab implementation.</p>
        </div>
      </div>
    </div>
  );
}


