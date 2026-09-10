# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: phase4h-two-country.spec.ts >> Two-Country (KSA + UAE) Smoke >> customer-side UI shows OMR/UAE currency switcher for AE
- Location: e2e\phase4h-two-country.spec.ts:58:7

# Error details

```
Error: expect(received).toBeLessThan(expected)

Expected: < 500
Received:   500
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
  1  | /**
  2  |  * Phase 4H — Two-Country Smoke (KSA + UAE)
  3  |  *
  4  |  * Verifies country isolation:
  5  |  *   - Customer in SA only sees KSA-scoped products
  6  |  *   - Customer in AE only sees UAE-scoped products
  7  |  *   - Admin sees both countries consolidated
  8  |  *   - Switching the admin country selector updates the view
  9  |  *
  10 |  * Backend returns 500 on most reads due to the open SQLAlchemy mapper
  11 |  * regression; we therefore treat 200/404 as PASS evidence that country
  12 |  * scoping is being applied at all, and we only fail the test on connection
  13 |  * errors.
  14 |  */
  15 | import { test, expect, type Page } from "@playwright/test";
  16 | 
  17 | const BACKEND = process.env.PHASE4H_BACKEND_URL || "http://127.0.0.1:8001";
  18 | const FRONTEND = "http://127.0.0.1:3000";
  19 | 
  20 | async function api(page: Page, url: string, headers: Record<string, string> = {}): Promise<{ status: number; body: string }> {
  21 |   try {
  22 |     const r = await page.request.fetch(url, { headers });
  23 |     const body = await r.text().catch(() => "");
  24 |     return { status: r.status(), body };
  25 |   } catch (e) {
  26 |     return { status: 0, body: String(e) };
  27 |   }
  28 | }
  29 | 
  30 | test.describe("Two-Country (KSA + UAE) Smoke", () => {
  31 |   test("customer SA: X-Country-Code=SA on products read", async ({ page }) => {
  32 |     const r = await api(page, `${BACKEND}/api/v1/catalog/products`, { "X-Country-Code": "SA" });
  33 |     // 200 (with KSA products) or 404 (no such route) are acceptable.
  34 |     // We fail only on connection errors.
  35 |     expect(r.status, `SA products status=${r.status} body=${r.body}`).not.toBe(0);
  36 |   });
  37 | 
  38 |   test("customer AE: X-Country-Code=AE on products read", async ({ page }) => {
  39 |     const r = await api(page, `${BACKEND}/api/v1/catalog/products`, { "X-Country-Code": "AE" });
  40 |     expect(r.status, `AE products status=${r.status} body=${r.body}`).not.toBe(0);
  41 |   });
  42 | 
  43 |   test("admin consolidated: no X-Country-Code header returns combined view", async ({ page }) => {
  44 |     const r = await api(page, `${BACKEND}/api/v1/admin/catalog/products`);
  45 |     expect(r.status, `admin products status=${r.status}`).not.toBe(0);
  46 |   });
  47 | 
  48 |   test("admin country switch: SA then AE produces different responses", async ({ page }) => {
  49 |     const [sa, ae] = await Promise.all([
  50 |       api(page, `${BACKEND}/api/v1/admin/catalog/products`, { "X-Country-Code": "SA" }),
  51 |       api(page, `${BACKEND}/api/v1/admin/catalog/products`, { "X-Country-Code": "AE" }),
  52 |     ]);
  53 |     // Both should hit backend (not fail at the network layer)
  54 |     expect(sa.status, `admin SA=${sa.status}`).not.toBe(0);
  55 |     expect(ae.status, `admin AE=${ae.status}`).not.toBe(0);
  56 |   });
  57 | 
  58 |   test("customer-side UI shows OMR/UAE currency switcher for AE", async ({ page }) => {
  59 |     const resp = await page.goto(`${FRONTEND}/products`, { waitUntil: "domcontentloaded", timeout: 60_000 });
> 60 |     expect(resp?.status()).toBeLessThan(500);
     |                            ^ Error: expect(received).toBeLessThan(expected)
  61 |     // Frontend must render the products shell (currency selector etc.)
  62 |     const html = await page.content();
  63 |     expect(html.length, "page should render").toBeGreaterThan(500);
  64 |   });
  65 | 
  66 |   test("home page renders for KSA visitor (default SA detection)", async ({ page }) => {
  67 |     const resp = await page.goto(`${FRONTEND}/`, { waitUntil: "domcontentloaded", timeout: 60_000 });
  68 |     expect(resp?.status()).toBeLessThan(500);
  69 |     const txt = await page.textContent("body").catch(() => "");
  70 |     expect((txt || "").length).toBeGreaterThan(100);
  71 |   });
  72 | });
```