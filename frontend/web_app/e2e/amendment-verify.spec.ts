import { expect, test } from "@playwright/test";
import { ensurePanelSession } from "./helpers/auth";

test.describe.configure({ timeout: 180_000 });

const cases: Array<{ role: string; user: string; pass: string; loginPath: string; landing: string; landingRegex: RegExp; title: string }> = [
  { role: "admin", user: "admin@zozi.com", pass: "admin123", loginPath: "/admin/login", landing: "/admin/dashboard", landingRegex: /\/admin\/dashboard(?:\?|$)/, title: "Choose how many dashboard widgets fit in view" },
  { role: "supplier", user: "supplier@zozi.com", pass: "supplier123", loginPath: "/supplier/login", landing: "/supplier/dashboard", landingRegex: /\/supplier\/dashboard(?:\?|$)/, title: "Business performance at a glance" },
  { role: "logistics", user: "logistics@zozi.com", pass: "logistics123", loginPath: "/logistics-partner/login", landing: "/logistics-partner/dashboard", landingRegex: /\/logistics-partner\/dashboard(?:\?|$)/, title: "Real-time logistics operations overview" },
  { role: "logistics", user: "logistics@zozi.com", pass: "logistics123", loginPath: "/logistics-partner/login", landing: "/logistics-partner/routes", landingRegex: /\/logistics-partner\/routes(?:\?|$)/, title: "Total Coverage" },
];

for (const c of cases) {
  test(`${c.role}: ${c.landing} renders with shared shell, StatCard, no duplicate h1, no overflow (mobile)`, async ({ page }) => {
    test.setTimeout(180_000);
    await ensurePanelSession(page, {
      user: c.user,
      pass: c.pass,
      loginPath: c.loginPath,
      landing: c.landing,
      landingRegex: c.landingRegex,
    });

    await page.waitForSelector("aside.theme-sidebar-shell", { state: "attached", timeout: 30_000 });

    await expect(page.getByText(c.title, { exact: false }).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/something went wrong|application error/i)).toHaveCount(0);

    const h1Count = await page.locator("h1").count();
    expect(h1Count).toBeLessThanOrEqual(1);

    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(500);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 4);
    expect(overflow).toBe(false);
  });
}
