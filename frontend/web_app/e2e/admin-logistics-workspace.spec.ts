import { expect, test, type Page, type Route } from "@playwright/test";

test.describe.configure({ timeout: 180_000 });

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function mockAdminSession(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.setItem("zozi_has_session", "1");
  });

  await page.route("**/api/auth/refresh**", async (route) => {
    await fulfillJson(route, { access_token: "admin-test-token" });
  });

  await page.route("**/api/auth/me**", async (route) => {
    await fulfillJson(route, {
      id: 1,
      email: "admin@zozi.com",
      username: "admin",
      role: "admin",
      permissions: [],
      preferred_language: "en",
    });
  });

  await page.route("**/admin/hierarchy/permissions", async (route) => {
    await fulfillJson(route, {
      matrix: null,
    });
  });

  await page.route("**/cart/**", async (route) => fulfillJson(route, []));
  await page.route("**/notifications**", async (route) => fulfillJson(route, []));
  await page.route("**/api/notifications**", async (route) => fulfillJson(route, []));
}

async function mockLogisticsApi(page: Page) {
  const partners = [
    {
      id: 101,
      name: "Alpha Express",
      code: "ALPHA",
      contact_name: "Amina Noor",
      contact_email: "ops@alpha.test",
      contact_phone: "+971500000001",
      website: "https://alpha.test",
      status: "active",
      verification_status: "approved",
      verification_note: "Profile approved for live routing.",
      coverage_regions: ["Dubai", "Sharjah"],
      service_types: ["Same-day", "COD"],
      linked_username: "alpha_ops",
      linked_user_email: "alpha@zozi.com",
      country: "UAE",
      city: "Dubai",
      address: "Warehouse District, Dubai",
      bio: "Primary metro operator.",
      created_at: "2025-01-01T00:00:00Z",
    },
    {
      id: 202,
      name: "Beta Cargo",
      code: "BETA",
      contact_name: "Bilal Khan",
      contact_email: "ops@beta.test",
      contact_phone: "+971500000002",
      website: null,
      status: "suspended",
      verification_status: "pending",
      verification_note: "Waiting on updated compliance file.",
      coverage_regions: ["Abu Dhabi"],
      service_types: ["Inter-city"],
      linked_username: "beta_ops",
      linked_user_email: "beta@zozi.com",
      country: "UAE",
      city: "Abu Dhabi",
      address: "Airport Road, Abu Dhabi",
      bio: "Inter-city specialist.",
      created_at: "2025-01-02T00:00:00Z",
    },
  ];

  let serviceAreas = [
    {
      id: 301,
      partner_id: 101,
      country_code: "AE",
      country_name: "United Arab Emirates",
      city_name: "Dubai",
      zone_label: "Downtown Dubai",
      latitude: 25.2048,
      longitude: 55.2708,
      charge_amount: 18,
      minimum_charge: 15,
      per_kg_rate: 2,
      per_km_rate: 0.8,
      fuel_multiplier: 1.05,
      currency: "AED",
      delivery_days_min: 1,
      delivery_days_max: 2,
      is_active: true,
      approval_status: "pending",
      review_note: "Awaiting launch approval.",
    },
    {
      id: 303,
      partner_id: 101,
      country_code: "AE",
      country_name: "United Arab Emirates",
      city_name: "Dubai",
      zone_label: "Dubai Marina",
      latitude: 25.0801,
      longitude: 55.1403,
      charge_amount: 20,
      minimum_charge: 16,
      per_kg_rate: 2.2,
      per_km_rate: 0.9,
      fuel_multiplier: 1.05,
      currency: "AED",
      delivery_days_min: 1,
      delivery_days_max: 2,
      is_active: true,
      approval_status: "approved",
      review_note: "Approved metro lane for pricing control.",
    },
    {
      id: 302,
      partner_id: 202,
      country_code: "AE",
      country_name: "United Arab Emirates",
      city_name: "Abu Dhabi",
      zone_label: "Airport Zone",
      latitude: 24.4539,
      longitude: 54.3773,
      charge_amount: 25,
      minimum_charge: 20,
      per_kg_rate: 3,
      per_km_rate: 1.1,
      fuel_multiplier: 1,
      currency: "AED",
      delivery_days_min: 2,
      delivery_days_max: 3,
      is_active: true,
      approval_status: "approved",
      review_note: "Approved for inter-city coverage.",
    },
  ];

  const pricingProfiles = [
    {
      id: 401,
      partner_id: 101,
      service_area_id: 303,
      profile_name: "Metro Core",
      base_in_city_fee: 12,
      base_inter_city_fee: 20,
      per_km_rate: 0.9,
      per_kg_rate: 2.2,
      minimum_charge: 15,
      fuel_multiplier: 1.05,
      bulk_discount_threshold_kg: 10,
      bulk_discount_percent: 5,
      currency: "AED",
      is_active: true,
      approval_status: "approved",
      review_note: "Aligned with approved metro pricing.",
    },
  ];

  const categoryRules = [
    {
      id: 501,
      partner_id: 101,
      service_area_id: 303,
      category_name: "Fragile Electronics",
      flat_fee_override: 4,
      per_kg_rate_override: null,
      fragile_multiplier: 1.15,
      special_handling_fee: 3,
      currency: "AED",
      is_active: true,
      approval_status: "approved",
      review_note: "Handling surcharge approved.",
    },
    {
      id: 502,
      partner_id: 101,
      service_area_id: 303,
      category_name: "Cold Chain",
      flat_fee_override: 6,
      per_kg_rate_override: null,
      fragile_multiplier: 1,
      special_handling_fee: 5,
      currency: "AED",
      is_active: true,
      approval_status: "approved",
      review_note: "Cold-chain handling approved.",
    },
  ];

  const vehicleRules = [
    {
      id: 601,
      partner_id: 101,
      service_area_id: 303,
      route_scope: "in_city",
      vehicle_type: "bike",
      max_weight_kg: 5,
      max_volume_cm3: 40000,
      cost_multiplier: 1,
      priority_rank: 1,
      is_active: true,
      approval_status: "approved",
      review_note: "Primary urban rider rule.",
    },
  ];

  const cityDistances = [
    {
      id: 701,
      origin_country_code: "AE",
      origin_city_name: "Dubai",
      destination_country_code: "AE",
      destination_city_name: "Abu Dhabi",
      distance_km: 139,
      notes: "Primary corridor",
      created_at: "2025-01-01T00:00:00Z",
      updated_at: "2025-01-01T00:00:00Z",
    },
  ];

  const pricingInsights = {
    partner_id: 101,
    service_area_id: 303,
    health_summary: {
      total_allocations: 6,
      minimum_hits: 1,
      maximum_hits: 0,
      near_cap_count: 2,
      accepted_vehicle_count: 1,
      average_effective_charge: 23.5,
      average_accepted_charge: 24.7,
    },
    alerts: [
      {
        kind: "near_cap",
        severity: "warning",
        count: 2,
        title: "Near cap lanes",
        body: "Recent lanes are clustering close to the configured maximum charge.",
      },
    ],
    route_presets: [
      {
        id: "preset-301",
        source: "preset",
        label: "Downtown Dubai",
        service_area_id: 303,
        route_type: "in_city",
        distance_km: 0,
        weight_kg: 3,
        pickup_count: 1,
        dropoff_count: 1,
        categories: ["Fragile Electronics"],
        vehicle_type: "bike",
        vehicle_multiplier: 1,
        shipping_amount: 18,
        destination_city: "Dubai",
        destination_country: "United Arab Emirates",
      },
    ],
    historical_orders: [
      {
        id: "order-44",
        source: "accepted_vehicle",
        label: "Order #44",
        order_id: 44,
        shipment_id: 22,
        service_area_id: 303,
        route_type: "in_city",
        distance_km: 0,
        weight_kg: 6,
        pickup_count: 1,
        dropoff_count: 1,
        categories: ["Cold Chain", "Fragile Electronics"],
        vehicle_type: "van",
        vehicle_multiplier: 1.2,
        shipping_amount: 27,
        destination_city: "Dubai",
        destination_country: "United Arab Emirates",
      },
    ],
  };

  await page.route(/\/api\/logistics-partners\/?$/, async (route) => {
    const method = route.request().method();
    if (method === "GET") {
      await fulfillJson(route, partners);
      return;
    }

    await route.continue();
  });

  await page.route("**/api/logistics-partners/service-areas", async (route) => {
    await fulfillJson(route, serviceAreas);
  });

  await page.route("**/api/logistics-partners/pricing-profiles", async (route) => {
    await fulfillJson(route, pricingProfiles);
  });

  await page.route("**/api/logistics-partners/category-rules", async (route) => {
    await fulfillJson(route, categoryRules);
  });

  await page.route("**/api/logistics-partners/vehicle-rules", async (route) => {
    await fulfillJson(route, vehicleRules);
  });

  await page.route("**/api/logistics-partners/city-distances", async (route) => {
    await fulfillJson(route, { items: cityDistances });
  });

  await page.route("**/api/logistics-partners/pricing-insights**", async (route) => {
    await fulfillJson(route, pricingInsights);
  });

  await page.route("**/api/logistics-partners/review/service-areas/*", async (route) => {
    const payload = route.request().postDataJSON() as { approval_status?: string };
    const areaId = Number(route.request().url().split("/").pop());
    serviceAreas = serviceAreas.map((area) =>
      area.id === areaId
        ? {
            ...area,
            approval_status: payload.approval_status ?? "approved",
            review_note: `Updated during e2e: ${payload.approval_status ?? "approved"}`,
          }
        : area,
    );

    await fulfillJson(route, {
      detail: `Service area ${payload.approval_status ?? "approved"}.`,
    });
  });

  await page.route("http://localhost:8000/**", async (route) => {
    const url = new URL(route.request().url());
    const pathname = url.pathname.replace(/\/$/, "") || "/";

    if (pathname === "/admin/hierarchy/permissions") {
      await fulfillJson(route, { matrix: null });
      return;
    }

    if (pathname === "/logistics-partners") {
      await fulfillJson(route, partners);
      return;
    }

    if (pathname === "/logistics-partners/service-areas") {
      await fulfillJson(route, serviceAreas);
      return;
    }

    if (pathname === "/logistics-partners/pricing-profiles") {
      await fulfillJson(route, pricingProfiles);
      return;
    }

    if (pathname === "/logistics-partners/category-rules") {
      await fulfillJson(route, categoryRules);
      return;
    }

    if (pathname === "/logistics-partners/vehicle-rules") {
      await fulfillJson(route, vehicleRules);
      return;
    }

    if (pathname === "/logistics-partners/city-distances") {
      await fulfillJson(route, { items: cityDistances });
      return;
    }

    if (pathname === "/logistics-partners/pricing-insights") {
      await fulfillJson(route, pricingInsights);
      return;
    }

    if (pathname.startsWith("/logistics-partners/review/service-areas/")) {
      const payload = route.request().postDataJSON() as { approval_status?: string };
      const areaId = Number(pathname.split("/").pop());
      serviceAreas = serviceAreas.map((area) =>
        area.id === areaId
          ? {
              ...area,
              approval_status: payload.approval_status ?? "approved",
              review_note: `Updated during e2e: ${payload.approval_status ?? "approved"}`,
            }
          : area,
      );
      await fulfillJson(route, { detail: `Service area ${payload.approval_status ?? "approved"}.` });
      return;
    }

    await fulfillJson(route, {});
  });
}

