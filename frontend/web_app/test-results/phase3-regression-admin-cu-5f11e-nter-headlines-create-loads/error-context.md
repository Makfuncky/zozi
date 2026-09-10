# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: phase3-regression-admin-customer.spec.ts >> Admin Regression (Phase 2A + 2B) >> admin/command-center/headlines/create loads
- Location: e2e\phase3-regression-admin-customer.spec.ts:108:9

# Error details

```
Error: admin session bootstrap

expect(received).toBeTruthy()

Received: false
```

# Page snapshot

```yaml
- generic:
  - generic [active]:
    - generic [ref=e3]:
      - generic [ref=e4]:
        - navigation [ref=e6]:
          - button [disabled] [ref=e7]:
            - img "previous" [ref=e8]
          - generic [ref=e10]:
            - generic [ref=e11]: 1/
            - generic [ref=e12]: "1"
          - button [disabled] [ref=e13]:
            - img "next" [ref=e14]
        - generic [ref=e17]:
          - generic "Latest available version is detected (16.3.4)." [ref=e20]: Next.js 16.3.4
          - generic [ref=e21]: Turbopack
      - dialog "Build Error" [ref=e23]:
        - generic [ref=e26]:
          - generic [ref=e28]:
            - generic [ref=e29]:
              - generic [ref=e30]: Build Error
              - generic [ref=e32]:
                - button "Copy Error Info" [ref=e33] [cursor=pointer]
                - link "Go to related documentation" [ref=e36] [cursor=pointer]:
                  - /url: https://nextjs.org/docs/messages/module-not-found
                - button "Attach Node.js inspector" [ref=e39] [cursor=pointer]
            - generic [ref=e48]: "Module not found: Can't resolve '@shared/adminPermissions'"
          - generic [ref=e51]:
            - generic [ref=e53]:
              - generic [ref=e58]: ./src/lib/useAuth.tsx (18:1)
              - button "Open in editor" [ref=e59] [cursor=pointer]
            - generic [ref=e64]:
              - generic [ref=e65]: "Error: Module not found: Can't resolve '@shared/adminPermissions'"
              - generic [ref=e66]: 16 |
              - text: import type
              - generic [ref=e67]: "{"
              - text: Locale
              - generic [ref=e68]: "}"
              - text: from "@/lib/i18n"
              - generic [ref=e69]: ;
              - generic [ref=e70]: 17 |
              - text: import
              - generic [ref=e71]: "{ normalizeLocale }"
              - text: from "@shared/localization"
              - generic [ref=e72]: ;
              - text: ">"
              - generic [ref=e73]: 18 |
              - text: import
              - generic [ref=e74]: "{"
              - generic [ref=e75]: "|"
              - text: ^^^^^^^ >
              - generic [ref=e76]: 19 |
              - generic [ref=e77]: clearAdminPermissionOverrides,
              - generic [ref=e78]: "|"
              - text: ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ >
              - generic [ref=e79]: 20 |
              - generic [ref=e80]: isAdminStaffRole,
              - generic [ref=e81]: "|"
              - text: ^^^^^^^^^^^^^^^^^^^ >
              - generic [ref=e82]: 21 |
              - generic [ref=e83]: setCurrentAdminPermissions,
              - generic [ref=e84]: "|"
              - text: ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ >
              - generic [ref=e85]: 22 |
              - generic [ref=e86]: setAdminPermissionOverrides,
              - generic [ref=e87]: "|"
              - text: ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ >
              - generic [ref=e88]: 23 |
              - generic [ref=e89]: "}"
              - text: from "@shared/adminPermissions"
              - generic [ref=e90]: ;
              - generic [ref=e91]: "|"
              - text: ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              - generic [ref=e92]: 24 |
              - generic [ref=e93]: 25 |
              - generic [ref=e94]: /* ---------- Types ------------------------------------------- */
              - generic [ref=e95]: 26 |
              - text: export interface UserInfo
              - generic [ref=e96]:
                - text: "{ Import map: aliased to relative '../shared/src/adminPermissions' inside of [project]/ Import traces: Server Component: ./src/lib/useAuth.tsx ./src/app/layout.tsx Client Component Browser: ./src/lib/useAuth.tsx [Client Component Browser] ./src/lib/useRequireAuthAction.ts [Client Component Browser] ./src/components/ProductCard.tsx [Client Component Browser] ./src/app/products/page.tsx [Client Component Browser] ./src/app/products/page.tsx [Server Component] Client Component SSR: ./src/lib/useAuth.tsx [Client Component SSR] ./src/lib/useRequireAuthAction.ts [Client Component SSR] ./src/components/ProductCard.tsx [Client Component SSR] ./src/app/products/page.tsx [Client Component SSR] ./src/app/products/page.tsx [Server Component]"
                - link "https://nextjs.org/docs/messages/module-not-found" [ref=e97] [cursor=pointer]:
                  - /url: https://nextjs.org/docs/messages/module-not-found
    - button "Open issues overlay" [ref=e104] [cursor=pointer]:
      - generic [ref=e108]:
        - generic [ref=e109]: "0"
        - generic [ref=e110]: "1"
      - generic [ref=e111]: Issue
  - alert [ref=e112]
```

