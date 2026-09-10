# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: phase3-regression-admin-customer.spec.ts >> Customer Regression (Phase 2C + 2D) >> returns loads
- Location: e2e\phase3-regression-admin-customer.spec.ts:167:9

# Error details

```
Error: status=500

expect(received).toBeTruthy()

Received: false
```

# Page snapshot

```yaml
- alert [ref=e1]
```

# Test source

```ts
  69  |         const { status, ok } = await visit(page, "/admin/orders");
  70  |         expect(ok, `status=${status}`).toBeTruthy();
  71  |     });
  72  | 
  73  |     test("admin/permissions loads", async ({ page }) => {
  74  |         const { status, ok } = await visit(page, "/admin/permissions");
  75  |         expect(ok, `status=${status}`).toBeTruthy();
  76  |     });
  77  | 
  78  |     test("admin/tickets/[id] loads", async ({ page }) => {
  79  |         const { status, ok } = await visit(page, "/admin/tickets/1");
  80  |         expect(ok, `status=${status}`).toBeTruthy();
  81  |     });
  82  | 
  83  |     test("admin/staff loads", async ({ page }) => {
  84  |         const { status, ok } = await visit(page, "/admin/staff");
  85  |         expect(ok, `status=${status}`).toBeTruthy();
  86  |     });
  87  | 
  88  |     test("admin/suppliers loads and lists", async ({ page }) => {
  89  |         const { status, ok } = await visit(page, "/admin/suppliers");
  90  |         expect(ok, `status=${status}`).toBeTruthy();
  91  |     });
  92  | 
  93  |     test("admin/audit-logs loads with country filter", async ({ page }) => {
  94  |         const { status, ok } = await visit(page, "/admin/audit-logs");
  95  |         expect(ok, `status=${status}`).toBeTruthy();
  96  |     });
  97  | 
  98  |     test("admin/command-center WebSocket connects", async ({ page }) => {
  99  |         const { status, ok } = await visit(page, "/admin/command-center");
  100 |         expect(ok, `status=${status}`).toBeTruthy();
  101 |     });
  102 | 
  103 |     test("admin/command-center/headlines loads", async ({ page }) => {
  104 |         const { status, ok } = await visit(page, "/admin/command-center/headlines");
  105 |         expect(ok, `status=${status}`).toBeTruthy();
  106 |     });
  107 | 
  108 |     test("admin/command-center/headlines/create loads", async ({ page }) => {
  109 |         const { status, ok } = await visit(page, "/admin/command-center/headlines/create");
  110 |         expect(ok, `status=${status}`).toBeTruthy();
  111 |     });
  112 | });
  113 | 
  114 | // ============================================================
  115 | // CUSTOMER (Phase 2C + 2D fixes)
  116 | // ============================================================
  117 | test.describe("Customer Regression (Phase 2C + 2D)", () => {
  118 |     test("home loads with X-Country-Code header", async ({ page }) => {
  119 |         const c = await attachCollectors(page);
  120 |         const resp = await page.goto("/", { waitUntil: "domcontentloaded", timeout: 60_000 });
  121 |         expect(resp?.status(), "homepage status").toBeLessThan(400);
  122 |         expect(c.consoleErrors.length, "no console errors").toBe(0);
  123 |     });
  124 | 
  125 |     test("verify-email accepts token param", async ({ page }) => {
  126 |         const { status, ok } = await visit(page, "/verify-email?token=fake-token");
  127 |         expect(ok, `status=${status}`).toBeTruthy();
  128 |     });
  129 | 
  130 |     test("auth/callback loads", async ({ page }) => {
  131 |         const { status, ok } = await visit(page, "/auth/callback?token=foo&next=/");
  132 |         expect(ok, `status=${status}`).toBeTruthy();
  133 |     });
  134 | 
  135 |     test("products loads with dynamic categories", async ({ page }) => {
  136 |         const { status, ok } = await visit(page, "/products");
  137 |         expect(ok, `status=${status}`).toBeTruthy();
  138 |     });
  139 | 
  140 |     test("products/category loads", async ({ page }) => {
  141 |         const { status, ok } = await visit(page, "/products/category/electronics");
  142 |         expect(ok, `status=${status}`).toBeTruthy();
  143 |     });
  144 | 
  145 |     test("products/[id] loads with reviews POST", async ({ page }) => {
  146 |         const { status, ok } = await visit(page, "/products/1");
  147 |         expect(ok, `status=${status}`).toBeTruthy();
  148 |     });
  149 | 
  150 |     test("cart loads without 404", async ({ page }) => {
  151 |         const { status, ok } = await visit(page, "/cart");
  152 |         expect(ok, `status=${status}`).toBeTruthy();
  153 |     });
  154 | 
  155 |     test("checkout loads with corrected endpoints", async ({ page }) => {
  156 |         const { status, ok } = await visit(page, "/checkout");
  157 |         expect(ok, `status=${status}`).toBeTruthy();
  158 |     });
  159 | 
  160 |     test("profile loads with all 3 endpoints", async ({ page }) => {
  161 |         const ok = await bootstrapSessionViaApi(page, ["customer@zozi.com", "customer"], "customer123");
  162 |         expect(ok, "customer session bootstrap").toBeTruthy();
  163 |         const { status, ok: visitOk } = await visit(page, "/profile");
  164 |         expect(visitOk, `status=${status}`).toBeTruthy();
  165 |     });
  166 | 
  167 |     test("returns loads", async ({ page }) => {
  168 |         const { status, ok } = await visit(page, "/returns");
> 169 |         expect(ok, `status=${status}`).toBeTruthy();
      |                                        ^ Error: status=500
  170 |     });
  171 | 
  172 |     test("tracking/[id] loads", async ({ page }) => {
  173 |         const { status, ok } = await visit(page, "/tracking/123");
  174 |         expect(ok, `status=${status}`).toBeTruthy();
  175 |     });
  176 | 
  177 |     test("notifications loads", async ({ page }) => {
  178 |         const { status, ok } = await visit(page, "/notifications");
  179 |         expect(ok, `status=${status}`).toBeTruthy();
  180 |     });
  181 | 
  182 |     test("newsletter/preferences loads", async ({ page }) => {
  183 |         const { status, ok } = await visit(page, "/newsletter/preferences");
  184 |         expect(ok, `status=${status}`).toBeTruthy();
  185 |     });
  186 | 
  187 |     test("contact loads", async ({ page }) => {
  188 |         const { status, ok } = await visit(page, "/contact");
  189 |         expect(ok, `status=${status}`).toBeTruthy();
  190 |     });
  191 | 
  192 |     test("wishlist loads", async ({ page }) => {
  193 |         const { status, ok } = await visit(page, "/wishlist");
  194 |         expect(ok, `status=${status}`).toBeTruthy();
  195 |     });
  196 | 
  197 |     test("chatbot shows Beta badge", async ({ page }) => {
  198 |         const { status, ok } = await visit(page, "/chatbot");
  199 |         expect(ok, `status=${status}`).toBeTruthy();
  200 |     });
  201 | 
  202 |     test("meet/[room] shows Beta badge", async ({ page }) => {
  203 |         const { status, ok } = await visit(page, "/meet/abc123");
  204 |         expect(ok, `status=${status}`).toBeTruthy();
  205 |     });
  206 | });
```