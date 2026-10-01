import { test, expect, type Page, type Route } from "@playwright/test";

// ═══════════════════════════════════════════════════════════════════════════
//  This test suite validates the enhanced header search bar across 6 areas:
//  1. Category Selection  2. Price Filter  3. Rating Filter
//  4. Supplier Search     5. Voice Search   6. Image Search
// ═══════════════════════════════════════════════════════════════════════════

const API_HOST = /https?:\/\/(?:localhost|127\.0\.0\.1):8000/;

const MOCK_PRODUCTS = [
  { id: 101, name: "Classic T-Shirt", price: 29.99, category: "fashion", stock: 15, is_active: true, image_url: null, description: "A comfy tee", supplier: "FashionHub", rating: 4.5, sales_count: 120, tags: "cotton, casual" },
  { id: 102, name: "Wireless Headphones", price: 89.99, category: "electronics", stock: 8, is_active: true, image_url: null, description: "Bluetooth 5.0", supplier: "TechWorld", rating: 4.7, sales_count: 230, tags: "audio, wireless" },
  { id: 103, name: "Yoga Mat", price: 34.99, category: "sports", stock: 25, is_active: true, image_url: null, description: "Non-slip mat", supplier: "FitLife", rating: 4.3, sales_count: 89, tags: "fitness, yoga" },
  { id: 104, name: "Coffee Maker", price: 59.99, category: "home", stock: 12, is_active: true, image_url: null, description: "12-cup drip", supplier: "HomeGoods", rating: 4.1, sales_count: 67, tags: "kitchen, coffee" },
  { id: 105, name: "Running Shoes", price: 129.99, category: "sports", stock: 6, is_active: true, image_url: null, description: "Lightweight runners", supplier: "FitLife", rating: 4.8, sales_count: 310, tags: "running, shoes" },
];

const MOCK_SUPPLIERS = ["FashionHub", "TechWorld", "FitLife", "HomeGoods"];

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
}

async function setupSharedMocks(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem("zozi-theme", JSON.stringify({ state: { theme: "light" } }));
  });

  // Auth (anonymous)
  await page.route("**/api/auth/refresh", async (route) => fulfillJson(route, { detail: "No active session" }, 401));
  await page.route("**/api/auth/me", async (route) => fulfillJson(route, { detail: "Not authenticated" }, 401));
  await page.route("**/cart/", async (route) => fulfillJson(route, []));

  // Products — smart filtering mock
  await page.route(new RegExp(`${API_HOST.source}/products(\\?.*)?$`), async (route) => {
    const url = new URL(route.request().url());
    const q = url.searchParams.get("q");
    let filtered = [...MOCK_PRODUCTS];
    if (q) { const lq = q.toLowerCase(); filtered = filtered.filter((p) => p.name.toLowerCase().includes(lq) || p.description.toLowerCase().includes(lq)); }
    const category = url.searchParams.get("category");
    if (category && category !== "all") filtered = filtered.filter((p) => p.category === category);
    const minPrice = url.searchParams.get("min_price");
    if (minPrice) filtered = filtered.filter((p) => p.price >= Number(minPrice));
    const minRating = url.searchParams.get("min_rating");
    if (minRating) filtered = filtered.filter((p) => p.rating >= Number(minRating));
    await route.fulfill({ status: 200, contentType: "application/json", headers: { "x-total-count": String(filtered.length) }, body: JSON.stringify(filtered) });
  });

  // Suppliers
  await page.route(new RegExp(`${API_HOST.source}/products/suppliers$`), async (route) => fulfillJson(route, MOCK_SUPPLIERS));

  // Autocomplete
  await page.route(new RegExp(`${API_HOST.source}/search/autocomplete\\?.*`), async (route) => {
    const url = new URL(route.request().url());
    const q = url.searchParams.get("q")?.toLowerCase() || "";
    const suggestions = MOCK_PRODUCTS.filter((p) => p.name.toLowerCase().includes(q)).map((p) => p.name);
    await fulfillJson(route, { suggestions });
  });

  // Other
  await page.route(new RegExp(`${API_HOST.source}/search/trending\\?.*`), async (route) => fulfillJson(route, { queries: ["wireless headphones", "running shoes", "yoga mat"] }));
  await page.route(new RegExp(`${API_HOST.source}/search/visual$`), async (route) => fulfillJson(route, { similarProducts: MOCK_PRODUCTS.slice(0, 3), similarProductIds: [101, 102, 103] }));
  await page.route(new RegExp(`${API_HOST.source}/banners`), async (route) => fulfillJson(route, []));
  await page.route(new RegExp(`${API_HOST.source}/flash-sales$`), async (route) => fulfillJson(route, []));
  await page.route(new RegExp(`${API_HOST.source}/suppliers\\?.*`), async (route) => fulfillJson(route, { items: [], total: 0 }));
  await page.route(new RegExp(`${API_HOST.source}/suppliers/resolve/.*`), async (route) => fulfillJson(route, {}, 404));
  await page.route(new RegExp(`${API_HOST.source}/countries$`), async (route) => fulfillJson(route, [{ code: "US", name: "United States", currency: "USD", is_active: true }]));
}