# Test source

```ts
  1   | /**
  2   |  * Phase 3 Regression Spec — Admin (Phase 2A/2B) + Customer (Phase 2C/2D)
  3   |  *
  4   |  * NOTE: This spec is intended to run AFTER frontend dev server has all compile
  5   |  * errors fixed. As of 2026-09-03 the dev server returns 500 on every route due
  6   |  * to three import errors (see _audit_results/reports/11_REGRESSION_RESULTS.md).
  7   |  *
  8   |  * Each test captures: status code, console errors, network errors, and page text
  9   |  * snapshot for failure triage.
  10  |  */
  11  | import { test, expect, type Page, type Response } from "@playwright/test";
  12  | import { bootstrapAdminSessionViaApi, bootstrapSessionViaApi } from "./helpers/auth";
  13  | 
  14  | type NetFailure = { url: string; error: string };
  15  | type ApiCall = { url: string; status: number | string; method?: string };
  16  | 
  17  | async function attachCollectors(page: Page) {
  18  |     const consoleErrors: string[] = [];
  19  |     const pageErrors: string[] = [];
  20  |     const apiCalls: ApiCall[] = [];
  21  |     const netFailures: NetFailure[] = [];
  22  | 
  23  |     page.on("console", (m) => {
  24  |         if (m.type() === "error") consoleErrors.push(m.text());
  25  |     });
  26  |     page.on("pageerror", (e) => pageErrors.push(String(e?.stack ?? e)));
  27  |     page.on("response", (r) => {
  28  |         const u = r.url();
  29  |         if (/127\.0\.0\.1:8001/.test(u) || /^\/(api|auth|admin|__api|uploads|hr)\//.test(u)) {
  30  |             apiCalls.push({ url: u.replace(/http:\/\/127\.0\.0\.1:3000/, ""), status: r.status(), method: r.request().method() });
  31  |         }
  32  |     });
  33  |     page.on("requestfailed", (r) => {
  34  |         const u = r.url();
  35  |         if (/127\.0\.0\.1:8001/.test(u) || /^\/(api|auth|admin|__api|uploads|hr)\//.test(u)) {
  36  |             netFailures.push({ url: u.replace(/http:\/\/127\.0\.0\.1:3000/, ""), error: r.failure()?.errorText ?? "unknown" });
  37  |         }
  38  |     });
  39  | 
  40  |     return { consoleErrors, pageErrors, apiCalls, netFailures };
  41  | }
  42  | 
  43  | async function visit(page: Page, path: string, opts: { expectStatus?: number[] } = {}) {
  44  |     const expectStatus = opts.expectStatus ?? [200, 304];
  45  |     const resp = await page.goto(path, { waitUntil: "domcontentloaded", timeout: 60_000 });
  46  |     const status = resp?.status() ?? 0;
  47  |     return { status, ok: expectStatus.includes(status) };
  48  | }
  49  | 
  50  | // ============================================================
  51  | // ADMIN (Phase 2A + 2B fixes)
  52  | // ============================================================
  53  | test.describe("Admin Regression (Phase 2A + 2B)", () => {
  54  |     test.beforeEach(async ({ page }) => {
  55  |         const ok = await bootstrapAdminSessionViaApi(page);
> 56  |         expect(ok, "admin session bootstrap").toBeTruthy();
      |                                               ^ Error: admin session bootstrap
  57  |     });
  58  | 
  59  |     test("admin/ess loads", async ({ page }) => {
  60  |         const c = await attachCollectors(page);
  61  |         const { status, ok } = await visit(page, "/admin/ess");
  62  |         expect(ok, `status=${status}`).toBeTruthy();
  63  |         await expect(page.locator("text=ESS").first()).toBeVisible({ timeout: 5_000 });
  64  |         if (c.consoleErrors.length) console.warn("admin/ess console errors:", c.consoleErrors);
  65  |     });
  66  | 
  67  |     test("admin/orders loads and shows orders", async ({ page }) => {
  68  |         const c = await attachCollectors(page);
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
```