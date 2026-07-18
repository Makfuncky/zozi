import { expect, test, type Page, type Route } from "@playwright/test";

const API_HOST = /https?:\/\/(?:localhost|127\.0\.0\.1):8000/;

const supplierSummary = {
  id: 41,
  username: "dream_mart",
  business_name: "Dream Mart",
  slug: "dream-mart",
  canonical_path: "/supplier=dream-mart",
  badge_level: "verified",
  is_verified: true,
  credibility_score: 94,
  avg_rating: 4.8,
  total_reviews: 128,
  total_sales: 640,
  product_count: 22,
  logo_url: null,
  banner_url: null,
  about_us: "Dream Mart supplier storefront",
};

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function mockLoggedOutChrome(page: Page) {
  await page.route("**/api/auth/refresh", async (route) => {
    await fulfillJson(route, { detail: "No active session" }, 401);
  });

  await page.route("**/api/auth/me", async (route) => {
    await fulfillJson(route, { detail: "Not authenticated" }, 401);
  });

  await page.route("**/cart/", async (route) => {
    await fulfillJson(route, []);
  });
}

async function mockSupplierStorefrontApis(page: Page) {
  await page.route(new RegExp(`${API_HOST.source}/suppliers/resolve/.+`), async (route) => {
    await fulfillJson(route, supplierSummary);
  });

  await page.route(new RegExp(`${API_HOST.source}/suppliers/41/products\\?.*`), async (route) => {
    await fulfillJson(route, {
      items: [
        {
          id: 9001,
          name: "Dream Kettle",
          price: 129.99,
          image_url: null,
          rating: 4.7,
          reviews_count: 32,
          supplier_id: 41,
          supplier_name: "Dream Mart",
          category: "home",
          stock: 15,
          is_active: true,
        },
      ],
      total: 1,
      limit: 12,
      offset: 0,
    });
  });

  await page.route(new RegExp(`${API_HOST.source}/suppliers/41$`), async (route) => {
    await fulfillJson(route, {
      ...supplierSummary,
      email: "supplier@dreammart.test",
      phone: "+971500000000",
      address: "Dubai",
      established_year: 2019,
      response_time_hours: 2,
      ship_on_time_rate: 97,
      repeat_customer_rate: 61,
      video_url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      recent_reviews: [
        {
          id: 501,
          rating: 5,
          comment: "Fast shipping and reliable support.",
          customer_name: "Amina",
          created_at: "2026-03-30T10:00:00Z",
          verified_purchase: true,
        },
      ],
    });
  });
}

async function mockProductsPageApis(page: Page) {
  await page.route(new RegExp(`${API_HOST.source}/products/suppliers$`), async (route) => {
    await fulfillJson(route, ["Dream Mart", "Northwind", "Sunrise Goods"]);
  });

  await page.route(new RegExp(`${API_HOST.source}/products/autocomplete\\?.*`), async (route) => {
    const url = new URL(route.request().url());
    const query = url.searchParams.get("q") ?? "";
    await fulfillJson(route, query ? [query] : []);
  });

  await page.route(new RegExp(`${API_HOST.source}/suppliers\\?.*`), async (route) => {
    const url = new URL(route.request().url());
    const query = (url.searchParams.get("q") ?? "").toLowerCase();
    const names = (url.searchParams.get("names") ?? "").toLowerCase();
    const matchesDreamMart = query.includes("dream") || names.includes("dream mart");
    await fulfillJson(route, {
      items: matchesDreamMart ? [supplierSummary] : [],
      total: matchesDreamMart ? 1 : 0,
    });
  });

  await page.route(new RegExp(`${API_HOST.source}/products\\?.*`), async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      headers: { "x-total-count": "0" },
      body: JSON.stringify([]),
    });
  });
}

test.describe("supplier search routing", () => {
  test.beforeEach(async ({ page }) => {
    await mockLoggedOutChrome(page);
    await mockSupplierStorefrontApis(page);
    await mockProductsPageApis(page);
  });

  test("redirects a direct supplier query URL to the storefront", async ({ page }) => {
    await page.goto("/products?supplier=Dream%20Mart");

    await page.waitForURL("**/supplier=dream-mart");
    await expect(page).toHaveURL(/\/supplier=dream-mart$/);
    await expect(page.getByText("Dream Mart").first()).toBeVisible();
  });

  test("opens the supplier storefront from products supplier suggestions", async ({ page }) => {
    await page.goto("/products");

    await expect(page.getByRole("textbox", { name: /^supplier$/i })).toBeVisible();
    await page.getByRole("textbox", { name: /^supplier$/i }).fill("Dream Mart");
    const supplierSuggestion = page.locator("li").filter({ hasText: /^Dream Mart$/ }).first();
    await expect(supplierSuggestion).toBeVisible();
    await supplierSuggestion.click();

    await page.waitForURL("**/supplier=dream-mart");
    await expect(page).toHaveURL(/\/supplier=dream-mart$/);
    await expect(page.getByRole("heading", { name: "Dream Mart", exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "About Dream Mart" })).toBeVisible();
  });
});