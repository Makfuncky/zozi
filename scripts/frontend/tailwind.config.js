/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./web_app/src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./web_app/src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./web_app/src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./mobile_app/src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./mobile_app/src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./mobile_app/src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./shared/src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      /* -- Brand Palette -------------------------------------------- */
      colors: {
        primary: "var(--color-brand)",
        "primary-light": "var(--color-brand-light)",
        "primary-dark": "var(--color-brand-dark)",
        accent: "var(--color-accent)",
        "accent-light": "var(--color-accent-light)",
        success: "var(--color-success)",
        danger: "var(--color-danger)",
        warning: "var(--color-warning)",
        info: "var(--color-info)",
        "on-brand": "var(--color-on-brand)",
        "on-accent": "var(--color-on-accent)",
        "on-warning": "var(--color-on-warning)",
        surface: {
          base: "var(--color-surface-0)",
          1: "var(--color-surface-1)",
          2: "var(--color-surface-2)",
          3: "var(--color-surface-3)",
        },
        text: "var(--color-text)",
        "text-muted": "var(--color-text-muted)",
        "text-faint": "var(--color-text-faint)",
        border: "var(--color-border)",
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
        outfit: ["var(--font-display)", "Fraunces", "serif"],
        jakarta: ["var(--font-body)", "Sora", "sans-serif"],
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

      /* -- Max width ------------------------------------------------ */
      maxWidth: {
        "8xl": "88rem",
        "9xl": "96rem",
        "10xl": "120rem",
        "11xl": "140rem",
      },

      minHeight: {
        12: "3rem",
        16: "4rem",
        32: "8rem",
      },
    },
  },
  plugins: [],
};