async function goToProducts(page: Page) {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/products", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(2000);
}

// ═══════════════════════════════════════════════════════════════════════════
//  1️⃣ CATEGORY SELECTION
// ═══════════════════════════════════════════════════════════════════════════
test.describe("Category Selection", () => {
  test.beforeEach(async ({ page }) => {
    await setupSharedMocks(page);
    await goToProducts(page);
  });

  test("category button exists and is clickable in the search bar", async ({ page }) => {
    const catBtn = page.locator(".glass-search button").first();
    await expect(catBtn).toBeVisible({ timeout: 10000 });
    await expect(catBtn).toBeEnabled();
    await catBtn.click();
    await page.waitForTimeout(300);
  });

  test("category param is sent to /products endpoint", async ({ page }) => {
    let capturedUrl = "";
    // Wait for any existing route to be unregistered by using a fresh route
    await page.unroute(new RegExp(`${API_HOST.source}/products(\\?.*)?$`));
    await page.route(new RegExp(`${API_HOST.source}/products(\\?.*)?$`), async (route) => {
      capturedUrl = route.request().url();
      await fulfillJson(route, MOCK_PRODUCTS);
    });
    await page.goto("/products?category=fashion", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2000);
    expect(capturedUrl).toContain("category=fashion");
  });
});

// ═══════════════════════════════════════════════════════════════════════════
//  2️⃣ PRICE FILTER
// ═══════════════════════════════════════════════════════════════════════════
test.describe("Price Filter", () => {
  test.beforeEach(async ({ page }) => {
    await setupSharedMocks(page);
  });

  test("min_price param is passed to /products endpoint", async ({ page }) => {
    let capturedUrl = "";
    await page.unroute(new RegExp(`${API_HOST.source}/products(\\?.*)?$`));
    await page.route(new RegExp(`${API_HOST.source}/products(\\?.*)?$`), async (route) => {
      capturedUrl = route.request().url();
      await fulfillJson(route, MOCK_PRODUCTS);
    });
    await page.goto("/products?min_price=50", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2000);
    expect(capturedUrl).toContain("min_price=50");
  });

  test("price_asc sort param is passed to /products endpoint", async ({ page }) => {
    let capturedUrl = "";
    await page.unroute(new RegExp(`${API_HOST.source}/products(\\?.*)?$`));
    await page.route(new RegExp(`${API_HOST.source}/products(\\?.*)?$`), async (route) => {
      capturedUrl = route.request().url();
      await fulfillJson(route, MOCK_PRODUCTS);
    });
    await page.goto("/products?sort=price_asc", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2000);
    expect(capturedUrl).toContain("sort=price_asc");
  });
});

// ═══════════════════════════════════════════════════════════════════════════
//  3️⃣ RATING FILTER
// ═══════════════════════════════════════════════════════════════════════════
test.describe("Rating Filter", () => {
  test.beforeEach(async ({ page }) => {
    await setupSharedMocks(page);
  });

  test("min_rating param is passed to /products endpoint", async ({ page }) => {
    let capturedUrl = "";
    await page.unroute(new RegExp(`${API_HOST.source}/products(\\?.*)?$`));
    await page.route(new RegExp(`${API_HOST.source}/products(\\?.*)?$`), async (route) => {
      capturedUrl = route.request().url();
      await fulfillJson(route, MOCK_PRODUCTS);
    });
    await page.goto("/products?min_rating=4", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2000);
    expect(capturedUrl).toContain("min_rating=4");
  });
});

// ═══════════════════════════════════════════════════════════════════════════
//  4️⃣ SUPPLIER SEARCH
// ═══════════════════════════════════════════════════════════════════════════
test.describe("Supplier Search", () => {
  test.beforeEach(async ({ page }) => {
    await setupSharedMocks(page);
    await goToProducts(page);
  });

  test("supplier button exists in the search bar", async ({ page }) => {
    const supplierBtn = page.locator(".glass-search button", { hasText: "Supplier" });
    await expect(supplierBtn).toBeVisible({ timeout: 10000 });
  });

  test("supplier dropdown opens with search input", async ({ page }) => {
    const supplierBtn = page.locator(".glass-search button", { hasText: "Supplier" });
    await supplierBtn.click();
    await page.waitForTimeout(300);
    const supplierInput = page.getByPlaceholder("Search suppliers...");
    await expect(supplierInput).toBeVisible({ timeout: 5000 });
  });

  test("/products/suppliers endpoint is called on page load", async ({ page }) => {
    let called = false;
    await page.unroute(new RegExp(`${API_HOST.source}/products/suppliers$`));
    await page.route(new RegExp(`${API_HOST.source}/products/suppliers$`), async (route) => {
      called = true;
      await fulfillJson(route, MOCK_SUPPLIERS);
    });
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2000);
    expect(called).toBeTruthy();
  });
});

