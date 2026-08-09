# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin-commission.spec.ts >> Admin Commission Management >> overview tab shows global config and summary cards
- Location: e2e\admin-commission.spec.ts:130:7

# Error details

```
Error: page.goto: net::ERR_ABORTED at http://127.0.0.1:3000/admin/commission
Call log:
  - navigating to "http://127.0.0.1:3000/admin/commission", waiting until "domcontentloaded"

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - link "Skip to main content" [ref=e2] [cursor=pointer]:
    - /url: "#main-content"
  - generic [ref=e3]:
    - banner [ref=e5]:
      - generic [ref=e7]:
        - link "Go to home" [ref=e8] [cursor=pointer]:
          - /url: /
          - generic [ref=e9]:
            - img "Zozi logo" [ref=e11]
            - generic [ref=e27]: Zozi
        - generic [ref=e31]:
          - button "All Products" [ref=e33] [cursor=pointer]:
            - img [ref=e34]
            - generic [ref=e37]: All Products
            - img [ref=e38]
          - button "Price" [ref=e41] [cursor=pointer]:
            - img [ref=e42]
            - generic [ref=e45]: Price
            - img [ref=e46]
          - button "Rating" [ref=e49] [cursor=pointer]:
            - img [ref=e50]
            - generic [ref=e52]: Rating
            - img [ref=e53]
          - button "Supplier" [ref=e56] [cursor=pointer]:
            - img [ref=e57]
            - generic [ref=e61]: Supplier
            - img [ref=e62]
          - generic [ref=e64]:
            - img
            - textbox "Search products, brands, suppliers..." [ref=e65]
          - button "Search by image" [ref=e66] [cursor=pointer]:
            - img [ref=e67]
          - button "Voice search" [disabled] [ref=e70]:
            - img [ref=e71]
          - button "Search" [ref=e74] [cursor=pointer]:
            - img [ref=e75]
            - generic [ref=e78]: Search
        - generic [ref=e79]:
          - button "Toggle theme" [disabled] [ref=e80]
          - generic [ref=e81]:
            - generic [ref=e82]:
              - generic [ref=e83]: OMR
              - generic [ref=e84]: Auto detected
            - button "Choose country" [ref=e86] [cursor=pointer]:
              - generic [ref=e87]: AUTO
              - img [ref=e88]
            - button "Choose language" [ref=e91] [cursor=pointer]:
              - generic [ref=e92]: EN
              - img [ref=e93]
          - link "Wishlist" [ref=e95] [cursor=pointer]:
            - /url: /wishlist
            - img [ref=e96]
          - link "Cart" [ref=e98] [cursor=pointer]:
            - /url: /cart
            - img [ref=e99]
          - button "Open sign in menu" [ref=e103] [cursor=pointer]:
            - img [ref=e104]
    - main [ref=e108]:
      - main [ref=e109]:
        - generic [ref=e110]:
          - generic [ref=e111]:
            - button "New Arrivals" [ref=e112] [cursor=pointer]:
              - img [ref=e113]
              - text: New Arrivals
            - button "Trending" [ref=e116] [cursor=pointer]:
              - img [ref=e117]
              - text: Trending
            - button "Deals" [ref=e120] [cursor=pointer]:
              - img [ref=e121]
              - text: Deals
            - button "10%+" [ref=e125] [cursor=pointer]:
              - img [ref=e126]
              - text: 10%+
            - button "20%+" [ref=e129] [cursor=pointer]:
              - img [ref=e130]
              - text: 20%+
            - button "30%+" [ref=e133] [cursor=pointer]:
              - img [ref=e134]
              - text: 30%+
            - button "50%+" [ref=e137] [cursor=pointer]:
              - img [ref=e138]
              - text: 50%+
          - paragraph [ref=e142]: 0 results
          - generic [ref=e144]:
            - img [ref=e146]
            - heading "No products found" [level=3] [ref=e149]
            - paragraph [ref=e150]: Try adjusting your filters or search terms to discover more products.
            - button "Clear All Filters" [ref=e151] [cursor=pointer]
    - contentinfo [ref=e153]:
      - generic [ref=e155]:
        - generic [ref=e156]:
          - generic [ref=e157]:
            - img [ref=e159]
            - generic [ref=e162]: ZOZI
          - paragraph [ref=e163]: Trust delivered through verified suppliers, exceptional products, and global reach.
          - generic [ref=e164]:
            - link "Become a Supplier" [ref=e165] [cursor=pointer]:
              - /url: /supplier/register
            - link "Become Logistics Partner" [ref=e166] [cursor=pointer]:
              - /url: /logistics-partner/login
        - generic [ref=e167]:
          - heading "The ZOZI Dispatch" [level=5] [ref=e168]
          - generic [ref=e169]:
            - generic [ref=e170]:
              - heading "Stay in Style" [level=3] [ref=e171]
              - paragraph [ref=e172]: Get exclusive access to new arrivals, special offers, and fashion tips.
            - generic [ref=e173]:
              - textbox "First name (optional)" [ref=e175]
              - textbox "Enter your email" [ref=e177]
              - button "Subscribe" [disabled] [ref=e178]:
                - img [ref=e179]
                - text: Subscribe
      - generic [ref=e183]:
        - paragraph [ref=e184]: © 2026 ZOZI. All rights reserved.
        - generic [ref=e185]:
          - link "Terms" [ref=e186] [cursor=pointer]:
            - /url: /terms
          - link "Privacy" [ref=e187] [cursor=pointer]:
            - /url: /privacy
          - link "Cookies" [ref=e188] [cursor=pointer]:
            - /url: /cookies
          - link "Admin Portal" [ref=e189] [cursor=pointer]:
            - /url: /admin/login
            - img [ref=e190]
```

