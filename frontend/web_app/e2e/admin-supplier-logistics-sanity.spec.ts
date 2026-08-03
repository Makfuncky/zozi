import { devices, expect, test, type Page, type Route } from "@playwright/test";

test.describe.configure({ timeout: 180_000 });
test.use({ browserName: "chromium", ...devices["iPhone 13"] });

const API_HOST = /https?:\/\/(?:localhost|127\.0\.0\.1):8000/;
type LoginConfig = {
  username: string;
  password: string;
  landingRoute: string;
  expectedUrl: RegExp;
};

type SupplierRecord = {
  id: number;
  username: string;
  email: string;
  phone: string;
  is_active: boolean;
  product_count: number;
  order_count: number;
  revenue: number;
  created_at: string;
  verification_status: string;
  verification_note: string;
  top_product_name: string;
  profile: {
    business_name: string;
    credibility_score: number;
    badge_level: string;
    city: string;
    region: string;
    country: string;
    website: string;
    tax_id: string;
    phone_business: string;
  };
};

type ShipmentRecord = {
  id: number;
  order_id: number;
  supplier_id: number;
  supplier_name: string;
  supplier_phone: string;
  supplier_pickup_address: string;
  supplier_pickup_location: string;
  customer_name: string;
  customer_phone: string;
  customer_dropoff_address: string;
  customer_dropoff_location: string;
  estimated_partner_payout: number;
  accepted_load_fit_label: string | null;
  accepted_load_fit_factor: number | null;
  accepted_vehicle_type: string | null;
  accepted_vehicle_multiplier: number | null;
  accepted_shipping_amount: number | null;
  accepted_vehicle_selected_at: string | null;
  pricing_breakdown: {
    shipping_amount: number;
    pickup_fee: number;
    dropoff_fee: number;
    load_fit_label: string;
    load_fit_factor: number;
    floor_applied: boolean;
    ceiling_applied: boolean;
  };
  carrier_name: string;
  tracking_number: string;
  status: string;
  status_label: string;
  distribution_channel: string;
  current_hub: string;
  scan_code: string;
  shipping_address: string;
  delivery_location: string;
  package_count: number;
  package_weight_kg: number;
  package_dimensions: string;
  estimated_delivery: string;
  created_at: string;
};

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

