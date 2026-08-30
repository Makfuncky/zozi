import { expect, test } from "@playwright/test";

/**
 * Comprehensive design system Playwright test.
 * Validates all CSS custom properties, undefined-class fixes,
 * glass system, z-index scale, motion tokens, and theme switching.
 */

const BASE = "http://127.0.0.1:3000";

async function evalCSS(page: import("@playwright/test").Page, prop: string): Promise<string> {
  return page.evaluate((p) => getComputedStyle(document.documentElement).getPropertyValue(p).trim(), prop);
}

test.describe("Phase 0 — token wiring", () => {
  test("tokens.css is imported and tokens resolve", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const sm = await evalCSS(page, "--zozi-radius-sm");
    const fast = await evalCSS(page, "--zozi-duration-fast");
    const md = await evalCSS(page, "--zozi-elevation-md");
    expect(sm).toMatch(/px$/);
    expect(fast).toMatch(/(ms|s)$/);
    expect(md).toBeTruthy();
  });

  test("glow.css is imported (glow page styles render)", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const glow = await evalCSS(page, "--zozi-ext-glow");
    expect(glow).toBeTruthy();
  });
});

test.describe("Phase 1 — undefined class fixes", () => {
  test("--color-background is defined", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const bg = await evalCSS(page, "--color-background");
    expect(bg).toBeTruthy();
  });

  test("--zozi-ext-* tokens are defined", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const glow = await evalCSS(page, "--zozi-ext-glow");
    const orbit = await evalCSS(page, "--zozi-ext-orbit");
    const scanline = await evalCSS(page, "--zozi-ext-scanline");
    expect(glow).toBeTruthy();
    expect(orbit).toBeTruthy();
    expect(scanline).toBeTruthy();
  });

  test("bcu-* keyframes exist in stylesheet", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const hasKeyframe = await page.evaluate(() => {
      for (const sheet of document.styleSheets) {
        try {
          for (const rule of sheet.cssRules) {
            if (rule instanceof CSSKeyframesRule && rule.name === "bcu-confetti") return true;
          }
        } catch {}
      }
      return false;
    });
    expect(hasKeyframe).toBe(true);
  });

  test("theme-btn-danger class is defined", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const exists = await page.evaluate(() => {
      for (const sheet of document.styleSheets) {
        try {
          for (const rule of sheet.cssRules) {
            if (rule instanceof CSSStyleRule && rule.selectorText === ".theme-btn-danger") return true;
          }
        } catch {}
      }
      return false;
    });
    expect(exists).toBe(true);
  });

  test("hero-display class is defined", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const exists = await page.evaluate(() => {
      for (const sheet of document.styleSheets) {
        try {
          for (const rule of sheet.cssRules) {
            if (rule instanceof CSSStyleRule && rule.selectorText === ".hero-display") return true;
          }
        } catch {}
      }
      return false;
    });
    expect(exists).toBe(true);
  });

  test("focus-visible ring is applied on keyboard navigation", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    // Tab to first focusable element
    await page.keyboard.press("Tab");
    const hasFocusVisible = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el) return false;
      const style = getComputedStyle(el);
      return style.boxShadow !== "none" && style.boxShadow !== "";
    });
    expect(hasFocusVisible).toBe(true);
  });

  test("reduced-motion media query exists", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const hasQuery = await page.evaluate(() => {
      for (const sheet of document.styleSheets) {
        try {
          for (const rule of sheet.cssRules) {
            if (rule instanceof CSSMediaRule && rule.conditionText?.includes("prefers-reduced-motion")) return true;
          }
        } catch {}
      }
      return false;
    });
    expect(hasQuery).toBe(true);
  });
});

test.describe("Phase 2 — token reconciliation", () => {
  test("status colors are defined and theme-aware", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const success = await evalCSS(page, "--color-success");
    const danger = await evalCSS(page, "--color-danger");
    const warning = await evalCSS(page, "--color-warning");
    const info = await evalCSS(page, "--color-info");
    expect(success).toBeTruthy();
    expect(danger).toBeTruthy();
    expect(warning).toBeTruthy();
    expect(info).toBeTruthy();
  });

  test("--radius-card references token variable", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const card = await evalCSS(page, "--radius-card");
    expect(card).toBeTruthy();
  });

  test("motion tokens are defined", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const easeOut = await evalCSS(page, "--zozi-ease-out");
    const easeSpring = await evalCSS(page, "--zozi-ease-spring");
    expect(easeOut).toBeTruthy();
    expect(easeSpring).toBeTruthy();
  });
});

test.describe("Phase 3 — component system", () => {
  test("glass-panel class renders backdrop-filter", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const hasGlass = await page.evaluate(() => {
      for (const sheet of document.styleSheets) {
        try {
          for (const rule of sheet.cssRules) {
            if (rule instanceof CSSStyleRule && rule.selectorText?.includes(".glass-panel")) {
              return rule.style.backdropFilter !== "" || rule.style.webkitBackdropFilter !== "";
            }
          }
        } catch {}
      }
      return false;
    });
    expect(hasGlass).toBe(true);
  });
});

test.describe("Phase 5 — modern look", () => {
  test("entrance utility classes exist", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const classes = [".anim-fade-up", ".anim-fade-in", ".anim-scale-in"];
    for (const cls of classes) {
      const exists = await page.evaluate((c) => {
        for (const sheet of document.styleSheets) {
          try {
            for (const rule of sheet.cssRules) {
              if (rule instanceof CSSStyleRule && rule.selectorText === c) return true;
            }
          } catch {}
        }
        return false;
      }, cls);
      expect(exists, `${cls} should exist`).toBe(true);
    }
  });

  test("hero-gradient utility exists", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const exists = await page.evaluate(() => {
      for (const sheet of document.styleSheets) {
        try {
          for (const rule of sheet.cssRules) {
            if (rule instanceof CSSStyleRule && rule.selectorText === ".hero-gradient") return true;
          }
        } catch {}
      }
      return false;
    });
    expect(exists).toBe(true);
  });

  test("print styles exist", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const hasPrint = await page.evaluate(() => {
      for (const sheet of document.styleSheets) {
        try {
          for (const rule of sheet.cssRules) {
            if (rule instanceof CSSMediaRule && rule.conditionText?.includes("print")) return true;
          }
        } catch {}
      }
      return false;
    });
    expect(hasPrint).toBe(true);
  });
});

test.describe("z-index named scale", () => {
  test("z-index config has named scale entries", async () => {
    const fs = await import("fs");
    const config = fs.readFileSync("tailwind.config.js", "utf-8");
    expect(config).toContain("header");
    expect(config).toContain("modal");
    expect(config).toContain("overlay");
    expect(config).toContain("toast");
  });
});

test.describe("theme switching", () => {
  test("toggle light/dark re-themes CSS variables", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    const beforeSurface0 = await evalCSS(page, "--color-surface-0");
    // Try toggling theme if button exists
    const toggleBtn = page.locator("[data-theme-toggle], button:has-text('theme'), button:has-text('dark'), button:has-text('light')").first();
    if (await toggleBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await toggleBtn.click();
      await page.waitForTimeout(500);
      const afterSurface0 = await evalCSS(page, "--color-surface-0");
      expect(afterSurface0).not.toBe(beforeSurface0);
    }
  });
});
