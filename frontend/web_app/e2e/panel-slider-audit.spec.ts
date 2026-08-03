import { expect, test, type Page } from "@playwright/test";

test.describe.configure({ timeout: 60_000 });

const USERS: Record<string, { email: string; password: string; loginPage: string; landing: string }> = {
  admin: { email: "admin@zozi.com", password: process.env.E2E_ADMIN_PASSWORD ?? "admin123", loginPage: "/admin/login", landing: "/admin/dashboard" },
  supplier: { email: "supplier@zozi.com", password: process.env.E2E_SUPPLIER_PASSWORD ?? "supplier123", loginPage: "/supplier/login", landing: "/supplier/dashboard" },
  logistics: { email: "logistics@zozi.com", password: process.env.E2E_LOGISTICS_PASSWORD ?? "logistics123", loginPage: "/logistics-partner/login", landing: "/logistics-partner/dashboard" },
};

/** Log in via the panel-specific login form (most reliable auth setup). */
async function formLogin(page: Page, cfg: typeof USERS.admin) {
  await page.goto(cfg.loginPage, { waitUntil: "load" });
  await page.waitForLoadState("networkidle");

  // Fill the login form and submit. The login inputs use sibling <label>
  // text (no htmlFor), so target by control type rather than getByLabel.
  const identifier = page.locator("input:not([type='password']):visible").first();
  await identifier.fill(cfg.email);
  const passwordInput = page.locator("input[type='password']:visible").first();
  await passwordInput.fill(cfg.password);
  await page.getByRole("button", { name: /sign.?in|log.?in|submit|get started/i }).click();

  // Wait for redirect to the expected landing
  await page.waitForURL(`**${cfg.landing}`, { timeout: 20000 });
  await page.waitForLoadState("networkidle");
}

async function getDrawerTransform(page: Page): Promise<string> {
  return page.evaluate(() => {
    const dialog = document.querySelector('[role="dialog"][aria-modal="true"]');
    if (!dialog) return "none";
    return getComputedStyle(dialog).transform;
  });
}

for (const [label, cfg] of Object.entries(USERS)) {
  test(`${label} mobile drawer opens and closes`, async ({ page }) => {
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 390, height: 844 });
    await formLogin(page, cfg);

    // Hamburger visible on mobile
    const hamburger = page.getByRole("button", { name: "Open navigation" });
    await expect(hamburger).toBeVisible({ timeout: 8000 });

    // Drawer starts off-screen
    const closed = await getDrawerTransform(page);
    expect(closed).not.toBe("matrix(1, 0, 0, 1, 0, 0)");

    // Open drawer
    await hamburger.click();
    await page.waitForTimeout(400);
    const open = await getDrawerTransform(page);
    expect(open).toBe("matrix(1, 0, 0, 1, 0, 0)");

    // Overlay present
    const overlay = page.locator(".theme-overlay");
    await expect(overlay).toBeVisible();

    // Close via overlay click
    await overlay.click({ position: { x: 20, y: 20 }, force: true });
    await page.waitForTimeout(400);
    const afterClose = await getDrawerTransform(page);
    expect(afterClose).not.toBe("matrix(1, 0, 0, 1, 0, 0)");

    // Reopen then close via Escape
    await hamburger.click();
    await page.waitForTimeout(400);
    await page.keyboard.press("Escape");
    await page.waitForTimeout(400);
    const afterEsc = await getDrawerTransform(page);
    expect(afterEsc).not.toBe("matrix(1, 0, 0, 1, 0, 0)");

    // No horizontal overflow
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 4);
    expect(overflow).toBe(false);
  });

  test(`${label} desktop sidebar collapses`, async ({ page }) => {
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1440, height: 900 });
    await formLogin(page, cfg);

    // Sidebar is present on desktop — target <aside> specifically to
    // avoid matching the invisible mobile drawer (also .theme-sidebar-shell).
    const aside = page.locator("aside.theme-sidebar-shell");
    await expect(aside).toBeVisible({ timeout: 8000 });

    // Get initial width
    const initialW = await aside.evaluate((el: HTMLElement) => el.getBoundingClientRect().width);
    expect(initialW).toBeGreaterThan(200);

    // Click collapse button
    const collapseBtn = aside.getByRole("button", { name: "Collapse sidebar" });
    await expect(collapseBtn).toBeVisible();
    await collapseBtn.click();
    await page.waitForTimeout(400);

    const collapsedW = await aside.evaluate((el: HTMLElement) => el.getBoundingClientRect().width);
    expect(collapsedW).toBeLessThanOrEqual(100);

    // Expand back
    const expandBtn = aside.getByRole("button", { name: "Expand sidebar" });
    await expect(expandBtn).toBeVisible();
    await expandBtn.click();
    await page.waitForTimeout(400);

    const restoredW = await aside.evaluate((el: HTMLElement) => el.getBoundingClientRect().width);
    expect(restoredW).toBeGreaterThan(200);
  });
}
