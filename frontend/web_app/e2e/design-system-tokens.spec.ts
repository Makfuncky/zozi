import { expect, test } from "@playwright/test";

/**
 * Design-system token runtime check (DS12).
 * Verifies the CSS custom properties from `styles/tokens.css` are actually
 * present and resolved on the rendered document, proving the token source is
 * wired (globals.css + layout.tsx) and not just defined-but-dead.
 */
test.describe("design-system tokens resolve at runtime", () => {
  test("homepage exposes the wired design tokens", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

    const radius = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue("--zozi-radius-sm").trim(),
    );
    const duration = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue("--zozi-duration-fast").trim(),
    );
    const elevation = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue("--zozi-elevation-md").trim(),
    );

    expect(radius).toBeTruthy();
    expect(radius).toMatch(/px$/);
    expect(duration).toMatch(/ms$/);
    expect(elevation).toMatch(/rgb\(/);
  });
});
