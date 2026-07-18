/**
 * Centralized status → theme-chip class mapping for all panels.
 * Import and use instead of defining local STATUS_COLORS in each page.
 */

/** Order / shipment status → theme chip class */
export const ORDER_STATUS_CHIP: Record<string, string> = {
  pending:     "theme-chip-warning",
  confirmed:   "theme-chip-info",
  processing:  "theme-chip-info",
  prepared:    "theme-chip-brand",
  picking_up:  "theme-chip-brand",
  shipped:     "theme-chip-brand",
  in_transit:  "theme-chip-warning",
  delivered:   "theme-chip-success",
  cancelled:   "theme-chip-danger",
  failed:      "theme-chip-danger",
  returned:    "theme-chip-danger",
  refunded:    "theme-chip-muted",
};

/** Product verification status → theme chip class */
export const PRODUCT_STATUS_CHIP: Record<string, string> = {
  approved:  "theme-chip-success",
  pending:   "theme-chip-warning",
  rejected:  "theme-chip-danger",
};

/** Return / refund status → theme chip class */
export const RETURN_STATUS_CHIP: Record<string, string> = {
  pending:   "theme-chip-warning",
  approved:  "theme-chip-info",
  rejected:  "theme-chip-danger",
  completed: "theme-chip-success",
};

export type PartnerBadgeLevel = "gold" | "silver" | "bronze" | "verified" | "none";

export type PartnerBadgeStyle = {
  level: PartnerBadgeLevel;
  label: string;
  shortLabel: string;
  emoji: string;
  toneClass: string;
};

export const PARTNER_BADGE_STYLE: Record<PartnerBadgeLevel, PartnerBadgeStyle> = {
  gold: {
    level: "gold",
    label: "Gold Partner",
    shortLabel: "Gold partner",
    emoji: "🥇",
    toneClass: "border-accent/30 bg-accent/15 text-accent",
  },
  silver: {
    level: "silver",
    label: "Silver Partner",
    shortLabel: "Silver partner",
    emoji: "🥈",
    toneClass: "border-border bg-surface-2 text-text-muted",
  },
  bronze: {
    level: "bronze",
    label: "Bronze Partner",
    shortLabel: "Bronze partner",
    emoji: "🥉",
    toneClass: "border-warning/30 bg-warning/15 text-warning",
  },
  verified: {
    level: "verified",
    label: "Verified",
    shortLabel: "Verified supplier",
    emoji: "✓",
    toneClass: "border-info/30 bg-info/15 text-info",
  },
  none: {
    level: "none",
    label: "Member",
    shortLabel: "Supplier storefront",
    emoji: "📦",
    toneClass: "border-border bg-surface-2 text-text-muted",
  },
};

export function getPartnerBadgeStyle(level: string | null | undefined): PartnerBadgeStyle {
  const normalized = (level ?? "none").toLowerCase() as PartnerBadgeLevel;
  return PARTNER_BADGE_STYLE[normalized] ?? PARTNER_BADGE_STYLE.none;
}

/** Generic fallback for unknown statuses */
export function getStatusChip(status: string | null | undefined, map: Record<string, string> = ORDER_STATUS_CHIP): string {
  if (!status) return "theme-chip-muted";
  return map[status] ?? "theme-chip-muted";
}
