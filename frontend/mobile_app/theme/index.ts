/**
 * Mobile theme tokens derived from the shared design system.
 * Maps shared color/spacing constants to React Native StyleSheet values.
 */

import { Platform } from "react-native";
import { brand, dark, light, status, spacing, radius, fontSize, fontWeight, fontFamily, glass } from "@shared/theme";

export type ThemeMode = "dark" | "light";

export function getTheme(mode: ThemeMode) {
  const colors = mode === "light" ? light : dark;
  // Moderate scale for mobile — balanced between readability and fit.
  const SCALE = 0.92;

  function scaleNumericMap<T extends Record<string, number>>(map: T, factor: number): T {
    const out: Record<string, number> = {};
    for (const k of Object.keys(map)) {
      // preserve integer-ish values for RN points
      out[k] = Math.max(1, Math.round((map as any)[k] * factor));
    }
    return out as T;
  }

  const scaledSpacing = scaleNumericMap(spacing, SCALE);
  const scaledRadius = scaleNumericMap(radius, SCALE);
  const scaledFontSize = scaleNumericMap(fontSize, SCALE);

  // Mobile dark mode now mirrors the web_app dark palette exactly so both
  // apps share one visual language. (The previous charcoal override is removed.)
  const surfaceColors = colors;

  // Frosted-glass layer tokens — parity with @shared/glass used by web_app.
  const isDark = mode === "dark";
  const glassTokens = {
    panel: isDark ? glass.panel : "rgba(255,255,255,0.72)",
    panelStrong: isDark ? glass.solid : "rgba(255,255,255,0.86)",
    overlay: isDark ? "rgba(0,0,0,0.55)" : "rgba(15,23,42,0.28)",
    border: isDark ? glass.border : "rgba(0,0,0,0.08)",
    borderSoft: isDark ? glass.borderSoft : "rgba(0,0,0,0.06)",
    highlight: isDark ? glass.faint : "rgba(255,255,255,0.75)",
    sheen: isDark ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.55)",
  };

  return {
    mode,
    colors: {
      ...surfaceColors,
      brand: brand.primary,
      brandLight: brand.primaryLight,
      brandDark: brand.primaryDark,
      accent: brand.accent,
      accentLight: brand.accentLight,
      onBrand: colors.onBrand ?? "#ffffff",
      onAccent: colors.onAccent ?? "#ffffff",
      onWarning: colors.onWarning ?? "#1c1917",
      ...status,
      glass: glassTokens,
      processing: "#3b82f6",
      shipped: "#8b5cf6",
      picking: "#6366f1",
      neutral: "#9ca3af",
      // Quick action colors for visual distinction
      quickActionOffers: "#ef4444",
      quickActionFlash: "#f59e0b",
      quickActionWishlist: "#ec4899",
      quickActionCoupons: "#8b5cf6",
      quickActionOrders: "#3b82f6",
      quickActionChat: "#22c55e",
      // Flash sale colors
      flashSale: "#22c55e",
      flashSaleText: "#000000",
      discountTag: "#ef4444",
      discountTagText: "#ffffff",
      // Pill/active states (brand green — was off-brand coral #FF5C3A)
      pillActive: brand.primary,
      pillActiveBg: "rgba(50,205,50,0.14)",
      // Action button colors
      danger: "#ef4444",
      dangerBg: "rgba(239,68,68,0.08)",
      dangerText: "#ffffff",
      // Status background colors
      success: "#22c55e",
      successBg: "rgba(34,197,94,0.15)",
      warning: "#f59e0b",
      warningBg: "rgba(245,158,11,0.15)",
      info: "#38bdf8",
      infoBg: "rgba(56,189,248,0.15)",
      // Staff management colors
      staffGold: "#d4af37",
      staffGoldBg: "rgba(212,175,55,0.12)",
      // Status background colors (semantic aliases)
      statusSuccessBg: "rgba(34,197,94,0.15)",
      statusWarningBg: "rgba(245,158,11,0.15)",
      statusInfoBg: "rgba(56,189,248,0.15)",
      statusDangerBg: "rgba(239,68,68,0.08)",
      statusProcessingBg: "rgba(59,130,246,0.12)",
      statusShippedBg: "rgba(139,92,246,0.12)",
      statusPickingBg: "rgba(99,102,241,0.12)",
      statusPendingBg: "rgba(156,163,252,0.12)",
      // Order status colors
      statusPending: "#9ca3af",
      statusProcessing: "#3b82f6",
      statusShipped: "#8b5cf6",
      statusDelivered: "#22c55e",
      statusCancelled: "#ef4444",
      statusReturned: "#6b7280",
      statusReplacement: "#8b5cf6",
      // Notification colors
      notificationOrder: "#3b82f6",
      notificationPromotion: "#f59e0b",
      notificationSystem: "#8b5cf6",
      notificationSuccess: "#22c55e",
      notificationWarning: "#f59e0b",
      notificationError: "#ef4444",
    },
    spacing: scaledSpacing,
    radius: scaledRadius,
    fontSize: scaledFontSize,
    fontFamily,
    fontWeight,
    gradients: {
      // Exact web_app hero gradient: lime → green → yellow
      button: ["#7CFC00", "#32CD32"] as string[],
      buttonAccent: ["#FFEA00", "#FFD700"] as string[],
      // Header: pure system lime-green ramp (brandLight → brand → brandDark).
      // No gold stop so the bar reads as the canonical ZOZI lime green (#32CD32).
      header: ["#7CFC00", "#32CD32", "#228B22"] as string[],
      footer: ["#7CFC00", "#32CD32", "#228B22"] as string[],
    },
  };
}

