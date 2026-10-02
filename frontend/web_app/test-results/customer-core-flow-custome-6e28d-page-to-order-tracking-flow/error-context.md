# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: customer-core-flow.spec.ts >> customer core browser flow >> product page to order tracking flow
- Location: e2e\customer-core-flow.spec.ts:129:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByLabel(/open account menu/i)
Expected: visible
Timeout: 90000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 90000ms
  - waiting for getByLabel(/open account menu/i)

```

```yaml
- banner:
  - link "Go to home":
    - /url: /
    - img "Zozi logo"
    - text: Zozi
  - button "All Products"
  - button "Price"
  - button "Rating"
  - button "Supplier"
  - textbox "Search products, brands, suppliers..."
  - button "Search by image"
  - button "Voice search"
  - button "Search"
  - button "Switch to dark theme": 🌙
  - text: OMR Auto detected
  - button "Choose country": AUTO
  - button "Choose language": EN
  - link "Wishlist":
    - /url: /wishlist
  - link "Cart (1 items)":
    - /url: /cart
    - text: "1"
  - button "Open sign in menu"
  - navigation:
    - link "Shop":
      - /url: /products
    - link "Suppliers":
      - /url: /suppliers
    - link "Offers":
      - /url: /offers
    - link "Help":
      - /url: /help
- main:
  - heading "Cart (1)" [level=1]
  - button "Browse Products"
  - img "Chef's Knife 8-inch"
  - heading "Chef's Knife 8-inch" [level=3]
  - paragraph: OMR 89.990
  - paragraph: "Color: Silver"
  - button
  - text: "1"
  - button
  - button
  - heading "Order Summary" [level=2]
  - text: 1 items OMR 0.000 VAT OMR 0.000 Delivery Free Total OMR 0.000
  - button "Calculate Shipping"
  - button "Proceed to Checkout"
  - button "Clear Cart"
  - text: Secure checkout. Your payment information is protected.
- contentinfo:
  - text: ZOZI
  - paragraph: Trust delivered through verified suppliers, exceptional products, and global reach.
  - link "Become a Supplier":
    - /url: /supplier/register
  - link "Become Logistics Partner":
    - /url: /logistics-partner/login
  - heading "The ZOZI Dispatch" [level=5]
  - heading "Stay in Style" [level=3]
  - paragraph: Get exclusive access to new arrivals, special offers, and fashion tips.
  - textbox "First name (optional)"
  - textbox "Enter your email"
  - button "Subscribe" [disabled]
  - paragraph: © 2026 ZOZI. All rights reserved.
  - link "Terms":
    - /url: /terms
  - link "Privacy":
    - /url: /privacy
  - link "Cookies":
    - /url: /cookies
  - link "Admin Portal":
    - /url: /admin/login
- button "Chat":
  - img
  - text: Chat
