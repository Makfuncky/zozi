import { expect, test, type Page, type Route } from "@playwright/test";
import { bootstrapAdminSessionViaApi } from "./helpers/auth";

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function expectNavigation(page: Page, expectedUrl: RegExp, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (expectedUrl.test(page.url())) {
      return;
    }
    await page.waitForTimeout(250);
  }

  throw new Error(`Timed out waiting for ${expectedUrl}, current URL: ${page.url()}`);
}

async function waitForSessionFlag(page: Page, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const hasLocalSession = await page
      .evaluate(() => window.localStorage.getItem("zozi_has_session") === "1")
      .catch(() => false);
    const cookies = await page.context().cookies();
    if (hasLocalSession || cookies.some((cookie) => cookie.name === "zozi_refresh" || cookie.name === "refresh_token")) {
      return;
    }
    const currentUrl = page.url();
    if (!/\/supplier\/login(?:\?|$)/.test(currentUrl)) {
      return;
    }
    await page.waitForTimeout(250);
  }

  throw new Error(`Timed out waiting for supplier session state after ${timeoutMs}ms`);
}

async function bootstrapSupplierApiSession(page: Page) {
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

  for (const username of ["supplier@zozi.com", "supplier"]) {
    await bootstrapAdminSessionViaApi(page);
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
    return true;
  }

  return false;
}