export type AppTheme = ReturnType<typeof getTheme>;

// Shared web-only backdrop-filter for inline frosted panels (mirrors GlassCard).
// Spread into any `style` array used with a translucent `glass.panel` background.
export const glassWebFilter = Platform.select({
  web: { backdropFilter: "blur(18px) saturate(150%)" },
  default: {},
}) as import("react-native").ViewStyle;

// Default themes
export const darkTheme = getTheme("dark");
export const lightTheme = getTheme("light");

// ── Common StyleSheet helpers ─────────────────────────────────────────────────

export function makeStyles(theme: AppTheme) {
  return {
    container: {
      flex: 1,
      backgroundColor: theme.colors.surface0,
    },
    centered: {
      flex: 1,
      justifyContent: "center" as const,
      alignItems: "center" as const,
      backgroundColor: theme.colors.surface0,
    },
    surface: {
      backgroundColor: theme.colors.surface1,
      borderRadius: theme.radius.lg,
    },
    text: {
      color: theme.colors.text,
      fontSize: theme.fontSize.base,
      fontFamily: theme.fontFamily.body,
    },
    textMuted: {
      color: theme.colors.textMuted,
      fontSize: theme.fontSize.sm,
      fontFamily: theme.fontFamily.body,
    },
    textBrand: {
      color: theme.colors.brand,
      fontWeight: theme.fontWeight.semibold,
      fontFamily: theme.fontFamily.body,
    },
    title: {
      color: theme.colors.text,
      fontSize: theme.fontSize["2xl"],
      fontWeight: theme.fontWeight.bold,
      fontFamily: theme.fontFamily.heading,
    },
    subtitle: {
      color: theme.colors.textMuted,
      fontSize: theme.fontSize.sm,
      fontFamily: theme.fontFamily.body,
    },
    row: {
      flexDirection: "row" as const,
      alignItems: "center" as const,
    },
    rowBetween: {
      flexDirection: "row" as const,
      alignItems: "center" as const,
      justifyContent: "space-between" as const,
    },
    btnPrimary: {
      backgroundColor: theme.colors.brand,
      borderRadius: theme.radius.xl,
      paddingVertical: theme.spacing.md,
      paddingHorizontal: theme.spacing.xl,
      alignItems: "center" as const,
    },
    btnPrimaryText: {
      color: "#ffffff",
      fontWeight: theme.fontWeight.semibold,
      fontSize: theme.fontSize.base,
    },
    btnSecondary: {
      borderWidth: 1,
      borderColor: theme.colors.brand,
      borderRadius: theme.radius.xl,
      paddingVertical: theme.spacing.md,
      paddingHorizontal: theme.spacing.xl,
      alignItems: "center" as const,
    },
    btnSecondaryText: {
      color: theme.colors.brand,
      fontWeight: theme.fontWeight.semibold,
      fontSize: theme.fontSize.base,
    },
    input: {
      backgroundColor: theme.colors.surface2,
      color: theme.colors.text,
      borderRadius: theme.radius.md,
      borderWidth: 1,
      borderColor: theme.colors.border,
      paddingHorizontal: theme.spacing.md,
      paddingVertical: theme.spacing.sm + 4,
      fontSize: theme.fontSize.base,
      fontFamily: theme.fontFamily.body,
    },
    divider: {
      height: 1,
      backgroundColor: theme.colors.border,
    },
    card: {
      backgroundColor: theme.colors.surface1,
      borderRadius: theme.radius.xl,
      borderWidth: 1,
      borderColor: theme.colors.border,
      padding: theme.spacing.lg,
      ...Platform.select({
        web: { boxShadow: "0px 6px 14px rgba(0,0,0,0.25)" },
        default: {
          shadowColor: "#000",
          shadowOffset: { width: 0, height: 6 },
          shadowOpacity: 0.25,
          shadowRadius: 14,
          elevation: 8,
        },
      }),
    },
    // ── Glassy / glow helpers (web parity) ────────────────────────────────
    glassCard: {
      backgroundColor: theme.colors.glass.panel,
      borderRadius: theme.radius.xl,
      borderWidth: 1,
      borderColor: theme.colors.glass.border,
      ...Platform.select({
        web: { backdropFilter: "blur(18px) saturate(150%)", boxShadow: "0 8px 26px rgba(0,0,0,0.38), inset 0 1px 0 rgba(255,255,255,0.10)" },
        default: {
          shadowColor: "#000",
          shadowOffset: { width: 0, height: 8 },
          shadowOpacity: 0.32,
          shadowRadius: 20,
          elevation: 10,
        },
      }),
    },
    glassInput: {
      backgroundColor: theme.colors.glass.panel,
      borderRadius: theme.radius.lg,
      borderWidth: 1,
      borderColor: theme.colors.glass.border,
      paddingHorizontal: theme.spacing.md,
      paddingVertical: theme.spacing.sm + 4,
      color: theme.colors.text,
      fontSize: theme.fontSize.base,
      fontFamily: theme.fontFamily.body,
    },
    glassPill: {
      borderRadius: theme.radius.full,
      paddingHorizontal: theme.spacing.md,
      paddingVertical: theme.spacing.sm,
      borderWidth: 1,
      borderColor: theme.colors.glass.border,
      backgroundColor: theme.colors.glass.panel,
    },
    glassHeader: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      paddingHorizontal: theme.spacing.lg,
      paddingVertical: theme.spacing.sm + 4,
      backgroundColor: theme.colors.glass.panelStrong,
      borderBottomWidth: 1,
      borderBottomColor: theme.colors.glass.border,
      ...Platform.select({
        web: { backdropFilter: "blur(18px) saturate(150%)", boxShadow: "0 6px 20px rgba(0,0,0,0.30)" },
        default: {
          shadowColor: "#000",
          shadowOffset: { width: 0, height: 4 },
          shadowOpacity: 0.3,
          shadowRadius: 12,
          elevation: 8,
        },
      }),
    },
    glowPrimary: {
      ...Platform.select({
        web: { boxShadow: "0 8px 26px rgba(50,205,50,0.38)" },
        default: {
          shadowColor: brand.primary,
          shadowOffset: { width: 0, height: 6 },
          shadowOpacity: 0.45,
          shadowRadius: 16,
          elevation: 8,
        },
      }),
    },
    glowAccent: {
      ...Platform.select({
        web: { boxShadow: "0 8px 26px rgba(255,215,0,0.38)" },
        default: {
          shadowColor: brand.accent,
          shadowOffset: { width: 0, height: 6 },
          shadowOpacity: 0.4,
          shadowRadius: 16,
          elevation: 8,
        },
      }),
    },
    section: {
      paddingHorizontal: theme.spacing.lg,
      paddingTop: theme.spacing.md,
      paddingBottom: theme.spacing.md,
      gap: theme.spacing.sm,
    },
    sectionHeader: {
      flexDirection: "row" as const,
      alignItems: "center" as const,
      justifyContent: "space-between" as const,
      paddingHorizontal: theme.spacing.lg,
      marginBottom: theme.spacing.xs,
    },
    sectionTitle: {
      color: theme.colors.text,
      fontSize: theme.fontSize.lg,
      fontWeight: theme.fontWeight.bold,
      fontFamily: theme.fontFamily.heading,
    },
    sectionIconBg: {
      width: 28,
      height: 28,
      borderRadius: theme.radius.sm,
      alignItems: "center" as const,
      justifyContent: "center" as const,
    },
    horizontalList: {
      paddingHorizontal: theme.spacing.lg,
      gap: theme.spacing.md,
    },
    badge: {
      borderRadius: theme.radius.full,
      paddingHorizontal: theme.spacing.sm,
      paddingVertical: theme.spacing.xs / 2,
      alignItems: "center" as const,
      justifyContent: "center" as const,
    },
    badgeText: {
      color: "#ffffff",
      fontSize: theme.fontSize.xs,
      fontWeight: theme.fontWeight.bold,
    },
    chip: {
      borderRadius: theme.radius.full,
      paddingHorizontal: theme.spacing.md,
      paddingVertical: theme.spacing.sm,
      borderWidth: 1,
      borderColor: theme.colors.border,
      backgroundColor: theme.colors.surface1,
    },
    chipActive: {
      borderRadius: theme.radius.full,
      paddingHorizontal: theme.spacing.md,
      paddingVertical: theme.spacing.sm,
      borderWidth: 1,
      borderColor: theme.colors.brand,
      backgroundColor: theme.colors.brand,
    },
    cardImage: {
      width: "100%",
      aspectRatio: 1,
      borderRadius: theme.radius.lg,
      backgroundColor: theme.colors.surface0,
    },
    placeholder: {
      width: "100%",
      aspectRatio: 1,
      borderRadius: theme.radius.lg,
      backgroundColor: theme.colors.surface0,
      alignItems: "center" as const,
      justifyContent: "center" as const,
    },
  };
}

