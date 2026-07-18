import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

test.describe.configure({ timeout: 240_000 });

const BACKEND_BASE_URL = "http://localhost:8000";

type AuthSession = {
  token: string;
  email: string;
};

async function backendLogin(
  request: APIRequestContext,
  usernameCandidates: string[],
  password: string,
): Promise<string> {
  for (const username of usernameCandidates) {
    const response = await request.post(`${BACKEND_BASE_URL}/auth/login`, {
      form: { username, password },
      failOnStatusCode: false,
    });
    if (!response.ok()) {
      continue;
    }
    const payload = await response.json();
    const token = typeof payload?.access_token === "string" ? payload.access_token : "";
    if (token) {
      return token;
    }
  }

  throw new Error("Unable to authenticate with provided credentials");
}

async function createApprovedCountryPartner(
  request: APIRequestContext,
  adminToken: string,
  name: string,
  code: string,
  countryName: string,
  countryCode: string,
  cityName: string,
): Promise<number> {
  const createResponse = await request.post(`${BACKEND_BASE_URL}/logistics-partners/`, {
    headers: { Authorization: `Bearer ${adminToken}` },
    data: {
      name,
      code,
      status: "active",
    },
    failOnStatusCode: false,
  });

  expect(createResponse.ok()).toBeTruthy();
  const createdPayload = await createResponse.json();
  const partnerId = Number(createdPayload?.id);
  expect(Number.isFinite(partnerId)).toBeTruthy();

  const approveProfileResponse = await request.post(
    `${BACKEND_BASE_URL}/logistics-partners/review/profile/${partnerId}`,
    {
      headers: { Authorization: `Bearer ${adminToken}` },
      data: { status: "approved" },
      failOnStatusCode: false,
    },
  );
  expect(approveProfileResponse.ok()).toBeTruthy();

  const createAreaResponse = await request.post(`${BACKEND_BASE_URL}/logistics-partners/service-areas`, {
    headers: { Authorization: `Bearer ${adminToken}` },
    data: {
      partner_id: partnerId,
      country_name: countryName,
      country_code: countryCode,
      city_name: cityName,
      charge_amount: 10,
      currency: "AED",
      is_active: true,
    },
    failOnStatusCode: false,
  });
  expect(createAreaResponse.ok()).toBeTruthy();
  const areaPayload = await createAreaResponse.json();
  const areaId = Number(areaPayload?.id);
  expect(Number.isFinite(areaId)).toBeTruthy();

  return partnerId;
}

async function bootstrapCustomerBrowserSession(page: Page) {
  for (let attempt = 0; attempt < 2; attempt += 1) {
    await page.context().clearCookies();
    for (const username of ["customer@zozi.com", "customer"]) {
      await page.goto("/login", { waitUntil: "domcontentloaded", timeout: 120_000 });
      const form = page.locator("form").first();
      const usernameInput = form.locator("input[name='username']:visible").first();
      const passwordInput = form.locator("input[name='password']:visible, input[type='password']:visible").first();
      const submitButton = form.getByRole("button", { name: /sign in|log in/i }).first();

      await usernameInput.fill(username);
      await passwordInput.fill("customer123");
      await expect.poll(async () => submitButton.isEnabled(), { timeout: 15_000 }).toBe(true);
      await submitButton.click();

      const deadline = Date.now() + 60_000;
      while (Date.now() < deadline) {
        const accountMenuVisible = await page
          .getByRole("button", { name: /open account menu/i })
          .isVisible()
          .catch(() => false);
        if (accountMenuVisible) {
          await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
          return;
        }
        await page.waitForTimeout(250);
      }
    }
  }

  throw new Error("Customer browser session did not stabilize on the authenticated app shell.");
}

async function selectCountryFromHeader(page: Page, matcher: RegExp) {
  await page.getByRole("button", { name: /choose country/i }).click();
  const option = page.locator("button").filter({ hasText: matcher }).first();
  await expect(option).toBeVisible({ timeout: 15_000 });
  await option.click();
}

test("manual country switching updates logistics discovery segregation and request country header", async ({ page, request }) => {
  test.slow();

  let lastCountryHeader: string | null = null;
  await page.route("http://localhost:8000/logistics-partners/public**", async (route) => {
    lastCountryHeader = route.request().headers()["x-country-code"] ?? null;
    await route.continue();
  });
  await page.route("http://127.0.0.1:8000/logistics-partners/public**", async (route) => {
    lastCountryHeader = route.request().headers()["x-country-code"] ?? null;
    await route.continue();
  });

  const runId = `${Date.now()}`;
  const adminToken = await backendLogin(request, ["admin@zozi.com", "admin"], "admin123");

  const pkName = `Country Partner PK ${runId}`;
  const omName = `Country Partner OM ${runId}`;

  await createApprovedCountryPartner(
    request,
    adminToken,
    pkName,
    `LPPK${runId.slice(-6)}`,
    "Pakistan",
    "PK",
    "Lahore",
  );

  await createApprovedCountryPartner(
    request,
    adminToken,
    omName,
    `LPOM${runId.slice(-6)}`,
    "Oman",
    "OM",
    "Muscat",
  );

  await bootstrapCustomerBrowserSession(page);

  await page.goto("/logistics-partners", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: /discover logistics partners approved/i })).toBeVisible({ timeout: 90_000 });

  await selectCountryFromHeader(page, /Pakistan|\bPK\b/i);
  await expect.poll(() => page.evaluate(() => window.localStorage.getItem("zozi_selected_country"))).toBe("PK");
  const searchInput = page.getByRole("textbox", { name: /search approved logistics partners/i });
  await searchInput.fill(runId);
  await page.getByRole("button", { name: /^search$/i }).click();

  await expect(page.getByRole("heading", { name: new RegExp(pkName, "i") })).toBeVisible({ timeout: 60_000 });
  await expect(page.getByRole("heading", { name: new RegExp(omName, "i") })).toHaveCount(0);
  await expect(page.getByText("OMR").first()).toHaveCount(0);
  await expect.poll(() => lastCountryHeader, { timeout: 30_000 }).toBe("PK");
});