async function bootstrapSupplierSession(page: Page) {
  let lastError: unknown;

  for (let attempt = 1; attempt <= 2; attempt += 1) {
    try {
      await page.context().clearCookies();
      await page.evaluate(() => window.localStorage.removeItem("zozi_has_session")).catch(() => undefined);

      if (await bootstrapSupplierApiSession(page)) {
        await page.goto("/supplier/dashboard", { waitUntil: "domcontentloaded", timeout: 120_000 });
        await expectNavigation(page, /\/supplier\/dashboard(?:\?|$)/, 120_000);
        return;
      }

      await page.goto("/supplier/login", { waitUntil: "domcontentloaded", timeout: 120_000 });

      const usernameInput = page.getByRole("textbox", { name: /username/i });
      const passwordInput = page.locator("input[type='password']").first();
      await usernameInput.waitFor({ state: "visible", timeout: 30_000 });

      await usernameInput.fill("supplier@zozi.com");
      await expect(usernameInput).toHaveValue("supplier@zozi.com");
      await passwordInput.fill("supplier123");
      await expect(passwordInput).toHaveValue("supplier123");
      const submitButton = page.locator("main").getByRole("button", { name: /^sign in$/i });
      await expect.poll(async () => submitButton.isEnabled(), { timeout: 15_000 }).toBe(true);
      await Promise.all([
        page.waitForURL(/\/supplier\/(dashboard|products)(?:\?|$)/, { timeout: 60_000 }),
        submitButton.click(),
      ]);
      await waitForSessionFlag(page, 15_000);
      if (!/\/supplier\/dashboard(?:\?|$)/.test(page.url())) {
        await page.goto("/supplier/dashboard", { waitUntil: "domcontentloaded", timeout: 120_000 });
      }
      await expectNavigation(page, /\/supplier\/dashboard(?:\?|$)/, 120_000);
      return;
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError;
}

async function openSupplierRoute(page: Page, path: string, expectedUrl: RegExp, timeoutMs = 60_000) {
  await page.goto(path, { waitUntil: "domcontentloaded", timeout: timeoutMs });
  await expectNavigation(page, expectedUrl, timeoutMs);
}

async function ensureSupplierProfileGuide(page: Page) {
  if (/\/supplier\/login(?:\?|$)/.test(page.url())) {
    await bootstrapSupplierSession(page);
    await openSupplierRoute(page, "/supplier/profile?tab=guide", /\/supplier\/profile\?tab=guide(?:$|&)/, 120_000);
  }
}

test.describe("supplier browser smoke", () => {
  test("supplier register completes the multi-step flow", async ({ page }) => {
    await page.route("**/api/auth/register", async (route) => {
      const payload = route.request().postDataJSON() as Record<string, unknown>;
      expect(payload.role).toBe("supplier");
      expect(payload.business_name).toBe("Smoke Supplies");
      expect(payload.terms_accepted).toBe(true);
      await fulfillJson(route, { id: 44, username: payload.username }, 201);
    });

    await page.goto("/supplier/register");

    await page.getByPlaceholder("Choose a username (3-30 chars)").fill("supplier_smoke");
    await page.getByPlaceholder("you@yourbusiness.com").fill("supplier@example.com");
    await page.getByPlaceholder("••••••••").nth(0).fill("SupplierPass123!");
    await page.getByPlaceholder("••••••••").nth(1).fill("SupplierPass123!");
    await page.waitForTimeout(150);
    await page.getByRole("button", { name: /^next/i }).click();
    await expect(page.getByPlaceholder("Your business or brand name")).toBeVisible();

    await page.getByPlaceholder("Your business or brand name").fill("Smoke Supplies");
    await page.getByPlaceholder("+971 50 000 0000").fill("+971 50 123 4567");
    await page.getByRole("combobox").nth(1).selectOption({ label: "United Arab Emirates" });
    await page.waitForTimeout(150);
    await page.getByRole("button", { name: /^next/i }).click();
    await expect(page.getByPlaceholder("https://yourbusiness.com")).toBeVisible();

    await page.getByPlaceholder("https://yourbusiness.com").fill("https://smoke.example.com");
    await page.waitForTimeout(150);
    await page.getByRole("button", { name: /continue/i }).click();
    await expect(page.getByRole("checkbox")).toBeVisible();

    await page.getByRole("checkbox").check();
    await page.waitForTimeout(150);

    await Promise.all([
      page.waitForURL(/\/supplier\/login\?registered=1$/, { timeout: 20_000 }),
      page.getByRole("button", { name: /create account/i }).click(),
    ]);
  });

  test("retired supplier routes land on the merged workspaces", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await bootstrapSupplierSession(page);

    await openSupplierRoute(page, "/supplier/invoices", /\/supplier\/payouts\?view=invoices(?:$|&)/, 120_000);
    await expect(page.getByText("Orders, settlements, payout requests, and invoice records now sit in one finance workspace")).toBeVisible();
    await expect(page.getByRole("button", { name: /invoice records/i })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Invoice history" })).toBeVisible();

    await openSupplierRoute(page, "/supplier/disputes", /\/supplier\/support\?section=disputes(?:$|&)/, 120_000);
    await expect(page.getByText("Support and dispute handling now live in one workspace")).toBeVisible();

    await openSupplierRoute(page, "/supplier/returns", /\/supplier\/orders\?section=returns(?:$|&)/, 120_000);
    await expect(page.getByText("Returns are handled from orders")).toBeVisible();

    await openSupplierRoute(page, "/supplier/logistics", /\/supplier\/orders(?:\?|$)/, 120_000);
    await expect(page.getByText(/Manage handoffs, shipments, delivery confirmations, and return-linked order follow-up from one workspace\./i)).toBeVisible();

    await openSupplierRoute(page, "/supplier/documents", /\/supplier\/profile\?tab=documents(?:$|&)/, 120_000);
    await expect(page.getByRole("button", { name: "KYC Documents" })).toBeVisible();
    await expect(page.getByText(/No KYC documents uploaded yet|Maintain KYC documents/i)).toBeVisible();

    await openSupplierRoute(page, "/supplier/guide", /\/supplier\/profile\?tab=guide(?:$|&)/, 120_000);
    await expect(page.getByText(/Profile, Product Management, Orders, Reports, and Payouts now work as one system\./i)).toBeVisible();
    await expect(page.getByRole("link", { name: /open full supplier guide/i })).toBeVisible();
  });

  test("merged supplier profile action strip stays accessible on narrow screens", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.setViewportSize({ width: 390, height: 844 });
    await bootstrapSupplierSession(page);
    await openSupplierRoute(page, "/supplier/profile?tab=guide", /\/supplier\/profile\?tab=guide(?:$|&)/, 120_000);

    const tabLabels = [
      "Account",
      "Business & Location",
      "Storefront & About",
      "Security",
      "Bank Details",
      "KYC Documents",
      "Coverage",
      "Terms & Conditions",
      "Supplier Guide",
    ] as const;

    const buttonBoxes = [] as Array<{ x: number; width: number; y: number }>;

    for (const label of tabLabels) {
      await ensureSupplierProfileGuide(page);
      const button = page.getByRole("button", { name: new RegExp(`^${label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`, "i") }).first();
      await expect(button).toBeVisible();
      const box = await button.boundingBox();
      expect(box).not.toBeNull();
      if (!box) {
        continue;
      }
      buttonBoxes.push({ x: box.x, width: box.width, y: box.y });
      expect(box.x + box.width).toBeLessThanOrEqual(390);
    }

    const uniqueRows = new Set(buttonBoxes.map((box) => Math.round(box.y)));
    expect(uniqueRows.size).toBeGreaterThan(1);

    const fullGuideLink = page.getByRole("link", { name: /open full supplier guide/i });
    await expect(fullGuideLink).toHaveAttribute("href", "#full-guide");
    await fullGuideLink.click();
    await expect.poll(() => new URL(page.url()).hash).toBe("#full-guide");
    await expect(page.getByText("Detailed walkthrough")).toBeVisible();
  });
});
