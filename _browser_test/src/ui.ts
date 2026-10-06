import { type Page, type Locator } from "@playwright/test";

// ── Page load ───────────────────────────────────────────────────────

export async function waitForPageLoad(page: Page): Promise<void> {
  await page.waitForLoadState("networkidle");
}

// ── Design system / theme ───────────────────────────────────────────

export function glassPanel(locator: Locator) {
  return locator.evaluate((el) => {
    const style = getComputedStyle(el) as CSSStyleDeclaration & { webkitBackdropFilter?: string };
    return style.backdropFilter.includes("blur") || (style.webkitBackdropFilter ?? "").includes("blur");
  });
}

export function sidebarShell(page: Page): Locator {
  return page.locator("aside.theme-sidebar-shell, aside[class*='sidebar']");
}

export function mobileDrawer(page: Page): Locator {
  return page.locator("[role='dialog'][class*='drawer'], [data-testid='mobile-drawer']");
}

export function themeToggle(page: Page): Locator {
  return page.locator("[data-testid='theme-toggle'], button[aria-label*='theme' i], button[aria-label*='dark' i]");
}

export function countrySelector(page: Page): Locator {
  return page.locator("[data-testid='country-selector'], select[name='country_code'], [data-testid='country-switcher']");
}

// ── Overflow / viewport audit ───────────────────────────────────────

export interface OverflowReport {
  viewportWidth: number;
  scrollWidth: number;
  offendingElements: Array<{ selector: string; scrollWidth: number }>;
}

export async function collectOverflowReport(page: Page): Promise<OverflowReport> {
  const viewportWidth = await page.evaluate(() => window.innerWidth);
  const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  const offendingElements = await page.evaluate(() => {
    const elements: Array<{ selector: string; scrollWidth: number }> = [];
    document.querySelectorAll("*").forEach((el) => {
      const rect = el.getBoundingClientRect();
      if (rect.right > window.innerWidth) {
        const testEl = el as HTMLElement;
        const id = testEl.id ? `#${testEl.id}` : "";
        const cls = testEl.className && typeof testEl.className === "string"
          ? `.${testEl.className.trim().split(/\s+/).join(".")}`
          : "";
        const tag = testEl.tagName.toLowerCase();
        elements.push({
          selector: `${tag}${id}${cls}`,
          scrollWidth: Math.round(rect.right - window.innerWidth),
        });
      }
    });
    return elements.sort((a, b) => b.scrollWidth - a.scrollWidth).slice(0, 20);
  });
  return { viewportWidth, scrollWidth, offendingElements };
}