async function openWorkspace(page: Page, name: RegExp) {
  const button = page.getByRole("button", { name }).first();
  await expect(button).toBeVisible();
  await button.evaluate((element: HTMLButtonElement) => element.click());
}

async function gotoWorkspacePage(page: Page, path: string) {
  for (let attempt = 1; attempt <= 2; attempt += 1) {
    try {
      await page.goto(path, { waitUntil: "domcontentloaded", timeout: 60_000 });
      await page.waitForLoadState("networkidle", { timeout: 60_000 });
      return;
    } catch (error) {
      if (attempt === 2) {
        throw error;
      }
      if (page.isClosed()) {
        throw error;
      }
      await page.waitForTimeout(1_500);
    }
  }
}

test.describe("admin logistics workspace", () => {
  test("opens on coverage and route review", async ({ page }) => {
    await mockAdminSession(page);
    await mockLogisticsApi(page);

    await gotoWorkspacePage(page, "/admin/logistics");

    await expect(page.getByText(/Coverage first, one simple charge model second/i)).toBeVisible();
    await expect(page.getByText(/Partner registry and service-area review/i).first()).toBeVisible();
  });

  test("uses the highest handling rule in the pricing workspace", async ({ page }) => {
    await mockAdminSession(page);
    await mockLogisticsApi(page);

    await gotoWorkspacePage(page, "/admin/logistics?section=pricing");

    await expect(page.getByRole("heading", { name: /ZOZI logistics pricing control/i })).toBeVisible();
    await expect(page.getByText(/Rate Card Inputs/i)).toBeVisible();
    await expect(page.getByText(/Extra Stop Charges/i)).toBeVisible();
    await expect(page.getByText(/Highest Handling Rule/i)).toBeVisible();
    await expect(page.getByText(/Coverage first, one simple charge model second/i)).toBeVisible();
  });

  test("shows each workspace with the correct logistics data", async ({ page }) => {
    await mockAdminSession(page);
    await mockLogisticsApi(page);

    // section=partners renders LogisticsPartnersPanel with scope="partners" (stacked layout:
    // "partners" and "areas" workspaces are both visible without workspace-tab navigation)
    await gotoWorkspacePage(page, "/admin/logistics?section=partners");
    await expect(page.getByText(/Partner registry and service-area review/i).first()).toBeVisible();
    await expect(page.getByText(/Partner & Coverage/i).first()).toBeVisible();

    // Partners workspace — stacked, no navigation needed
    await expect(page.getByRole("row", { name: /Alpha Express ALPHA/i })).toBeVisible();
    await expect(page.getByRole("row", { name: /Beta Cargo BETA/i })).toBeVisible();

    // Service Areas workspace — also stacked-visible in scope="partners"
    await expect(page.getByRole("heading", { name: /service area review queue/i })).toBeVisible();
    await expect(page.getByText(/coverage and route board/i)).toBeVisible();
    await expect(page.getByRole("row", { name: /Dubai to Abu Dhabi/i })).toBeVisible();
    await expect(page.getByRole("row", { name: /pending Downtown Dubai Alpha Express/i })).toBeVisible();
  });

  test("supports partner form access and service-area approval flow", async ({ page }) => {
    await mockAdminSession(page);
    await mockLogisticsApi(page);

    await gotoWorkspacePage(page, "/admin/logistics?section=partners");
    await expect(page.getByText(/Partner registry and service-area review/i).first()).toBeVisible();

    // Add Partner button is in the scoped header section
    await page.getByRole("button", { name: /add partner/i }).click();
    await expect(page.getByRole("heading", { name: /add new partner/i })).toBeVisible();
    await expect(page.getByText("Company Name *")).toBeVisible();
    await page.getByRole("button", { name: /^Cancel$/i }).click();
    await expect(page.getByRole("row", { name: /Alpha Express ALPHA Portal user: alpha@zozi\.com/i })).toBeVisible();

    // Service areas are rendered as table rows in the current stacked workspace.
    const pendingAreaRow = page.getByRole("row", { name: /pending Downtown Dubai Alpha Express Dubai/i });

    await expect(pendingAreaRow).toBeVisible();
    await pendingAreaRow.getByRole("button", { name: /^Approve$/i }).click();
    await expect(page.getByText(/service area approved\./i)).toBeVisible();
    await expect(page.getByRole("row", { name: /approved Downtown Dubai Alpha Express Dubai/i })).toBeVisible();
  });
});
