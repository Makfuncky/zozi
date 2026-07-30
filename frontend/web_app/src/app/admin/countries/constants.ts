"use client";

import { type ComponentType } from "react";
import {
  Globe, Percent, Truck, Compass, CreditCard, Scale, Map, MapPin,
  FileCheck, DollarSign, Layers, Tags, History, ShieldCheck,
  BarChart3, Users, MessageCircle, Tag, Globe2,
} from "@/lib/icons";
import { getErrorMessage } from "@/lib/api";
import type { ConfigTab } from "./types";

export const CONFIG_TABS: Array<{ key: ConfigTab; label: string; icon: ComponentType<{ className?: string }> }> = [
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

export function toErrorMessage(status: number, payload: any, fallback: string): string {
  const detail = payload ? getErrorMessage(payload) : fallback;
  return `${fallback} (HTTP ${status})${detail ? `: ${detail}` : ""}`;
}

export function toNumberOrNull(value: string): number | null {
  const normalized = value.trim();
  if (!normalized) return null;
  const parsed = Number(normalized);
  if (!Number.isFinite(parsed)) {
    throw new Error(`Invalid numeric value: ${value}`);
  }
  return parsed;
}

export function formatIso(value?: string | null): string {
  if (!value) return "-";
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) return value;
  return new Date(parsed).toLocaleString();
}
