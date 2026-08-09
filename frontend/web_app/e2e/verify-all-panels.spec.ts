import { test, expect, type Page } from "@playwright/test";
import { ensurePanelSession } from "./helpers/auth";

const cases = [
  { name: "admin", url: "/admin/dashboard", user: "admin@zozi.com", pass: "admin123", loginPath: "/admin/login", regex: /\/admin\/dashboard(?:\?|$)/ },
  { name: "supplier", url: "/supplier/dashboard", user: "supplier@zozi.com", pass: "supplier123", loginPath: "/supplier/login", regex: /\/supplier\/dashboard(?:\?|$)/ },
  { name: "logistics", url: "/logistics-partner/dashboard", user: "logistics@zozi.com", pass: "logistics123", loginPath: "/logistics-partner/login", regex: /\/logistics-partner\/dashboard(?:\?|$)/ },
];

async function getSidebarWidth(page: Page): Promise<number> {
  const deadline = Date.now() + 15_000;
  while (Date.now() < deadline) {
    const w = await page.evaluate(() => {
      const el = document.querySelector("aside.theme-sidebar-shell") as HTMLElement | null;
      return el ? Math.round(el.getBoundingClientRect().width) : null;
    });
    if (w !== null) return w;
    await page.waitForTimeout(150);
  }
  throw new Error("sidebar width unreadable");
}

for (const c of cases) {
  test(`panel ${c.name}: no global header + sidebar collapses`, async ({ page }) => {
    await page.setViewportSize({ width: 1366, height: 900 });
    await ensurePanelSession(page, {
      user: c.user,
      pass: c.pass,
      loginPath: c.loginPath,
      landing: c.url,
      landingRegex: c.regex,
    });

    await page.waitForSelector("aside.theme-sidebar-shell", { state: "attached", timeout: 30_000 });
    await page.waitForTimeout(500);

    const storeHeaderVisible = await page.locator("header.sticky.top-0.z-100").count();
    const globalHeader = await page.locator('[data-app-header] > header').count();
    console.log(`[${c.name}] global header elements:`, storeHeaderVisible, globalHeader);

    const beforeW = await getSidebarWidth(page);

    // The collapse control has a stable aria-label. Target it directly rather
    // than ".first()" (which can grab a different button on dashboards that
    // render extra controls). Click, then verify; if the first click didn't
    // register (e.g. a transient auth re-validation briefly intercepted the
    // pointer), click once more — the toggle is idempotent to "end state".
    const collapseBtn = page.getByRole("button", { name: /collapse sidebar|expand sidebar/i });
    async function isCollapsed(): Promise<boolean> {
      const w = await getSidebarWidth(page);
      return w !== null && w < beforeW - 50;
    }
    if (!(await isCollapsed())) {
      await collapseBtn.click();
      let ok = false;
      const deadline = Date.now() + 6_000;
      while (Date.now() < deadline) {
        await page.waitForTimeout(250);
        if (await isCollapsed()) {
          ok = true;
          break;
        }
      }
      if (!ok) {
        // One more attempt — tolerate a click that landed during a remount.
        await collapseBtn.click();
        const deadline2 = Date.now() + 4_000;
        while (Date.now() < deadline2) {
          await page.waitForTimeout(250);
          if (await isCollapsed()) {
            ok = true;
            break;
          }
        }
      }
    }
    const afterW = await getSidebarWidth(page);
    console.log(`[${c.name}] sidebar width before=${beforeW} after=${afterW}`);

    expect(afterW, `[${c.name}] sidebar should collapse`).toBeLessThan(beforeW - 50);
    expect(storeHeaderVisible, `[${c.name}] global header should be hidden`).toBe(0);
    expect(globalHeader, `[${c.name}] global header should be hidden`).toBe(0);
  });
}
