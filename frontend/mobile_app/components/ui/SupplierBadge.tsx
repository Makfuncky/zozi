import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";

export type BadgeTier = "gold" | "silver" | "bronze" | "verified" | "none";
export type LegacyBadgeTier = "trusted" | "premium" | "new";

interface SupplierBadgeProps {
  tier?: BadgeTier | LegacyBadgeTier | string;
  size?: "sm" | "md" | "lg";
}

type BadgeConfig = { label: string; icon: React.ComponentProps<typeof Ionicons>["name"]; color: string; bg: string };

const BADGE_CONFIG: Record<string, BadgeConfig> = {
  gold: { label: "Gold Partner", icon: "ribbon", color: "#d97706", bg: "rgba(217,119,6,0.14)" },
  silver: { label: "Silver Partner", icon: "medal", color: "#6b7280", bg: "rgba(107,114,128,0.14)" },
  bronze: { label: "Bronze Partner", icon: "medal-outline", color: "#ea580c", bg: "rgba(234,88,12,0.14)" },
  verified: { label: "Verified", icon: "checkmark-circle", color: "#3b82f6", bg: "rgba(59,130,246,0.14)" },
  none: { label: "Member", icon: "storefront-outline", color: "#6b7280", bg: "rgba(107,114,128,0.14)" },
  trusted: { label: "Trusted", icon: "shield-checkmark", color: "#38bdf8", bg: "rgba(56,189,248,0.16)" },
  premium: { label: "Premium", icon: "star", color: "#d4af37", bg: "rgba(212,175,55,0.18)" },
  new: { label: "New", icon: "sparkles", color: "#6b7280", bg: "rgba(107,114,128,0.14)" },
};

const FONT_SIZES: Record<"sm" | "md" | "lg", number> = {
  sm: 9,
  md: 11,
  lg: 13,
};

const ICON_SIZES: Record<"sm" | "md" | "lg", number> = {
  sm: 10,
  md: 12,
  lg: 14,
};

const PADDING: Record<"sm" | "md" | "lg", { h: number; v: number; r: number }> = {
  sm: { h: 6, v: 2, r: 6 },
  md: { h: 8, v: 3, r: 8 },
  lg: { h: 10, v: 4, r: 10 },
};

export default function SupplierBadge({ tier = "none", size = "sm" }: SupplierBadgeProps) {
  const { theme } = useThemeStore();
  const config = BADGE_CONFIG[tier] ?? BADGE_CONFIG.none;
  const padding = PADDING[size];
  return (
    <View
      style={[
        styles.badge,
        {
          backgroundColor: config.bg,
          borderColor: `${config.color}50`,
          paddingHorizontal: padding.h,
          paddingVertical: padding.v,
          borderRadius: padding.r,
        },
      ]}
    >
      <Ionicons name={config.icon} size={ICON_SIZES[size]} color={config.color} />
      <Text style={[styles.text, { color: config.color, fontSize: FONT_SIZES[size] }]}>
        {config.label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    borderWidth: 1,
    alignSelf: "flex-start",
  },
  text: {
    fontWeight: "700",
  },
});
