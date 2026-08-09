import React from "react";

/** Badge tiers matching backend badge_level values */
export type BadgeTier = "gold" | "silver" | "bronze" | "verified" | "none";

/** @deprecated Use the new backend-aligned tiers instead */
export type LegacyBadgeTier = "trusted" | "premium" | "new";

interface SupplierBadgeProps {
  tier?: BadgeTier | LegacyBadgeTier | string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

type BadgeConfig = { label: string; emoji: string; color: string; bg: string };

const BADGE_CONFIG: Record<string, BadgeConfig> = {
  gold:     { label: "Gold Partner",   emoji: "🥇", color: "#d97706", bg: "rgba(217,119,6,0.12)" },
  silver:   { label: "Silver Partner", emoji: "🥈", color: "#6b7280", bg: "rgba(107,114,128,0.12)" },
  bronze:   { label: "Bronze Partner", emoji: "🥉", color: "#ea580c", bg: "rgba(234,88,12,0.12)" },
  verified: { label: "Verified",       emoji: "✓",  color: "#3b82f6", bg: "rgba(59,130,246,0.12)" },
  none:     { label: "Member",         emoji: "📦", color: "#a3b3c8", bg: "rgba(163,179,200,0.10)" },
  // Legacy aliases for backward compatibility
  trusted:  { label: "Trusted",        emoji: "🛡", color: "#38bdf8", bg: "rgba(56,189,248,0.12)" },
  premium:  { label: "Premium",        emoji: "⭐", color: "#d4af37", bg: "rgba(212,175,55,0.15)" },
  new:      { label: "New Supplier",   emoji: "🆕", color: "#a3b3c8", bg: "rgba(163,179,200,0.12)" },
};

const SIZE_STYLES: Record<"sm" | "md" | "lg", React.CSSProperties> = {
  sm: { fontSize: "10px", padding: "2px 8px", borderRadius: "9999px" },
  md: { fontSize: "11px", padding: "3px 10px", borderRadius: "9999px" },
  lg: { fontSize: "13px", padding: "4px 12px", borderRadius: "9999px" },
};

export default function SupplierBadge({
  tier = "none",
  size = "sm",
  className = "",
}: SupplierBadgeProps) {
  const config = BADGE_CONFIG[tier] ?? BADGE_CONFIG.none;
  return (
    <span
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        fontWeight: 700,
        color: config.color,
        backgroundColor: config.bg,
        border: `1px solid ${config.color}30`,
        userSelect: "none",
        letterSpacing: "0.02em",
        ...SIZE_STYLES[size],
      }}
    >
      {config.emoji} {config.label}
    </span>
  );
}
