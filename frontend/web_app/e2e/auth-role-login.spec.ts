import { expect, test, type Page } from "@playwright/test";

test.describe.configure({ timeout: 120_000 });

/**
 * Poll the page URL until it matches the expectedUrl regex or the timeout
 * elapses. Works with Next.js App Router client-side transitions which do
 * not always emit waitForURL-compatible navigation events.
 */
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
    const currentUrl = page.url();
    if (!/\/(?:admin\/login|logistics-partner\/login|supplier\/login|login)(?:\?|$)/.test(currentUrl)) {
      return;
    }
    await page.waitForTimeout(250);
  }

  throw new Error(`Timed out waiting for session state after ${timeoutMs}ms`);
}

async function openProtectedRoute(
  page: Page,
  path: string,
  expectedUrl: RegExp,
  timeoutMs = 60_000,
) {
  await page.goto(path, { waitUntil: "domcontentloaded", timeout: timeoutMs });
  await expectNavigation(page, expectedUrl, timeoutMs);
}

async function submitCredentialForm(page: Page, username: string, password: string) {
  const submitButton = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  await submitButton.waitFor();
  const form = submitButton.locator("xpath=ancestor::form[1]");
  const identifierCandidates = [
    form.locator("input[name='username']:visible"),
    form.locator("input[autocomplete='username']:visible"),
    form.locator("input[type='email']:visible"),
    form.locator("input:not([type='password']):visible"),
  ];

  let identifierFilled = false;
  for (const candidate of identifierCandidates) {
    if (await candidate.count()) {
      await candidate.first().fill(username);
      await expect(candidate.first()).toHaveValue(username);
      identifierFilled = true;
      break;
    }
  }

  if (!identifierFilled) {
    throw new Error("Unable to find a visible username/email input on the login form.");
  }

  const passwordInput = form.locator("input[type='password']:visible").first();
  await passwordInput.fill(password);
  await expect(passwordInput).toHaveValue(password);
  await expect.poll(async () => submitButton.isEnabled(), { timeout: 15_000 }).toBe(true);
  await submitButton.click();
}

async function bootstrapSessionViaApi(page: Page, candidates: string[], password: string) {
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
  for (const candidate of candidates) {
    const response = await page.request.post("/api/auth/login", {
      form: { username: candidate, password },
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

test.describe("auth role login smoke", () => {
  test("customer login reaches authenticated customer pages", async ({ page }) => {
    test.slow();

    const hasApiSession = await bootstrapSessionViaApi(page, ["customer@zozi.com", "customer"], "customer123");
    if (!hasApiSession) {
      await page.goto("/login");
      await submitCredentialForm(page, "customer@zozi.com", "customer123");
      await waitForSessionFlag(page);
    }

    await openProtectedRoute(page, "/products", /\/products(?:\?|$)/, 60_000);
    await openProtectedRoute(page, "/orders", /\/orders(?:\?|$)/, 30_000);
  });

  test("admin login reaches admin dashboard", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    const hasApiSession = await bootstrapSessionViaApi(page, ["admin@zozi.com", "admin"], "admin123");
    if (!hasApiSession) {
      await page.goto("/admin/login");
      await submitCredentialForm(page, "admin@zozi.com", "admin123");
      await waitForSessionFlag(page);
    }

    await openProtectedRoute(page, "/admin/dashboard", /\/admin\/dashboard(?:\?|$)/, 120_000);
  });

  test("supplier login reaches supplier dashboard", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
    let loginResponse = await page.request.post("/api/auth/login", {
      form: { username: "supplier@zozi.com", password: "supplier123" },
      failOnStatusCode: false,
    });
    if (!loginResponse.ok()) {
      loginResponse = await page.request.post("/api/auth/login", {
        form: { username: "supplier", password: "supplier123" },
        failOnStatusCode: false,
      });
    }
    expect(loginResponse.ok()).toBeTruthy();

    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1"));
    await openProtectedRoute(page, "/supplier/dashboard", /\/supplier\/dashboard(?:\?|$)/, 60_000);
  });

  test("logistics partner login reaches logistics dashboard", async ({ page }) => {
    test.slow();
    test.setTimeout(180_000);

    const hasApiSession = await bootstrapSessionViaApi(page, ["logistics@zozi.com", "logistics"], "logistics123");
    if (!hasApiSession) {
      await page.goto("/logistics-partner/login");
      await submitCredentialForm(page, "logistics@zozi.com", "logistics123");
      await waitForSessionFlag(page);
    }

    await openProtectedRoute(page, "/logistics-partner/dashboard", /\/logistics-partner\/dashboard(?:\?|$)/, 120_000);
  });
});
