/**
 * SupplierBadge.native.tsx — React Native version
 * Shows supplier credibility badge matching backend badge_level.
 */
import React from "react";
import { View, Text, StyleSheet } from "react-native";

/** Badge tiers matching backend badge_level values */
export type BadgeTier = "gold" | "silver" | "bronze" | "verified" | "none";

/** @deprecated Use the new backend-aligned tiers instead */
export type LegacyBadgeTier = "trusted" | "premium" | "new";

interface SupplierBadgeProps {
  tier?: BadgeTier | LegacyBadgeTier | string;
  size?: "sm" | "md" | "lg";
}

type BadgeConfig = { label: string; emoji: string; color: string; bg: string };

const BADGE_CONFIG: Record<string, BadgeConfig> = {
  gold:     { label: "Gold Partner",   emoji: "🥇", color: "#d97706", bg: "rgba(217,119,6,0.12)" },
  silver:   { label: "Silver Partner", emoji: "🥈", color: "#6b7280", bg: "rgba(107,114,128,0.12)" },
  bronze:   { label: "Bronze Partner", emoji: "🥉", color: "#ea580c", bg: "rgba(234,88,12,0.12)" },
  verified: { label: "Verified",       emoji: "✓",  color: "#3b82f6", bg: "rgba(59,130,246,0.12)" },
  none:     { label: "Member",         emoji: "📦", color: "#a3b3c8", bg: "rgba(163,179,200,0.10)" },
  // Legacy aliases
  trusted:  { label: "Trusted",  emoji: "🛡", color: "#38bdf8", bg: "rgba(56,189,248,0.15)" },
  premium:  { label: "Premium",  emoji: "⭐", color: "#d4af37", bg: "rgba(212,175,55,0.18)" },
  new:      { label: "New",      emoji: "🆕", color: "#a3b3c8", bg: "rgba(163,179,200,0.12)" },
};

const FONT_SIZES: Record<"sm" | "md" | "lg", number> = {
  sm: 9,
  md: 11,
  lg: 13,
};

const PADDING: Record<"sm" | "md" | "lg", { h: number; v: number; r: number }> = {
  sm: { h: 6, v: 2, r: 6 },
  md: { h: 8, v: 3, r: 8 },
  lg: { h: 10, v: 4, r: 10 },
};

export default function SupplierBadge({ tier = "none", size = "sm" }: SupplierBadgeProps) {
  const config = BADGE_CONFIG[tier] ?? BADGE_CONFIG.none;
  const p = PADDING[size];
  return (
    <View
      style={[
        styles.badge,
        {
          backgroundColor: config.bg,
          borderColor: `${config.color}50`,
          paddingHorizontal: p.h,
          paddingVertical: p.v,
          borderRadius: p.r,
        },
      ]}
    >
      <Text style={[styles.text, { color: config.color, fontSize: FONT_SIZES[size] }]}>
        {config.emoji} {config.label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    alignSelf: "flex-start",
  },
  text: {
    fontWeight: "700",
  },
});