- alert
```

# Test source

```ts
  1   | import { expect, test, type Page } from "@playwright/test";
  2   | import { bootstrapAdminSessionViaApi, bootstrapSessionViaApi, submitCredentialForm, waitForSessionFlag } from "./helpers/auth";
  3   | 
  4   | test.describe.configure({ timeout: 240_000 });
  5   | 
  6   | type ProductSummary = {
  7   |   id: number;
  8   |   stock?: number;
  9   |   name?: string;
  10  | };
  11  | 
  12  | type ProductDetail = {
  13  |   id: number;
  14  |   stock?: number;
  15  |   name: string;
  16  |   sizes?: string | null;
  17  |   color?: string | null;
  18  |   variants?: Array<{
  19  |     size?: string | null;
  20  |     title?: string | null;
  21  |     color?: string | null;
  22  |     stock?: number | null;
  23  |     is_active?: boolean;
  24  |   }>;
  25  | };
  26  | 
  27  | function escapeRegExp(value: string) {
  28  |   return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  29  | }
  30  | 
  31  | async function expectNavigation(page: Page, expectedUrl: RegExp, timeoutMs = 90_000) {
  32  |   const deadline = Date.now() + timeoutMs;
  33  |   while (Date.now() < deadline) {
  34  |     if (expectedUrl.test(page.url())) {
  35  |       return;
  36  |     }
  37  |     await page.waitForTimeout(250);
  38  |   }
  39  | 
  40  |   throw new Error(`Timed out waiting for ${expectedUrl}, current URL: ${page.url()}`);
  41  | }
  42  | 
  43  | /**
  44  |  * The frontend stores the access token only in memory, so it is lost on every
  45  |  * full page navigation and must be re-established via a silent refresh from the
  46  |  * httpOnly refresh cookie. A navigation can momentarily cancel that refresh, so
  47  |  * we wait until the header shows the authenticated "Open account menu" control
  48  |  * before interacting with auth-gated UI.
  49  |  */
  50  | async function waitForAuth(page: Page, timeoutMs = 90_000) {
> 51  |   await expect(page.getByLabel(/open account menu/i)).toBeVisible({ timeout: timeoutMs });
      |                                                       ^ Error: expect(locator).toBeVisible() failed
  52  | }
  53  | 
  54  | async function bootstrapCustomerSession(page: Page) {
  55  |   await bootstrapAdminSessionViaApi(page);
  56  | }
  57  | 
  58  | async function fetchFirstPurchasableProduct(page: Page): Promise<ProductDetail> {
  59  |   const listRes = await page.request.get("http://localhost:8000/api/v1/customer/catalog/products?limit=50", {
  60  |     failOnStatusCode: false,
  61  |   });
  62  |   expect(listRes.ok()).toBeTruthy();
  63  | 
  64  |   const listJson = (await listRes.json()) as Record<string, unknown>;
  65  |   const listData = Array.isArray(listJson.items) ? listJson.items : (listJson as unknown as ProductSummary[]);
  66  |   expect(Array.isArray(listData)).toBeTruthy();
  67  | 
  68  |   for (const candidate of listData) {
  69  |     if (!candidate?.id) {
  70  |       continue;
  71  |     }
  72  | 
  73  |     const detailRes = await page.request.get(`http://localhost:8000/api/v1/customer/catalog/products/${candidate.id}`, {
  74  |       failOnStatusCode: false,
  75  |     });
  76  |     if (!detailRes.ok()) {
  77  |       continue;
  78  |     }
  79  | 
  80  |     const detail = (await detailRes.json()) as ProductDetail;
  81  |     const variants = Array.isArray(detail.variants) ? detail.variants : [];
  82  |     const hasStockVariant = variants.some((variant) => {
  83  |       const active = variant.is_active !== false;
  84  |       const variantStock = Number(variant.stock ?? 0);
  85  |       return active && variantStock > 0;
  86  |     });
  87  | 
  88  |     if (hasStockVariant || Number(detail.stock ?? 0) > 0) {
  89  |       return detail;
  90  |     }
  91  |   }
  92  | 
  93  |   throw new Error("No purchasable product found in seeded catalog.");
  94  | }
  95  | 
  96  | function getFirstVariantChoice(product: ProductDetail): { size?: string; color?: string } {
  97  |   const variants = Array.isArray(product.variants) ? product.variants : [];
  98  |   const activeVariants = variants.filter((variant) => variant.is_active !== false && Number(variant.stock ?? 0) > 0);
  99  | 
  100 |   const fromVariants = activeVariants[0];
  101 |   if (fromVariants) {
  102 |     return {
  103 |       size: (fromVariants.size || fromVariants.title || "").trim() || undefined,
  104 |       color: (fromVariants.color || "").trim() || undefined,
  105 |     };
  106 |   }
  107 | 
  108 |   const firstSizeFromJson = (() => {
  109 |     if (!product.sizes) return undefined;
  110 |     try {
  111 |       const parsed = JSON.parse(product.sizes);
  112 |       return Array.isArray(parsed) ? String(parsed[0] || "").trim() || undefined : undefined;
  113 |     } catch {
  114 |       return undefined;
  115 |     }
  116 |   })();
  117 | 
  118 |   const firstColorFromCsv = product.color
  119 |     ? product.color.split(",").map((value) => value.trim()).find(Boolean)
  120 |     : undefined;
  121 | 
  122 |   return {
  123 |     size: firstSizeFromJson,
  124 |     color: firstColorFromCsv,
  125 |   };
  126 | }
  127 | 
  128 | test.describe("customer core browser flow", () => {
  129 |   test("product page to order tracking flow", async ({ page }) => {
  130 |     test.slow();
  131 | 
  132 |     await bootstrapCustomerSession(page);
  133 | 
  134 |     const product = await fetchFirstPurchasableProduct(page);
  135 |     const selectedVariant = getFirstVariantChoice(product);
  136 | 
  137 |     await page.goto("/products", { waitUntil: "domcontentloaded" });
  138 |     await expectNavigation(page, /\/products(?:\?|$)/, 90_000);
  139 |     await expect(page.getByText(/\d+\s+results/i).first()).toBeVisible({ timeout: 90_000 });
  140 | 
  141 |     await page.goto(`/products/${product.id}`, { waitUntil: "domcontentloaded" });
  142 |     await expectNavigation(page, new RegExp(`/products/${product.id}(?:-|\\b|\\?|$)`), 90_000);
  143 |     await expect(page.getByRole("heading", { name: new RegExp(escapeRegExp(product.name), "i") })).toBeVisible({ timeout: 90_000 });
  144 | 
  145 |     if (selectedVariant.size) {
  146 |       const sizeButton = page
  147 |         .getByRole("button", { name: new RegExp(`^${escapeRegExp(selectedVariant.size)}$`, "i") })
  148 |         .first();
  149 |       if (await sizeButton.isVisible().catch(() => false)) {
  150 |         await sizeButton.click();
  151 |       }
```