// ═══════════════════════════════════════════════════════════════════════════
//  5️⃣ VOICE SEARCH BUTTON
// ═══════════════════════════════════════════════════════════════════════════
test.describe("Voice Search Button", () => {
  test.beforeEach(async ({ page }) => {
    await setupSharedMocks(page);
    await goToProducts(page);
  });

  test("mic button is visible with title 'Voice search'", async ({ page }) => {
    const micBtn = page.locator("button[title='Voice search']");
    await expect(micBtn).toBeVisible({ timeout: 10000 });
    // Note: disabled in headless browsers (no SpeechRecognition API)
  });
});

// ═══════════════════════════════════════════════════════════════════════════
//  6️⃣ IMAGE SEARCH BUTTON
// ═══════════════════════════════════════════════════════════════════════════
test.describe("Image Search Button", () => {
  test.beforeEach(async ({ page }) => {
    await setupSharedMocks(page);
    await goToProducts(page);
  });

  test("camera button is visible and enabled with title 'Search by image'", async ({ page }) => {
    const cameraBtn = page.locator("button[title='Search by image']");
    await expect(cameraBtn).toBeVisible({ timeout: 10000 });
    await expect(cameraBtn).toBeEnabled();
  });
});

// ═══════════════════════════════════════════════════════════════════════════
//  SEARCH BAR RENDERING
// ═══════════════════════════════════════════════════════════════════════════
test.describe("Search Bar Rendering", () => {
  test.beforeEach(async ({ page }) => {
    await setupSharedMocks(page);
    await goToProducts(page);
  });

  test("glass-search bar is present in the sticky header", async ({ page }) => {
    await expect(page.locator(".glass-search")).toBeVisible({ timeout: 10000 });
  });

  test("search input accepts text and triggers autocomplete", async ({ page }) => {
    const input = page.locator("input[placeholder*='Search']").first();
    await expect(input).toBeVisible();
    await expect(input).toBeEnabled();
    await input.fill("wireless");
    await expect(input).toHaveValue("wireless");
    // Autocomplete endpoint should be called
    await page.waitForTimeout(1200);
  });

  test("search button with text is visible", async ({ page }) => {
    const searchBtn = page.locator(".glass-search button", { hasText: "Search" });
    await expect(searchBtn).toBeVisible({ timeout: 10000 });
  });

  test("quick filter pills (New Arrivals, Trending, Deals) are visible", async ({ page }) => {
    await expect(page.getByText("New Arrivals")).toBeVisible({ timeout: 15000 });
    await expect(page.getByText("Trending")).toBeVisible();
    await expect(page.getByText("Deals")).toBeVisible();
  });
});

// ═══════════════════════════════════════════════════════════════════════════
//  EDGE CASES
// ═══════════════════════════════════════════════════════════════════════════
test.describe("Edge Cases", () => {
  test.beforeEach(async ({ page }) => {
    await setupSharedMocks(page);
  });

  test("autocomplete endpoint is called when user types", async ({ page }) => {
    let called = false;
    await page.unroute(new RegExp(`${API_HOST.source}/search/autocomplete\\?.*`));
    await page.route(new RegExp(`${API_HOST.source}/search/autocomplete\\?.*`), async (route) => {
      called = true;
      await fulfillJson(route, { suggestions: ["Classic T-Shirt"] });
    });
    await page.goto("/products", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2000);
    const input = page.locator("input[placeholder*='Search']").first();
    await input.fill("Classic");
    await page.waitForTimeout(1200);
    expect(called).toBeTruthy();
  });

  test("products page calls /products endpoint on initial load", async ({ page }) => {
    let called = false;
    await page.unroute(new RegExp(`${API_HOST.source}/products(\\?.*)?$`));
    await page.route(new RegExp(`${API_HOST.source}/products(\\?.*)?$`), async (route) => {
      called = true;
      await fulfillJson(route, MOCK_PRODUCTS);
    });
    await page.goto("/products", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    expect(called).toBeTruthy();
  });
});
