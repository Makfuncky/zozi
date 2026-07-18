import { expect, test, type Page, type Route } from "@playwright/test";

const API_HOST = /https?:\/\/(?:localhost|127\.0\.0\.1):8000/;

const productResults = [
  {
    id: 301,
    name: "Playwright Linen Set",
    price: 19.99,
    category: "fashion",
    stock: 8,
    is_active: true,
    image_url: null,
    description: "A lightweight linen set for storefront visual verification.",
    supplier: "Maison Noir",
    rating: 4.8,
    sales_count: 18,
    tags: "linen, summer",
  },
  {
    id: 302,
    name: "Playwright Travel Tote",
    price: 29.99,
    category: "accessories",
    stock: 5,
    is_active: true,
    image_url: null,
    description: "A structured tote for visual shell checks.",
    supplier: "Maison Noir",
    rating: 4.6,
    sales_count: 11,
    tags: "travel, tote",
  },
];

async function fulfillJson(route: Route, body: unknown, status = 200, headers?: Record<string, string>) {
  await route.fulfill({
    status,
    contentType: "application/json",
    headers,
    body: JSON.stringify(body),
  });
}

async function mockAnonymousChrome(page: Page) {
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

async function mockProductsPageApis(page: Page) {
  await page.route(new RegExp(`${API_HOST.source}/banners$`), async (route) => {
    await fulfillJson(route, [
      {
        id: 1,
        title: "ZOZI - Trust Delivered",
        subtitle: "Admin-managed campaigns stay readable while background effects remain visible.",
        badge_text: "Marketplace Edit",
        cta_label: "Shop now",
        cta_url: "/products",
        image_url: null,
        banner_type: "hero",
        is_active: true,
        sort_order: 0,
        bg_color: "#2f9440",
        text_color: "#ffffff",
        subtitle_color: "rgba(255,255,255,0.82)",
        btn_bg_color: "rgba(255,255,255,0.18)",
        btn_text_color: "#ffffff",
        badge_color: "rgba(255,255,255,0.16)",
        effect: "poppers",
      },
    ]);
  });

  await page.route(new RegExp(`${API_HOST.source}/banners\?type=promotional$`), async (route) => {
    await fulfillJson(route, []);
  });

  await page.route(new RegExp(`${API_HOST.source}/flash-sales$`), async (route) => {
    await fulfillJson(route, [
      {
        id: 1,
        title: "Summer Sale",
        discount_pct: 15,
        starts_at: "2026-06-01T00:00:00Z",
        ends_at: "2026-06-30T23:59:59Z",
        is_active: true,
      },
    ]);
  });

  await page.route(new RegExp(`${API_HOST.source}/products/suppliers$`), async (route) => {
    await fulfillJson(route, ["Maison Noir", "Northwind"]);
  });

  await page.route(new RegExp(`${API_HOST.source}/products/autocomplete\?.*`), async (route) => {
    await fulfillJson(route, []);
  });

  await page.route(new RegExp(`${API_HOST.source}/suppliers\?.*`), async (route) => {
    await fulfillJson(route, { items: [], total: 0 });
  });

  await page.route(new RegExp(`${API_HOST.source}/products\?.*`), async (route) => {
    const url = new URL(route.request().url());
    if (url.searchParams.get("sort") === "discount" && url.searchParams.get("min_discount") === "5") {
      await fulfillJson(route, []);
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      headers: { "x-total-count": String(productResults.length) },
      body: JSON.stringify(productResults),
    });
  });
}

test.describe("products visual shell", () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("zozi-theme", JSON.stringify({ state: { theme: "light" } }));
    });

    await mockAnonymousChrome(page);
    await mockProductsPageApis(page);
  });

  test("keeps background effects visible without reintroducing an opaque white shell", async ({ page }) => {
    await page.goto("/products");

    await expect(page.getByTestId("products-hero-shell")).toBeVisible();
    await expect(page.getByTestId("products-search-shell")).toBeVisible();
    await expect(page.getByTestId("products-results-shell")).toBeVisible();
    await expect(page.getByText(/flash sales|deals/i)).toBeVisible();
    await expect(page.locator(".glass-product-card")).toHaveCount(2);

    const diagnostics = await page.evaluate(() => {
      const readBlur = (value: string) => {
        const match = value.match(/blur\(([^p]+)/);
        return match ? Number.parseFloat(match[1]) : 0;
      };

      const readBackground = (selector: string) => {
        const element = document.querySelector(selector);
        if (!element) return null;
        const style = getComputedStyle(element);
        return {
          background: style.backgroundImage,
          blur: readBlur(style.backdropFilter),
        };
      };

      return {
        hasEffect: Boolean(document.querySelector(".aurora-bg, .confetti-fall, .balloon-rise, .sparkle-pulse")),
        search: readBackground('[data-testid="products-search-shell"]'),
        results: readBackground('[data-testid="products-results-shell"]'),
      };
    });

    expect(diagnostics.hasEffect).toBeTruthy();
    expect(diagnostics.search?.blur ?? 0).toBeLessThanOrEqual(20);
    expect(diagnostics.search?.background ?? "").not.toContain("0.96");
    expect(diagnostics.results?.background ?? "").not.toContain("0.99");
  });
});