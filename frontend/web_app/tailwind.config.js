/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      /* -- Brand Palette -------------------------------------------- */
      colors: {
        primary: "rgb(var(--color-brand-rgb) / <alpha-value>)",
        "primary-light": "var(--color-brand-light)",
        "primary-dark": "var(--color-brand-dark)",
        accent: "rgb(var(--color-accent-rgb) / <alpha-value>)",
        "accent-light": "var(--color-accent-light)",
        success: "rgb(var(--color-success-rgb) / <alpha-value>)",
        danger: "rgb(var(--color-danger-rgb) / <alpha-value>)",
        error: "rgb(var(--color-danger-rgb) / <alpha-value>)",
        "on-error": "var(--color-on-brand)",
        warning: "rgb(var(--color-warning-rgb) / <alpha-value>)",
        info: "rgb(var(--color-info-rgb) / <alpha-value>)",
        "on-brand": "var(--color-on-brand)",
        "primary-foreground": "var(--color-on-brand)",
        "on-accent": "var(--color-on-accent)",
        "on-warning": "var(--color-on-warning)",
        surface: {
          DEFAULT: "rgb(var(--color-surface-1-rgb) / <alpha-value>)",
          base: "var(--color-surface-0)",
          1: "rgb(var(--color-surface-1-rgb) / <alpha-value>)",
          2: "rgb(var(--color-surface-2-rgb) / <alpha-value>)",
          3: "rgb(var(--color-surface-3-rgb) / <alpha-value>)",
          hover: "rgb(var(--color-surface-2-rgb) / <alpha-value>)",
        },
        background: "rgb(var(--color-background-rgb) / <alpha-value>)",
        muted: "rgb(var(--color-surface-2-rgb) / <alpha-value>)",
        "muted-foreground": "var(--color-text-muted)",
        text: "rgb(var(--color-text-rgb) / <alpha-value>)",
        "text-muted": "rgb(var(--color-text-muted-rgb) / <alpha-value>)",
        "text-faint": "rgb(var(--color-text-faint-rgb) / <alpha-value>)",
        border: "rgb(var(--color-border-rgb) / <alpha-value>)",
        "border-light": "var(--color-border-light)",

        /* Glass / frosted-layer tokens — mirrors CSS color-mix vars */
        "glass-base":         "var(--color-glass-base)",
        "glass-mid":          "var(--color-glass-mid)",
        "glass-hi":           "var(--color-glass-hi)",
        "glass-solid":        "var(--color-glass-solid)",
        "glass-panel":        "var(--color-glass-panel)",
        "glass-faint":        "var(--color-glass-faint)",
        "glass-panel-hover":  "var(--color-glass-panel-hover)",
        "glass-border":       "var(--color-glass-border)",
        "glass-border-mid":   "var(--color-glass-border-mid)",
        "glass-border-soft":  "var(--color-glass-border-soft)",

        /* Legacy aliases (still supported) */
        charcoal: "#0f172a",
        "zozi-primary": "var(--color-brand)",
        "zozi-primary-light": "var(--color-brand-light)",
        "zozi-primary-dark": "var(--color-brand-dark)",
        "zozi-secondary": "var(--color-accent)",
        "zozi-secondary-light": "var(--color-accent-light)",
        "zozi-secondary-dark": "var(--color-accent-dark)",
        "zozi-accent": "var(--color-accent)",
        "zozi-highlight": "var(--color-danger)",
        "zozi-neutral": "var(--color-white)",
        "zozi-neutral-light": "var(--color-text-muted)",
      },

      /* -- Typography ----------------------------------------------- */
      fontFamily: {
        heading: ["var(--font-display)", "Fraunces", "serif"],
        display: ["var(--font-display)", "Fraunces", "serif"],
        body: ["var(--font-body)", "Sora", "sans-serif"],
        sans: ["var(--font-body)", "Sora", "system-ui", "sans-serif"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "1rem" }],
        xs: ["0.75rem", { lineHeight: "1.125rem" }],
        sm: ["0.875rem", { lineHeight: "1.375rem" }],
        base: ["1rem", { lineHeight: "1.625rem" }],
        lg: ["1.125rem", { lineHeight: "1.75rem" }],
        xl: ["1.25rem", { lineHeight: "1.875rem" }],
        "2xl": ["1.5rem", { lineHeight: "2rem" }],
        "3xl": ["1.875rem", { lineHeight: "2.25rem" }],
        "4xl": ["2.25rem", { lineHeight: "2.5rem" }],
        "5xl": ["3rem", { lineHeight: "1.15" }],
        "6xl": ["3.75rem", { lineHeight: "1.1" }],
        display: ["clamp(2.5rem,6vw,4.5rem)", { lineHeight: "1.1" }],
      },

      /* -- Spacing -------------------------------------------------- */
      spacing: {
        4.5: "1.125rem",
        13: "3.25rem",
        15: "3.75rem",
        18: "4.5rem",
        22: "5.5rem",
        30: "7.5rem",
        88: "22rem",
        128: "32rem",
      },

      /* -- Border Radius -------------------------------------------- */
      borderRadius: {
        sm: "0.375rem",
        md: "0.5rem",
        lg: "0.75rem",
        xl: "1rem",
        "2xl": "1.25rem",
        "3xl": "1.5rem",
        "4xl": "2rem",
        pill: "9999px",
      },

      /* -- Shadows -------------------------------------------------- */
      boxShadow: {
        "card-sm": "0 1px 3px rgb(0 0 0 / 0.06), 0 1px 2px rgb(0 0 0 / 0.04)",
        card: "0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.05)",
        "card-lg": "0 10px 25px -5px rgb(0 0 0 / 0.08), 0 8px 10px -6px rgb(0 0 0 / 0.04)",
        "card-xl": "0 20px 40px -10px rgb(0 0 0 / 0.1)",
        "glow-primary": "0 0 20px rgb(50 205 50 / 0.22)",
        "glow-accent": "0 0 20px rgb(255 215 0 / 0.20)",
        "glow-primary-lg": "0 8px 30px rgb(50 205 50 / 0.28)",
        glass: "0 8px 32px rgb(0 0 0 / 0.08), inset 0 1px 0 rgb(255 255 255 / 0.06)",
        "btn-primary": "0 4px 14px rgb(50 205 50 / 0.22)",
        "btn-primary-hover": "0 8px 24px rgb(50 205 50 / 0.32)",
        focus: "0 0 0 3px rgb(50 205 50 / 0.18)",
      },

      /* -- Gradients ------------------------------------------------ */
      backgroundImage: {
        "gradient-primary": "var(--gradient-banner)",
        "gradient-accent": "var(--gradient-banner-alt)",
        "gradient-hero": "var(--gradient-hero)",
        "gradient-logo": "var(--gradient-logo)",
        "gradient-card": "var(--gradient-card)",
        "gradient-radial": "radial-gradient(ellipse at center, var(--tw-gradient-stops))",
        "gradient-text": "var(--gradient-brand-text)",
        "gradient-logo-text": "var(--gradient-logo-text)",
      },

      /* -- Transitions ---------------------------------------------- */
      transitionTimingFunction: {
        smooth: "cubic-bezier(0.4, 0, 0.2, 1)",
        spring: "cubic-bezier(0.22, 1, 0.36, 1)",
        "expo-out": "cubic-bezier(0.16, 1, 0.3, 1)",
      },
      transitionDuration: {
        250: "250ms",
        350: "350ms",
        400: "400ms",
      },

      /* -- Animations ----------------------------------------------- */
      animation: {
        ticker: "ticker 60s linear infinite",
        float: "float 6s ease-in-out infinite",
        shimmer: "shimmer 2s infinite",
        "fade-in": "fadeIn 0.4s ease-out",
        "slide-up": "slideUp 0.5s ease-out",
        "scale-in": "scaleIn 0.3s ease-out",
        "spin-slow": "spin 8s linear infinite",
      },
      keyframes: {
        ticker: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-12px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
        slideUp: {
          from: { transform: "translateY(12px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        scaleIn: {
          from: { transform: "scale(0.95)", opacity: "0" },
          to: { transform: "scale(1)", opacity: "1" },
        },
      },

      /* -- Backdrop blur -------------------------------------------- */
      backdropBlur: {
        xs: "2px",
        sm: "4px",
        md: "8px",
        lg: "16px",
        xl: "24px",
      },

      /* -- Z-index -------------------------------------------------- */
      zIndex: {
        60: "60",
        70: "70",
        80: "80",
        90: "90",
        100: "100",
        1200: "1200",
        1201: "1201",
      },

      /* -- Ring (focus) --------------------------------------------- */
      ring: {
        brand: "var(--color-brand)",
      },

      /* -- Max width ------------------------------------------------ */
      maxWidth: {
        "8xl": "88rem",
        "9xl": "96rem",
        "10xl": "120rem",
        "11xl": "140rem",
        450: "112.5rem",
      },

      minHeight: {
        12: "3rem",
        16: "4rem",
        32: "8rem",
      },
    },
  },
  safelist: [
    "bg-accent/10", "bg-accent/20", "bg-accent/30", "bg-accent/5", "bg-accent/50", "bg-accent/70",
    "bg-amber/10", "bg-amber/20", "bg-amber/5",
    "bg-black/10", "bg-black/20", "bg-black/30", "bg-black/40", "bg-black/5", "bg-black/50", "bg-black/60", "bg-black/70", "bg-black/80",
    "bg-border/10", "bg-border/20", "bg-border/30", "bg-border/40", "bg-border/50", "bg-border/60", "bg-border/70", "bg-border/80",
    "bg-brand/10", "bg-brand/20", "bg-brand/40", "bg-brand/5",
    "bg-danger/10", "bg-danger/20", "bg-danger/30", "bg-danger/40", "bg-danger/5", "bg-danger/50", "bg-danger/60", "bg-danger/70", "bg-danger/80", "bg-danger/90",
    "bg-error/10", "bg-error/20", "bg-error/30", "bg-error/5",
    "bg-info/10", "bg-info/20", "bg-info/30", "bg-info/40", "bg-info/5", "bg-info/90",
    "bg-primary/10", "bg-primary/20", "bg-primary/30", "bg-primary/40", "bg-primary/5", "bg-primary/50", "bg-primary/60", "bg-primary/70", "bg-primary/80", "bg-primary/90",
    "bg-success/10", "bg-success/20", "bg-success/30", "bg-success/40", "bg-success/5", "bg-success/80",
    "bg-surface/60",
    "bg-text-faint/10", "bg-text-faint/20", "bg-text-faint/40", "bg-text-faint/50",
    "bg-warning/10", "bg-warning/20", "bg-warning/30", "bg-warning/40", "bg-warning/5", "bg-warning/80", "bg-warning/90",
    "bg-white/10", "bg-white/20", "bg-white/30", "bg-white/5", "bg-white/50", "bg-white/60", "bg-white/70", "bg-white/80", "bg-white/90",
    "border-accent/10", "border-accent/20", "border-accent/30", "border-accent/5", "border-accent/50", "border-accent/70",
    "border-amber/10", "border-amber/20", "border-amber/5",
    "border-black/10", "border-black/20", "border-black/30", "border-black/40", "border-black/5", "border-black/50", "border-black/60", "border-black/70", "border-black/80",
    "border-border/10", "border-border/20", "border-border/30", "border-border/40", "border-border/50", "border-border/60", "border-border/70", "border-border/80",
    "border-brand/10", "border-brand/20", "border-brand/40", "border-brand/5",
    "border-current/20",
    "border-danger/10", "border-danger/20", "border-danger/30", "border-danger/40", "border-danger/5", "border-danger/50", "border-danger/60", "border-danger/70", "border-danger/80", "border-danger/90",
    "border-error/10", "border-error/20", "border-error/30", "border-error/5",
    "border-glass-border/30",
    "border-info/10", "border-info/20", "border-info/30", "border-info/40", "border-info/5", "border-info/90",
    "border-on-brand/30",
    "border-primary/10", "border-primary/20", "border-primary/30", "border-primary/40", "border-primary/5", "border-primary/50", "border-primary/60", "border-primary/70", "border-primary/80", "border-primary/90",
    "border-success/10", "border-success/20", "border-success/30", "border-success/40", "border-success/5", "border-success/80",
    "border-warning/10", "border-warning/20", "border-warning/30", "border-warning/40", "border-warning/5", "border-warning/80", "border-warning/90",
    "border-white/10", "border-white/20", "border-white/30", "border-white/5", "border-white/50", "border-white/60", "border-white/70", "border-white/80", "border-white/90",
    "divide-border/10", "divide-border/20", "divide-border/30", "divide-border/40", "divide-border/50", "divide-border/60", "divide-border/70", "divide-border/80",
    "from-primary/10", "from-primary/20", "from-primary/30", "from-primary/40", "from-primary/5", "from-primary/50", "from-primary/60", "from-primary/70", "from-primary/80", "from-primary/90",
    "from-success/10", "from-success/20", "from-success/30", "from-success/40", "from-success/5", "from-success/80",
    "ring-black/10", "ring-black/20", "ring-black/30", "ring-black/40", "ring-black/5", "ring-black/50", "ring-black/60", "ring-black/70", "ring-black/80",
    "ring-border/10", "ring-border/20", "ring-border/30", "ring-border/40", "ring-border/50", "ring-border/60", "ring-border/70", "ring-border/80",
    "ring-danger/10", "ring-danger/20", "ring-danger/30", "ring-danger/40", "ring-danger/5", "ring-danger/50", "ring-danger/60", "ring-danger/70", "ring-danger/80", "ring-danger/90",
    "ring-primary/10", "ring-primary/20", "ring-primary/30", "ring-primary/40", "ring-primary/5", "ring-primary/50", "ring-primary/60", "ring-primary/70", "ring-primary/80", "ring-primary/90",
    "shadow-black/10", "shadow-black/20", "shadow-black/30", "shadow-black/40", "shadow-black/5", "shadow-black/50", "shadow-black/60", "shadow-black/70", "shadow-black/80",
    "shadow-danger/10", "shadow-danger/20", "shadow-danger/30", "shadow-danger/40", "shadow-danger/5", "shadow-danger/50", "shadow-danger/60", "shadow-danger/70", "shadow-danger/80", "shadow-danger/90",
    "shadow-info/10", "shadow-info/20", "shadow-info/30", "shadow-info/40", "shadow-info/5", "shadow-info/90",
    "shadow-primary/10", "shadow-primary/20", "shadow-primary/30", "shadow-primary/40", "shadow-primary/5", "shadow-primary/50", "shadow-primary/60", "shadow-primary/70", "shadow-primary/80", "shadow-primary/90",
    "shadow-success/10", "shadow-success/20", "shadow-success/30", "shadow-success/40", "shadow-success/5", "shadow-success/80",
    "shadow-warning/10", "shadow-warning/20", "shadow-warning/30", "shadow-warning/40", "shadow-warning/5", "shadow-warning/80", "shadow-warning/90",
    "text-accent/10", "text-accent/20", "text-accent/30", "text-accent/5", "text-accent/50", "text-accent/70",
    "text-brand/10", "text-brand/20", "text-brand/40", "text-brand/5",
    "text-danger/10", "text-danger/20", "text-danger/30", "text-danger/40", "text-danger/5", "text-danger/50", "text-danger/60", "text-danger/70", "text-danger/80", "text-danger/90",
    "text-primary/10", "text-primary/20", "text-primary/30", "text-primary/40", "text-primary/5", "text-primary/50", "text-primary/60", "text-primary/70", "text-primary/80", "text-primary/90",
    "text-text-faint/10", "text-text-faint/20", "text-text-faint/40", "text-text-faint/50",
    "text-warning/10", "text-warning/20", "text-warning/30", "text-warning/40", "text-warning/5", "text-warning/80", "text-warning/90",
    "text-white/10", "text-white/20", "text-white/30", "text-white/5", "text-white/50", "text-white/60", "text-white/70", "text-white/80", "text-white/90",
    "to-accent/10", "to-accent/20", "to-accent/30", "to-accent/5", "to-accent/50", "to-accent/70",
    "to-brand/10", "to-brand/20", "to-brand/40", "to-brand/5",
    "to-primary/10", "to-primary/20", "to-primary/30", "to-primary/40", "to-primary/5", "to-primary/50", "to-primary/60", "to-primary/70", "to-primary/80", "to-primary/90",
    "to-success/10", "to-success/20", "to-success/30", "to-success/40", "to-success/5", "to-success/80",
    "via-accent/10", "via-accent/20", "via-accent/30", "via-accent/5", "via-accent/50", "via-accent/70",
  ],
  plugins: [],
};