# Test source

```ts
  1   | /**
  2   |  * Admin Commission Management — Playwright E2E Tests
  3   |  *
  4   |  * Covers /admin/commission page: overview config, category rates,
  5   |  * and badge tiers.
  6   |  */
  7   | import { expect, test, type Page, type Route } from "@playwright/test";
  8   | import { bootstrapAdminSessionViaApi } from "./helpers/auth";
  9   | 
  10  | async function fulfillJson(route: Route, body: unknown, status = 200) {
  11  |   await route.fulfill({
  12  |     status,
  13  |     contentType: "application/json",
  14  |     body: JSON.stringify(body),
  15  |   });
  16  | }
  17  | 
  18  | async function mockAdminSession(page: Page) {
  19  |   await page.context().clearCookies();
  20  |   await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
  21  |   await page.evaluate(() => window.localStorage.removeItem("zozi_has_session")).catch(() => undefined);
  22  | 
  23  |   for (const candidate of ["admin@zozi.com", "admin"]) {
  24  |     await bootstrapAdminSessionViaApi(page);
  25  | 
  26  |     await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
  27  |     await page.request.get("/api/auth/me", { failOnStatusCode: false });
> 28  |     await page.goto("/admin/commission", { waitUntil: "domcontentloaded", timeout: 120_000 });
      |                ^ Error: page.goto: net::ERR_ABORTED at http://127.0.0.1:3000/admin/commission
  29  | 
  30  |     const gate = page.getByRole("heading", { name: /Admin Access/i });
  31  |     if (!(await gate.isVisible().catch(() => false))) {
  32  |       await page.route("**/cart/**", async (r) => fulfillJson(r, []));
  33  |       await page.route("**/notifications**", async (r) => fulfillJson(r, []));
  34  |       await page.route("**/api/notifications**", async (r) => fulfillJson(r, []));
  35  |       return;
  36  |     }
  37  |   }
  38  | 
  39  |   await page.goto("/admin/login", { waitUntil: "domcontentloaded", timeout: 120_000 });
  40  |   const btn = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  41  |   await btn.waitFor();
  42  |   const form = btn.locator("xpath=ancestor::form[1]");
  43  |   await form.locator("input:not([type='password']):visible").first().fill("admin@zozi.com");
  44  |   await form.locator("input[type='password']:visible").first().fill("admin123");
  45  |   await btn.click();
  46  |   await page.waitForTimeout(5000);
  47  |   await page.goto("/admin/commission", { waitUntil: "domcontentloaded", timeout: 120_000 });
  48  |   await page.route("**/cart/**", async (r) => fulfillJson(r, []));
  49  |   await page.route("**/notifications**", async (r) => fulfillJson(r, []));
  50  |   await page.route("**/api/notifications**", async (r) => fulfillJson(r, []));
  51  | }
  52  | 
  53  | test.describe("Admin Commission Management", () => {
  54  |   let rates: any[];
  55  |   let tiers: any[];
  56  | 
  57  |   test.beforeEach(async ({ page }) => {
  58  |     rates = [
  59  |       { id: 1, category_slug: "electronics", category_display_name: "Electronics", rate_percent: 0.08, is_active: true },
  60  |       { id: 2, category_slug: "fashion", category_display_name: "Fashion", rate_percent: 0.12, is_active: true },
  61  |     ];
  62  | 
  63  |     tiers = [
  64  |       { id: 1, badge_level: "bronze", commission_rate: 0.05, min_fulfilled_orders: 0, is_active: true },
  65  |       { id: 2, badge_level: "silver", commission_rate: 0.08, min_fulfilled_orders: 50, is_active: true },
  66  |     ];
  67  | 
  68  |     // Global config (commission.py router — /commission/global)
  69  |     await page.route("**/commission/global", async (route) => {
  70  |       if (route.request().method() === "GET") {
  71  |         await fulfillJson(route, {
  72  |           default_rate: 0.1,
  73  |           min_order: 50,
  74  |           max_cap: 1000,
  75  |           is_active: true,
  76  |         });
  77  |       } else {
  78  |         await route.continue();
  79  |       }
  80  |     });
  81  | 
  82  |     // Admin commission routes
  83  |     await page.route("**/admin/commission/**/rates", async (route) => {
  84  |       if (route.request().method() === "GET") {
  85  |         await fulfillJson(route, rates);
  86  |       } else {
  87  |         const body = route.request().postDataJSON();
  88  |         const newRate = {
  89  |           id: rates.length + 1,
  90  |           category_slug: body.category_slug,
  91  |           category_display_name: body.category_display_name,
  92  |           rate_percent: body.rate,
  93  |           is_active: body.is_active ?? true,
  94  |         };
  95  |         rates.push(newRate);
  96  |         await fulfillJson(route, newRate, 201);
  97  |       }
  98  |     });
  99  | 
  100 |     await page.route("**/admin/commission/**/badge-tiers", async (route) => {
  101 |       if (route.request().method() === "GET") {
  102 |         await fulfillJson(route, tiers);
  103 |       } else {
  104 |         const body = route.request().postDataJSON();
  105 |         const newTier = {
  106 |           id: tiers.length + 1,
  107 |           badge_level: body.badge_level,
  108 |           commission_rate: body.commission_rate,
  109 |           min_fulfilled_orders: body.min_fulfilled_orders ?? 0,
  110 |           is_active: body.is_active ?? true,
  111 |         };
  112 |         tiers.push(newTier);
  113 |         await fulfillJson(route, newTier, 201);
  114 |       }
  115 |     });
  116 | 
  117 |     // Suppliers list for overview
  118 |     await page.route("**/commission/suppliers**", async (route) => {
  119 |       await fulfillJson(route, {
  120 |         items: [
  121 |           { supplier_id: 101, business_name: "Mock Supply", current_rate: 0.1, total_earned: 450, order_count: 12 },
  122 |         ],
  123 |         total: 1, page: 1, page_size: 25, total_pages: 1,
  124 |       });
  125 |     });
  126 | 
  127 |     await mockAdminSession(page);
  128 |   });
```