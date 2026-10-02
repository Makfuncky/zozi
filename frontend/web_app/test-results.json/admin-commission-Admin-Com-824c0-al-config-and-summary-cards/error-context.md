# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin-commission.spec.ts >> Admin Commission Management >> overview tab shows global config and summary cards
- Location: e2e\admin-commission.spec.ts:130:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText(/Commission Management/i)
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByText(/Commission Management/i) with timeout 5000ms
  - waiting for getByText(/Commission Management/i)

```

```yaml
- complementary:
  - text: ZOZI Admin
  - button "Collapse sidebar"
  - paragraph: Admin
  - paragraph: admin
  - textbox "Search nav..."
  - navigation
  - button "Logout"
- banner:
  - text: Admin Workspace
  - heading "Commission" [level=1]
  - paragraph: Platform management and operational control
  - button "Open keyboard shortcuts help": "?"
  - button "Switch to dark theme": 🌙
  - group "Data density":
    - button "Compact density" [pressed]
    - button "Normal density"
    - button "Expanded density"
  - text: admin Admin
- main
- alert
```

# Test source

```ts
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
  44  |   await form.locator("input[type='password']:visible").first().fill("E2eAdmin#2026");
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
  68  |     // Global config (commission.py router â€” /commission/global)
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
  129 | 
  130 |   test("overview tab shows global config and summary cards", async ({ page }) => {
  131 |     await page.waitForTimeout(2000);
> 132 |     await expect(page.getByText(/Commission Management/i)).toBeVisible();
      |                                                            ^ Error: expect(locator).toBeVisible() failed
  133 |     await expect(page.getByText(/Global Commission Configuration/i)).toBeVisible({ timeout: 5000 });
  134 |   });
  135 | 
  136 |   test("category rates tab lists rates and supports add", async ({ page }) => {
  137 |     await page.waitForTimeout(1500);
  138 |     await page.getByRole("tab", { name: /category rates/i }).click();
  139 |     await page.waitForTimeout(1000);
  140 | 
  141 |     await expect(page.getByRole("button", { name: /add category rate/i })).toBeVisible({ timeout: 5000 });
  142 |     await expect(page.getByText(/Electronics/i)).toBeVisible();
  143 | 
  144 |     await page.getByRole("button", { name: /add category rate/i }).click();
  145 |     await expect(page.getByText(/Add Category Rate/i)).toBeVisible({ timeout: 5000 });
  146 | 
  147 |     await page.getByPlaceholder(/electronics/i).fill("home-garden");
  148 |     await page.getByPlaceholder(/Electronics/i).fill("Home & Garden");
  149 |     await page.locator('input[type="number"]').fill("0.07");
  150 |     await page.getByRole("button", { name: /save/i }).click();
  151 |     await page.waitForTimeout(1000);
  152 | 
  153 |     await expect(page.getByText(/Home & Garden/i)).toBeVisible();
  154 |   });
  155 | 
  156 |   test("badge tiers tab lists tiers and supports add", async ({ page }) => {
  157 |     await page.waitForTimeout(1500);
  158 |     await page.getByRole("tab", { name: /badge tiers/i }).click();
  159 |     await page.waitForTimeout(1000);
  160 | 
  161 |     await expect(page.getByRole("button", { name: /add badge tier/i })).toBeVisible({ timeout: 5000 });
  162 |     await expect(page.getByText(/bronze/i)).toBeVisible();
  163 | 
  164 |     await page.getByRole("button", { name: /add badge tier/i }).click();
  165 |     await expect(page.getByText(/Add Badge Tier/i)).toBeVisible({ timeout: 5000 });
  166 | 
  167 |     await page.getByPlaceholder(/bronze/i).fill("gold");
  168 |     await page.locator('input[type="number"]').first().fill("0.12");
  169 |     await page.getByRole("button", { name: /save/i }).click();
  170 |     await page.waitForTimeout(1000);
  171 | 
  172 |     await expect(page.getByText(/gold/i)).toBeVisible();
  173 |   });
  174 | });
  175 | 
  176 | 
  177 | 
```