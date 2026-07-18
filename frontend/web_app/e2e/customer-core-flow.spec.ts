import { expect, test, type Page } from "@playwright/test";

test.describe.configure({ timeout: 240_000 });

type ProductSummary = {
  id: number;
  stock?: number;
  name?: string;
};

type ProductDetail = {
  id: number;
  stock?: number;
  name: string;
  sizes?: string | null;
  color?: string | null;
  variants?: Array<{
    size?: string | null;
    title?: string | null;
    color?: string | null;
    stock?: number | null;
    is_active?: boolean;
  }>;
};

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

async function expectNavigation(page: Page, expectedUrl: RegExp, timeoutMs = 90_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (expectedUrl.test(page.url())) {
      return;
    }
    await page.waitForTimeout(250);
  }

  throw new Error(`Timed out waiting for ${expectedUrl}, current URL: ${page.url()}`);
}

/**
 * The frontend stores the access token only in memory, so it is lost on every
 * full page navigation and must be re-established via a silent refresh from the
 * httpOnly refresh cookie. A navigation can momentarily cancel that refresh, so
 * we wait until the header shows the authenticated "Open account menu" control
 * before interacting with auth-gated UI.
 */
async function waitForAuth(page: Page, timeoutMs = 90_000) {
  await expect(page.getByLabel(/open account menu/i)).toBeVisible({ timeout: timeoutMs });
}

async function bootstrapCustomerSession(page: Page) {
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

  const credentials = [
    { username: "customer@zozi.com", password: "customer123" },
    { username: "customer", password: "customer123" },
  ];

  let authenticated = false;
  for (const candidate of credentials) {
    const response = await page.request.post("/api/auth/login", {
      form: candidate,
      failOnStatusCode: false,
    });

    if (!response.ok()) {
      continue;
    }

    authenticated = true;
    break;
  }

  expect(authenticated).toBeTruthy();
  await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1"));
  await page.request.get("/api/auth/me", { failOnStatusCode: false });
}

async function fetchFirstPurchasableProduct(page: Page): Promise<ProductDetail> {
  const listRes = await page.request.get("http://localhost:8000/products?limit=50", {
    failOnStatusCode: false,
  });
  expect(listRes.ok()).toBeTruthy();

  const listData = (await listRes.json()) as ProductSummary[];
  expect(Array.isArray(listData)).toBeTruthy();

  for (const candidate of listData) {
    if (!candidate?.id) {
      continue;
    }

    const detailRes = await page.request.get(`http://localhost:8000/products/${candidate.id}`, {
      failOnStatusCode: false,
    });
    if (!detailRes.ok()) {
      continue;
    }

    const detail = (await detailRes.json()) as ProductDetail;
    const variants = Array.isArray(detail.variants) ? detail.variants : [];
    const hasStockVariant = variants.some((variant) => {
      const active = variant.is_active !== false;
      const variantStock = Number(variant.stock ?? 0);
      return active && variantStock > 0;
    });

    if (hasStockVariant || Number(detail.stock ?? 0) > 0) {
      return detail;
    }
  }

  throw new Error("No purchasable product found in seeded catalog.");
}

function getFirstVariantChoice(product: ProductDetail): { size?: string; color?: string } {
  const variants = Array.isArray(product.variants) ? product.variants : [];
  const activeVariants = variants.filter((variant) => variant.is_active !== false && Number(variant.stock ?? 0) > 0);

  const fromVariants = activeVariants[0];
  if (fromVariants) {
    return {
      size: (fromVariants.size || fromVariants.title || "").trim() || undefined,
      color: (fromVariants.color || "").trim() || undefined,
    };
  }

  const firstSizeFromJson = (() => {
    if (!product.sizes) return undefined;
    try {
      const parsed = JSON.parse(product.sizes);
      return Array.isArray(parsed) ? String(parsed[0] || "").trim() || undefined : undefined;
    } catch {
      return undefined;
    }
  })();

  const firstColorFromCsv = product.color
    ? product.color.split(",").map((value) => value.trim()).find(Boolean)
    : undefined;

  return {
    size: firstSizeFromJson,
    color: firstColorFromCsv,
  };
}

test.describe("customer core browser flow", () => {
  test("product page to order tracking flow", async ({ page }) => {
    test.slow();

    await bootstrapCustomerSession(page);

    const product = await fetchFirstPurchasableProduct(page);
    const selectedVariant = getFirstVariantChoice(product);

    await page.goto("/products", { waitUntil: "domcontentloaded" });
    await expectNavigation(page, /\/products(?:\?|$)/, 90_000);
    await expect(page.getByText(/\d+\s+results/i).first()).toBeVisible({ timeout: 90_000 });

    await page.goto(`/products/${product.id}`, { waitUntil: "domcontentloaded" });
    await expectNavigation(page, new RegExp(`/products/${product.id}(?:-|\\b|\\?|$)`), 90_000);
    await expect(page.getByRole("heading", { name: new RegExp(escapeRegExp(product.name), "i") })).toBeVisible({ timeout: 90_000 });

    if (selectedVariant.size) {
      const sizeButton = page
        .getByRole("button", { name: new RegExp(`^${escapeRegExp(selectedVariant.size)}$`, "i") })
        .first();
      if (await sizeButton.isVisible().catch(() => false)) {
        await sizeButton.click();
      }
    }

    if (selectedVariant.color) {
      const colorButton = page.locator(`button[title=\"${selectedVariant.color}\"]`).first();
      if (await colorButton.isVisible().catch(() => false)) {
        await colorButton.click();
      }
    }

    await page.getByRole("button", { name: /add to cart/i }).click();

    await page.goto("/cart", { waitUntil: "domcontentloaded" });
    await expectNavigation(page, /\/cart(?:\?|$)/, 90_000);
    await expect(page.getByRole("heading", { name: /^cart/i })).toBeVisible({ timeout: 60_000 });
    await waitForAuth(page);

    await page.getByRole("button", { name: /proceed to checkout/i }).click();
    await expectNavigation(page, /\/checkout(?:\?|$)/, 90_000);
    await waitForAuth(page);

    // Checkout is a single-page form (Delivery Details + Payment Method).
    // Input order on the page: Full Name, Phone, Country, City, Postal Code, Street.
    await page.locator("input").nth(0).fill("Customer Flow User");
    await page.locator("input").nth(1).fill("+971500000001");
    await page.locator("input").nth(2).fill("UAE");
    await page.locator("input").nth(3).fill("Dubai");
    await page.locator("input").nth(4).fill("00000");
    await page.locator("input").nth(5).fill("Business Bay Street 12");

    await page.getByRole("button", { name: /cash on delivery/i }).click();
    await page.getByRole("button", { name: /place order/i }).click();

    await expectNavigation(page, /\/orders\/\d+(?:\?|$)/, 90_000);

    const orderMatch = page.url().match(/\/orders\/(\d+)/);
    expect(orderMatch).not.toBeNull();
    const orderId = Number(orderMatch?.[1]);
    expect(Number.isFinite(orderId)).toBeTruthy();

    await page.goto(`/tracking/${orderId}`, { waitUntil: "domcontentloaded" });
    await expectNavigation(page, new RegExp(`/tracking/${orderId}(?:\\?|$)`), 90_000);
    await expect(page.getByText(new RegExp(`Order Tracker #${orderId}`, "i"))).toBeVisible({ timeout: 90_000 });
    await expect(page.getByTestId("tracking-live-status")).toBeVisible({ timeout: 90_000 });
  });
});
