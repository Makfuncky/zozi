/**
 * ZOZI Design Tokens — reference for component development.
 */
export const tokens = {
  colors: {
    brand: "var(--color-brand)",
    brandLight: "var(--color-brand-light)",
    brandDark: "var(--color-brand-dark)",
    accent: "var(--color-accent)",
    surface0: "var(--color-surface-0)",
    surface1: "var(--color-surface-1)",
    surface2: "var(--color-surface-2)",
    surface3: "var(--color-surface-3)",
    border: "var(--color-border)",
    text: "var(--color-text)",
    textMuted: "var(--color-text-muted)",
    success: "var(--color-success)",
    danger: "var(--color-danger)",
    warning: "var(--color-warning)",
    info: "var(--color-info)",
  },
  radius: {
    sm: "var(--zozi-radius-sm)",
    md: "var(--zozi-radius-md)",
    lg: "var(--zozi-radius-lg)",
    xl: "var(--zozi-radius-xl)",
    "2xl": "var(--zozi-radius-2xl)",
    pill: "var(--zozi-radius-pill)",
  },
  elevation: {
    sm: "var(--zozi-elevation-sm)",
    md: "var(--zozi-elevation-md)",
    lg: "var(--zozi-elevation-lg)",
    xl: "var(--zozi-elevation-xl)",
  },
  duration: {
    fast: "var(--zozi-duration-fast)",
    base: "var(--zozi-duration-base)",
    normal: "var(--zozi-duration-normal)",
    slow: "var(--zozi-duration-slow)",
    slower: "var(--zozi-duration-slower)",
    slowest: "var(--zozi-duration-slowest)",
  },
} as const;
