import { expect, test, type Page } from "@playwright/test";

test.describe.configure({ timeout: 60_000 });

// Warm up the dev server routes so the first interactive test doesn't hit a
// cold Next.js compile (which delays hydration and breaks the dropdown click).
test.beforeAll(async ({ request }) => {
  await request.get("/").catch(() => {});
  await request.get("/products").catch(() => {});
});

const LOGIN_PAGES: Record<string, { loginPage: string; landing: string; waitFor: string }> = {
  "admin@zozi.com": { loginPage: "/admin/login", landing: "/admin/dashboard", waitFor: "/admin/dashboard" },
  "supplier@zozi.com": { loginPage: "/supplier/login", landing: "/supplier/dashboard", waitFor: "/supplier/dashboard" },
  "logistics@zozi.com": { loginPage: "/logistics-partner/login", landing: "/logistics-partner/dashboard", waitFor: "/logistics-partner/dashboard" },
};

/** Log in via the panel-specific login form so client-side auth state hydrates. */
async function formLogin(page: Page, email: string, password: string) {
  const cfg = LOGIN_PAGES[email];
  await page.goto(cfg.loginPage, { waitUntil: "domcontentloaded" });
  // Wait for the SPA to hydrate the controlled login form before filling,
  // otherwise React resets the values on submit.
  await page.waitForLoadState("networkidle").catch(() => {});
  const userField = page.locator("input:not([type='password']):visible").first();
  await expect(userField).toBeVisible({ timeout: 15000 });
  await userField.fill(email);
  await page.locator("input[type='password']:visible").first().fill(password);
  await page.locator("button[type='submit']:visible").first().click();
  // After a successful login the panel shell (sidebar) is mounted even on
  // mobile (the drawer variant), proving we're past the login screen. Using
  // "attached" avoids viewport-visibility flakiness and the login→dashboard
  // redirect race.
  await page.locator("aside.theme-sidebar-shell").first().waitFor({ state: "attached", timeout: 20000 });
  await page.waitForLoadState("domcontentloaded");
}

async function reportOverflow(page: Page, label: string) {
  return page.evaluate((lbl) => {
    const vw = window.innerWidth;
    const sw = document.documentElement.scrollWidth;
    const offenders = sw > vw + 4
      ? Array.from(document.querySelectorAll("body *"))
          .map((el) => {
            const r = el.getBoundingClientRect();
            return { tag: el.tagName.toLowerCase(), cls: (typeof el.className === "string" ? el.className : "").slice(0, 80), right: Math.round(r.right), w: Math.round(r.width) };
          })
          .filter((o) => o.right > vw + 4)
          .slice(0, 8)
      : [];
    return { label: lbl, viewport: vw, scrollWidth: sw, overflow: sw > vw + 4, offenders };
  }, label);
}

test("storefront: homepage and products page load, price slider present", async ({ page }) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  await expect(page.locator("header, nav").first()).toBeVisible({ timeout: 15000 });

  // The storefront price filter is a dual-handle slider inside the
  // FilterSearchBar "Price" dropdown.
  await page.goto("/products", { waitUntil: "domcontentloaded" });
  await page.waitForLoadState("networkidle").catch(() => {});
  const priceToggle = page.getByRole("button", { name: "Price filter" }).first();
  await expect(priceToggle).toBeVisible({ timeout: 15000 });
  await priceToggle.click();
  // The dropdown animates open; wait for the dual-handle slider group to settle.
  const dual = page.locator(".theme-range-dual").first();
  await dual.waitFor({ state: "attached", timeout: 20000 });
  await expect(dual).toBeVisible({ timeout: 10000 });
  // The group must contain two range inputs (min + max handles).
  await expect(dual.locator("input[type='range'].theme-range")).toHaveCount(2, { timeout: 10000 });
  // The fill bar proves the slider is wired to the selected price bounds.
  await expect(dual.locator(".theme-range-track-fill")).toBeVisible({ timeout: 10000 });
});

test("admin: sidebar + supplier modal open with consistent glass card", async ({ page }) => {
  test.setTimeout(90_000);
  await formLogin(page, "admin@zozi.com", "admin123");
  const aside = page.locator("aside.theme-sidebar-shell");
  await expect(aside).toBeVisible({ timeout: 10000 });

  // Navigate client-side via the sidebar so SPA auth state is preserved
  // (a hard page.goto re-triggers the auth guard and bounces to the storefront).
  await page.getByRole("link", { name: "Suppliers" }).first().click();
  await expect(page).toHaveURL(/\/admin\/suppliers/, { timeout: 15000 });
  const createBtn = page.getByRole("button", { name: /create supplier|add supplier|new supplier/i }).first();
  await expect(createBtn).toBeVisible({ timeout: 10000 });
  await createBtn.click();
  const modal = page.locator(".theme-modal-card, .theme-card").first();
  await expect(modal).toBeVisible({ timeout: 8000 });
  const cls = (await modal.getAttribute("class")) || "";
  // The modal should NOT be the old flat bg-surface-1 look
  expect(cls).not.toContain("bg-surface-1");
});

test("mobile: admin drawer opens without overflow", async ({ page }) => {
  test.setTimeout(90_000);
  await page.setViewportSize({ width: 390, height: 844 });
  await formLogin(page, "admin@zozi.com", "admin123");
  const hamburger = page.getByRole("button", { name: "Open navigation" });
  await expect(hamburger).toBeVisible({ timeout: 10000 });
  await hamburger.click();
  await page.waitForTimeout(800);
  await expect(page.locator(".theme-overlay").first()).toBeVisible({ timeout: 8000 });
  const rep = await reportOverflow(page, "admin-mobile-drawer");
  expect(rep.overflow, JSON.stringify(rep)).toBe(false);
});

test("mobile: supplier dashboard must not overflow", async ({ page }) => {
  test.setTimeout(90_000);
  await page.setViewportSize({ width: 390, height: 844 });
  await formLogin(page, "supplier@zozi.com", "supplier123");
  await page.waitForTimeout(800);
  const rep = await reportOverflow(page, "supplier-mobile");
  expect(rep.overflow, JSON.stringify(rep)).toBe(false);
});

test("mobile: logistics dashboard must not overflow", async ({ page }) => {
  test.setTimeout(90_000);
  await page.setViewportSize({ width: 390, height: 844 });
  await formLogin(page, "logistics@zozi.com", "logistics123");
  await page.waitForTimeout(800);
  const rep = await reportOverflow(page, "logistics-mobile");
  expect(rep.overflow, JSON.stringify(rep)).toBe(false);
});