async function waitForSessionState(page: Page, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const hasLocalSession = await page
      .evaluate(() => window.localStorage.getItem("zozi_has_session") === "1")
      .catch(() => false);
    const cookies = await page.context().cookies();
    if (hasLocalSession || cookies.some((cookie) => cookie.name === "zozi_refresh")) {
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

  const identifierCandidates = [
    form.locator("input[name='username']:visible"),
    form.locator("input[autocomplete='username']:visible"),
    form.locator("input[required]:not([type='password']):visible"),
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
  await expect.poll(async () => submitButton.isEnabled()).toBe(true);
  await submitButton.click();
}

async function loginForSanity(page: Page, config: LoginConfig) {
  const loginPath = config.landingRoute.startsWith("/admin/")
    ? "/admin/login"
    : config.landingRoute.startsWith("/logistics-partner/")
      ? "/logistics-partner/login"
      : "/login";

  await page.goto(loginPath, { waitUntil: "domcontentloaded" });
  await submitCredentialForm(page, config.username, config.password);
  await waitForSessionState(page, 30_000);
  await expectNavigation(page, config.expectedUrl, 60_000);
  await page.waitForLoadState("networkidle");
}

function formatStatusLabel(status: string) {
  return status.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

test.describe("admin supplier and logistics sanity", () => {
  test("admin supplier page supports bulk approval and badge recalculation", async ({ page }) => {
    const supplier: SupplierRecord = {
      id: 101,
      username: "mock-supplier",
      email: "supplier-mock@zozi.test",
      phone: "+971500000101",
      is_active: true,
      product_count: 12,
      order_count: 4,
      revenue: 1450,
      created_at: "2026-04-10T09:00:00Z",
      verification_status: "pending",
      verification_note: "Awaiting KYC confirmation",
      top_product_name: "Mock Sofa",
      profile: {
        business_name: "Mock Supply House",
        credibility_score: 62,
        badge_level: "bronze",
        city: "Dubai",
        region: "Dubai",
        country: "UAE",
        website: "https://mock-supply-house.test",
        tax_id: "TAX-101",
        phone_business: "+971500000101",
      },
    };

    let lastBulkPayload: Record<string, unknown> | null = null;
    let refreshBadgeHits = 0;

    await page.route(new RegExp(`${API_HOST.source}/admin/suppliers/all\\?.*`), async (route) => {
      await fulfillJson(route, {
        total: 1,
        page: 1,
        page_size: 25,
        total_pages: 1,
        summary: {
          pending_suppliers: supplier.verification_status === "pending" ? 1 : 0,
          active_suppliers: supplier.is_active ? 1 : 0,
          suspended_suppliers: supplier.is_active ? 0 : 1,
          total_revenue: supplier.revenue,
        },
        items: [supplier],
      });
    });

    await page.route(new RegExp(`${API_HOST.source}/admin/commission/suppliers$`), async (route) => {
      await fulfillJson(route, [
        {
          supplier_id: supplier.id,
          current_rate: 0.14,
          combined_default_rate: 0.2,
          calculation_method: "global",
        },
      ]);
    });

    await page.route(new RegExp(`${API_HOST.source}/admin/suppliers/bulk$`), async (route) => {
      lastBulkPayload = route.request().postDataJSON() as Record<string, unknown>;
      const action = String(lastBulkPayload.action || "");
      if (action === "verify") {
        supplier.verification_status = "approved";
        supplier.is_active = true;
      }
      await fulfillJson(route, { processed: 1 });
    });

    await page.route(new RegExp(`${API_HOST.source}/admin/suppliers/${supplier.id}/refresh-badge$`), async (route) => {
      refreshBadgeHits += 1;
      supplier.profile.badge_level = "silver";
      supplier.profile.credibility_score = 74;
      await fulfillJson(route, { badge_level: "silver" });
    });

    await loginForSanity(page, {
      username: "admin@zozi.com",
      password: "admin123",
      landingRoute: "/admin/dashboard",
      expectedUrl: /\/admin\/dashboard(?:\?|$)/,
    });

    await page.goto("/admin/suppliers", { waitUntil: "domcontentloaded" });
    await page.waitForLoadState("networkidle");

    const rowSelector = page.locator('label:has-text("Select row")').first();
    await rowSelector.click();
    const bulkActionBar = page.getByTestId("bulk-action-bar");
    await expect(bulkActionBar).toBeVisible();

    await bulkActionBar.getByRole("button", { name: "Approve Selected" }).evaluate((button) => {
      (button as HTMLButtonElement).click();
    });
    await expect.poll(() => lastBulkPayload?.action ?? null).toBe("verify");

    expect(lastBulkPayload).toMatchObject({
      supplier_ids: [supplier.id],
      action: "verify",
    });
    expect(supplier.verification_status).toBe("approved");

    await bulkActionBar.getByRole("button", { name: "Clear selection" }).evaluate((button) => {
      (button as HTMLButtonElement).click();
    });
    await expect(page.getByTestId("bulk-action-bar")).not.toBeVisible();

    await page.getByRole("button", { name: /Credibility & Badges/i }).click();
    const badgeRow = page.getByRole("row", { name: /Mock Supply House/i });
    await expect(badgeRow).toBeVisible();
    await badgeRow.getByRole("button", { name: "Recalculate" }).evaluate((button) => {
      (button as HTMLButtonElement).click();
    });
    await expect.poll(() => refreshBadgeHits).toBe(1);

    expect(refreshBadgeHits).toBe(1);
    expect(supplier.profile.badge_level).toBe("silver");
  });

  test("logistics shipment page supports row confirm and bulk status advance", async ({ page }) => {
    const shipment: ShipmentRecord = {
      id: 501,
      order_id: 7001,
      supplier_id: 101,
      supplier_name: "Mock Supply House",
      supplier_phone: "+971500000101",
      supplier_pickup_address: "Dubai Marina Warehouse",
      supplier_pickup_location: "Dubai Marina",
      customer_name: "Aisha Noor",
      customer_phone: "+971500001234",
      customer_dropoff_address: "Palm Jumeirah Residence",
      customer_dropoff_location: "Palm Jumeirah",
      estimated_partner_payout: 38,
      accepted_load_fit_label: null,
      accepted_load_fit_factor: null,
      accepted_vehicle_type: null,
      accepted_vehicle_multiplier: null,
      accepted_shipping_amount: null,
      accepted_vehicle_selected_at: null,
      pricing_breakdown: {
        shipping_amount: 42,
        pickup_fee: 4,
        dropoff_fee: 6,
        load_fit_label: "car",
        load_fit_factor: 1,
        floor_applied: false,
        ceiling_applied: false,
      },
      carrier_name: "Zozi Partner Fleet",
      tracking_number: "TRK-7001-ZOZI",
      status: "prepared",
      status_label: "Prepared",
      distribution_channel: "partner network",
      current_hub: "Dubai Supplier Hub",
      scan_code: "SHIP-7001-0501",
      shipping_address: "Palm Jumeirah Residence",
      delivery_location: "Palm Jumeirah",
      package_count: 2,
      package_weight_kg: 3.5,
      package_dimensions: "40x25x18 cm",
      estimated_delivery: "2026-04-12T12:00:00Z",
      created_at: "2026-04-11T09:00:00Z",
    };

    let rowStatusPayload: Record<string, unknown> | null = null;
    let bulkStatusPayload: Record<string, unknown> | null = null;

    await page.route(new RegExp(`${API_HOST.source}/logistics-partners/shipments\\?.*`), async (route) => {
      await fulfillJson(route, {
        total: 1,
        page: 1,
        page_size: 30,
        total_pages: 1,
        items: [shipment],
      });
    });

    await page.route(new RegExp(`${API_HOST.source}/logistics-partners/shipments/bulk-status$`), async (route) => {
      bulkStatusPayload = route.request().postDataJSON() as Record<string, unknown>;
      shipment.status = String(bulkStatusPayload.status || shipment.status);
      shipment.status_label = formatStatusLabel(shipment.status);
      await fulfillJson(route, { updated: 1 });
    });

    await page.route(new RegExp(`${API_HOST.source}/logistics-partners/shipments/${shipment.id}/status$`), async (route) => {
      rowStatusPayload = route.request().postDataJSON() as Record<string, unknown>;
      shipment.status = String(rowStatusPayload.status || shipment.status);
      shipment.status_label = formatStatusLabel(shipment.status);
      shipment.accepted_load_fit_label = String(rowStatusPayload.load_fit_label || "car");
      shipment.accepted_load_fit_factor = shipment.accepted_load_fit_label === "van" ? 1.2 : shipment.accepted_load_fit_label === "truck" ? 1.5 : shipment.accepted_load_fit_label === "bike" ? 0.9 : 1;
      shipment.accepted_vehicle_type = shipment.accepted_load_fit_label;
      shipment.accepted_vehicle_multiplier = shipment.accepted_load_fit_factor;
      shipment.accepted_shipping_amount = shipment.pricing_breakdown.shipping_amount;
      shipment.accepted_vehicle_selected_at = "2026-04-11T11:15:00Z";
      await fulfillJson(route, { status: shipment.status, status_label: shipment.status_label });
    });

    await loginForSanity(page, {
      username: "logistics",
      password: process.env.E2E_LOGISTICS_PASSWORD ?? "logistics123",
      landingRoute: "/logistics-partner/dashboard",
      expectedUrl: /\/logistics-partner\/dashboard(?:\?|$)/,
    });

    await page.goto("/logistics-partner/shipments", { waitUntil: "domcontentloaded" });
    await page.waitForLoadState("networkidle");

    const confirmButton = page.locator("button:visible").filter({ hasText: "Confirm" }).first();
    await expect(confirmButton).toBeVisible();
    await confirmButton.evaluate((button) => {
      (button as HTMLButtonElement).click();
    });
    await expect.poll(() => rowStatusPayload?.status ?? null).toBe("picking_up");

    expect(rowStatusPayload).toMatchObject({
      status: "picking_up",
      event_type: "pickup_confirmed",
      load_fit_label: "car",
    });
    expect(shipment.status).toBe("picking_up");

    await page.locator('label:has-text("Select row")').first().click();
    await expect(page.getByTestId("bulk-action-bar")).toBeVisible();

    const bulkAdvanceButton = page.locator('[data-testid="bulk-action-bar"] button', { hasText: "Set to in transit" }).first();
    await bulkAdvanceButton.evaluate((button) => {
      (button as HTMLButtonElement).click();
    });
    await expect.poll(() => bulkStatusPayload?.status ?? null).toBe("in_transit");

    expect(bulkStatusPayload).toMatchObject({
      shipment_ids: [shipment.id],
      status: "in_transit",
    });
    expect(shipment.status).toBe("in_transit");
  });
});