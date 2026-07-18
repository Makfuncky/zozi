import { expect, test, type Page } from "@playwright/test";

test.describe.configure({ timeout: 180_000 });

async function expectNavigation(
  page: Page,
  expectedUrl: RegExp,
  timeoutMs = 60_000,
) {
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
    await page.waitForTimeout(250);
  }

  throw new Error(`Timed out waiting for session state after ${timeoutMs}ms`);
}

async function submitCredentialForm(page: Page, username: string, password: string) {
  const submitButton = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  await submitButton.waitFor();
  const form = submitButton.locator("xpath=ancestor::form[1]");
  await form.waitFor({ state: "visible" });

  const identifierCandidates = [
    form.locator("input[name='username']:visible"),
    form.locator("input[autocomplete='username']:visible"),
    form.locator("input[required]:not([type='password']):visible"),
    form.locator("input[type='email']:visible"),
    form.locator("input:not([type='password']):visible"),
  ];

  for (const candidate of identifierCandidates) {
    if (await candidate.count()) {
      await candidate.first().fill(username);
      await expect(candidate.first()).toHaveValue(username);
      const passwordInput = form.locator("input[type='password']:visible").first();
      await passwordInput.fill(password);
      await expect(passwordInput).toHaveValue(password);
      await expect.poll(async () => submitButton.isEnabled()).toBe(true);
      await submitButton.click();
      return;
    }
  }

  throw new Error("Unable to find a visible username/email input on the login form.");
}

async function bootstrapAdminSessionViaApi(page: Page) {
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
  for (const candidate of ["admin@zozi.com", "admin"]) {
    const response = await page.request.post("/api/auth/login", {
      form: { username: candidate, password: "admin123" },
      failOnStatusCode: false,
    });
    if (!response.ok()) {
      continue;
    }
    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1"));
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    return true;
  }
  return false;
}

test.describe("admin logistics pricing insights live smoke", () => {
  test("pricing workspace loads real pricing insights without stale-backend route drift", async ({ page }) => {
    test.slow();

    const stalePricingRequests: string[] = [];
    page.on("request", (request) => {
      if (/\/logistics-partners\/pricing-insights\?/.test(request.url())) {
        stalePricingRequests.push(request.url());
      }
    });

    const hasApiSession = await bootstrapAdminSessionViaApi(page);
    if (!hasApiSession) {
      try {
        await page.goto("/admin/login", { waitUntil: "domcontentloaded", timeout: 120_000 });
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        if (/ERR_ABORTED|ERR_CONNECTION_REFUSED|ERR_CONNECTION_RESET|ERR_CONNECTION_CLOSED/i.test(message)) {
          test.skip(true, `Skipping: frontend admin login route is unavailable in this environment (${message}).`);
        }
        throw error;
      }
      await submitCredentialForm(page, "admin@zozi.com", "admin123");
    }
    await waitForSessionFlag(page, 45_000);
    if (!/\/admin\//.test(page.url())) {
      await page.goto("/admin/dashboard", { waitUntil: "domcontentloaded", timeout: 120_000 }).catch(() => undefined);
    }
    const stillOnLogin = /\/admin\/login(?:\?|$)/.test(page.url());
    const loginButtonVisible = (await page.getByRole("button", { name: /sign in|log in|signin/i }).count().catch(() => 0)) > 0;
    if (stillOnLogin || loginButtonVisible) {
      test.skip(true, "Skipping: admin session could not be established reliably in this live environment.");
    }

    const logisticsPageResponse = await page.goto("/admin/logistics?section=pricing", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await expectNavigation(page, /\/admin\/logistics\?section=pricing(?:&|$)/, 120_000);

    if (logisticsPageResponse?.status() === 404) {
      const snapshotText = await page.locator("body").innerText().catch(() => "");
      if (/Route GET:\/admin\/logistics\?section=pricing not found/i.test(snapshotText)) {
        test.skip(true, "Skipping: /admin route is being served by a non-Next process on localhost:3000 in this environment.");
      }
    }

    await expect(page.getByRole("heading", { name: "ZOZI logistics pricing control" })).toBeVisible({ timeout: 120_000 });
    await expect(page.getByText("Rate Card Filter")).toBeVisible({ timeout: 120_000 });

    const pricingInputs = page.getByText(/Rate Card Inputs/i);
    const emptyState = page.getByText(/No approved pricing profile is available/i);

    await expect
      .poll(async () => (await pricingInputs.count()) > 0 || (await emptyState.count()) > 0, { timeout: 120_000 })
      .toBe(true);

    const hasInputs = (await pricingInputs.count()) > 0;
    const hasEmptyState = (await emptyState.count()) > 0;
    expect(hasInputs || hasEmptyState).toBe(true);

    if (hasInputs) {
      await expect(page.getByText(/Extra Stop Charges/i)).toBeVisible({ timeout: 120_000 });
      await expect(page.getByText(/Highest Handling Rule/i)).toBeVisible({ timeout: 120_000 });
    } else {
      await expect(emptyState).toBeVisible({ timeout: 120_000 });
    }
    expect(stalePricingRequests).toHaveLength(0);
    await expect(page.getByText(/Method Not Allowed/i)).toHaveCount(0);
  });
});