// ── Semantic status colors ──────────────────────────────────────────────────
// Central mapping so screens stop defining local `STATUS_COLORS` hex maps.
// Returns a foreground color + tinted background/border derived from theme tokens.

export interface StatusColorSet {
  color: string;
  bg: string;
  border: string;
}

export function getStatusColor(status: string | null | undefined, theme: AppTheme): StatusColorSet {
  const key = String(status ?? "")
    .toLowerCase()
    .replace(/\s+/g, "_");

  const map: Record<string, StatusColorSet> = {
    pending: { color: theme.colors.statusPending, bg: theme.colors.statusPendingBg, border: theme.colors.statusPendingBg },
    processing: { color: theme.colors.statusProcessing, bg: theme.colors.statusProcessingBg, border: theme.colors.statusProcessingBg },
    picking: { color: theme.colors.statusProcessing, bg: theme.colors.statusProcessingBg, border: theme.colors.statusProcessingBg },
    shipped: { color: theme.colors.statusShipped, bg: theme.colors.statusShippedBg, border: theme.colors.statusShippedBg },
    in_transit: { color: theme.colors.statusShipped, bg: theme.colors.statusShippedBg, border: theme.colors.statusShippedBg },
    delivered: { color: theme.colors.statusDelivered, bg: theme.colors.statusSuccessBg, border: theme.colors.statusSuccessBg },
    completed: { color: theme.colors.statusDelivered, bg: theme.colors.statusSuccessBg, border: theme.colors.statusSuccessBg },
    paid: { color: theme.colors.statusDelivered, bg: theme.colors.statusSuccessBg, border: theme.colors.statusSuccessBg },
    cancelled: { color: theme.colors.statusCancelled, bg: theme.colors.statusDangerBg, border: theme.colors.statusDangerBg },
    canceled: { color: theme.colors.statusCancelled, bg: theme.colors.statusDangerBg, border: theme.colors.statusDangerBg },
    returned: { color: theme.colors.statusReturned, bg: theme.colors.statusWarningBg, border: theme.colors.statusWarningBg },
    replacement: { color: theme.colors.statusShipped, bg: theme.colors.statusShippedBg, border: theme.colors.statusShippedBg },
    refunded: { color: theme.colors.statusShipped, bg: theme.colors.statusShippedBg, border: theme.colors.statusShippedBg },
    approved: { color: theme.colors.statusDelivered, bg: theme.colors.statusSuccessBg, border: theme.colors.statusSuccessBg },
    verified: { color: theme.colors.statusDelivered, bg: theme.colors.statusSuccessBg, border: theme.colors.statusSuccessBg },
    rejected: { color: theme.colors.statusCancelled, bg: theme.colors.statusDangerBg, border: theme.colors.statusDangerBg },
    failed: { color: theme.colors.statusCancelled, bg: theme.colors.statusDangerBg, border: theme.colors.statusDangerBg },
    active: { color: theme.colors.statusDelivered, bg: theme.colors.statusSuccessBg, border: theme.colors.statusSuccessBg },
    suspended: { color: theme.colors.statusCancelled, bg: theme.colors.statusDangerBg, border: theme.colors.statusDangerBg },
    open: { color: theme.colors.statusProcessing, bg: theme.colors.statusProcessingBg, border: theme.colors.statusProcessingBg },
    resolved: { color: theme.colors.statusDelivered, bg: theme.colors.statusSuccessBg, border: theme.colors.statusSuccessBg },
    closed: { color: theme.colors.textMuted, bg: theme.colors.statusPendingBg, border: theme.colors.statusPendingBg },
    warning: { color: theme.colors.warning, bg: theme.colors.statusWarningBg, border: theme.colors.statusWarningBg },
    info: { color: theme.colors.info, bg: theme.colors.statusInfoBg, border: theme.colors.statusInfoBg },
    success: { color: theme.colors.success, bg: theme.colors.statusSuccessBg, border: theme.colors.statusSuccessBg },
    danger: { color: theme.colors.danger, bg: theme.colors.statusDangerBg, border: theme.colors.statusDangerBg },
  };

  return (
    map[key] ?? {
      color: theme.colors.textMuted,
      bg: theme.colors.statusPendingBg,
      border: theme.colors.statusPendingBg,
    }
  );
}
