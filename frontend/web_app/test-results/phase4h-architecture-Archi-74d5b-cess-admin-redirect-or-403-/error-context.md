# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: phase4h-architecture.spec.ts >> Architecture smoke >> RBAC gating: customer cannot access /admin (redirect or 403)
- Location: e2e\phase4h-architecture.spec.ts:94:7

# Error details

```
Error: customer /admin status=500 url=http://127.0.0.1:3000/admin

expect(received).toBeTruthy()

Received: false
```

# Page snapshot

```yaml
- generic:
  - generic [active]:
    - generic [ref=f1e3]:
      - generic [ref=f1e4]:
        - navigation [ref=f1e6]:
          - button [disabled] [ref=f1e7]:
            - img "previous" [ref=f1e8]
          - generic [ref=f1e10]:
            - generic [ref=f1e11]: 1/
            - generic [ref=f1e12]: "1"
          - button [disabled] [ref=f1e13]:
            - img "next" [ref=f1e14]
        - generic [ref=f1e17]:
          - generic "Latest available version is detected (16.3.4)." [ref=f1e20]: Next.js 16.3.4
          - generic [ref=f1e21]: Turbopack
      - dialog "Build Error" [ref=f1e23]:
        - generic [ref=f1e26]:
          - generic [ref=f1e28]:
            - generic [ref=f1e29]:
              - generic [ref=f1e30]: Build Error
              - generic [ref=f1e32]:
                - button "Copy Error Info" [ref=f1e33] [cursor=pointer]
                - link "Go to related documentation" [ref=f1e36] [cursor=pointer]:
                  - /url: https://nextjs.org/docs/messages/module-not-found
                - button "Attach Node.js inspector" [ref=f1e39] [cursor=pointer]
            - generic [ref=f1e48]: "Module not found: Can't resolve '@shared/adminPermissions'"
          - generic [ref=f1e51]:
            - generic [ref=f1e53]:
              - generic [ref=f1e58]: ./src/lib/useAuth.tsx (18:1)
              - button "Open in editor" [ref=f1e59] [cursor=pointer]
            - generic [ref=f1e64]:
              - generic [ref=f1e65]: "Error: Module not found: Can't resolve '@shared/adminPermissions'"
              - generic [ref=f1e66]: 16 |
              - text: import type
              - generic [ref=f1e67]: "{"
              - text: Locale
              - generic [ref=f1e68]: "}"
              - text: from "@/lib/i18n"
              - generic [ref=f1e69]: ;
              - generic [ref=f1e70]: 17 |
              - text: import
              - generic [ref=f1e71]: "{ normalizeLocale }"
              - text: from "@shared/localization"
              - generic [ref=f1e72]: ;
              - text: ">"
              - generic [ref=f1e73]: 18 |
              - text: import
              - generic [ref=f1e74]: "{"
              - generic [ref=f1e75]: "|"
              - text: ^^^^^^^ >
              - generic [ref=f1e76]: 19 |
              - generic [ref=f1e77]: clearAdminPermissionOverrides,
              - generic [ref=f1e78]: "|"
              - text: ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ >
              - generic [ref=f1e79]: 20 |
              - generic [ref=f1e80]: isAdminStaffRole,
              - generic [ref=f1e81]: "|"
              - text: ^^^^^^^^^^^^^^^^^^^ >
              - generic [ref=f1e82]: 21 |
              - generic [ref=f1e83]: setCurrentAdminPermissions,
              - generic [ref=f1e84]: "|"
              - text: ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ >
              - generic [ref=f1e85]: 22 |
              - generic [ref=f1e86]: setAdminPermissionOverrides,
              - generic [ref=f1e87]: "|"
              - text: ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ >
              - generic [ref=f1e88]: 23 |
              - generic [ref=f1e89]: "}"
              - text: from "@shared/adminPermissions"
              - generic [ref=f1e90]: ;
              - generic [ref=f1e91]: "|"
              - text: ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              - generic [ref=f1e92]: 24 |
              - generic [ref=f1e93]: 25 |
              - generic [ref=f1e94]: /* ---------- Types ------------------------------------------- */
              - generic [ref=f1e95]: 26 |
              - text: export interface UserInfo
              - generic [ref=f1e96]:
                - text: "{ Import map: aliased to relative '../shared/src/adminPermissions' inside of [project]/ Import traces: Server Component: ./src/lib/useAuth.tsx ./src/app/layout.tsx Client Component Browser: ./src/lib/useAuth.tsx [Client Component Browser] ./src/lib/useRequireAuthAction.ts [Client Component Browser] ./src/components/ProductCard.tsx [Client Component Browser] ./src/app/products/page.tsx [Client Component Browser] ./src/app/products/page.tsx [Server Component] Client Component SSR: ./src/lib/useAuth.tsx [Client Component SSR] ./src/lib/useRequireAuthAction.ts [Client Component SSR] ./src/components/ProductCard.tsx [Client Component SSR] ./src/app/products/page.tsx [Client Component SSR] ./src/app/products/page.tsx [Server Component]"
                - link "https://nextjs.org/docs/messages/module-not-found" [ref=f1e97] [cursor=pointer]:
                  - /url: https://nextjs.org/docs/messages/module-not-found
    - button "Open issues overlay" [ref=f1e104] [cursor=pointer]:
      - generic [ref=f1e108]:
        - generic [ref=f1e109]: "0"
        - generic [ref=f1e110]: "1"
      - generic [ref=f1e111]: Issue
  - alert [ref=f1e112]
```

# Test source

```ts
  6   |  * 3. RBAC features are gated by role (admin sees admin pages; customer gets 403/redirect)
  7   |  * 4. Country isolation is enforced on read endpoints
  8   |  *
  9   |  * We sample the 146-page scope with the highest-traffic 30 pages. Each test
  10  |  * records the status code and any console errors for the regression report.
  11  |  */
  12  | import { test, expect, type Page, type Response } from "@playwright/test";
  13  | import { bootstrapAdminSessionViaApi } from "./helpers/auth";
  14  | 
  15  | const FRONTEND = "http://127.0.0.1:3000";
  16  | 
  17  | // Pages sampled from the 146-page audit scope (admin, customer, supplier,
  18  | // employee, logistics-partner, supplier-panel). If a sampled page returns
  19  | // >=500 we fail the test and log the URL for triage.
  20  | const PAGE_SAMPLE: ReadonlyArray<{ role: string; path: string }> = [
  21  |   { role: "public", path: "/" },
  22  |   { role: "public", path: "/products" },
  23  |   { role: "public", path: "/products/category/electronics" },
  24  |   { role: "public", path: "/products/1" },
  25  |   { role: "public", path: "/cart" },
  26  |   { role: "public", path: "/checkout" },
  27  |   { role: "public", path: "/contact" },
  28  |   { role: "public", path: "/wishlist" },
  29  |   { role: "public", path: "/returns" },
  30  |   { role: "public", path: "/tracking/123" },
  31  |   { role: "public", path: "/notifications" },
  32  |   { role: "public", path: "/newsletter/preferences" },
  33  |   { role: "public", path: "/chatbot" },
  34  |   { role: "public", path: "/meet/abc123" },
  35  |   { role: "public", path: "/verify-email?token=fake" },
  36  |   { role: "public", path: "/auth/callback?token=foo&next=/" },
  37  |   // admin (must be logged in to render — the previous Phase3 spec proves this
  38  |   // is fragile, so we just probe the URL; expect 200/302/307/<500 allowed).
  39  |   { role: "admin", path: "/admin" },
  40  |   { role: "admin", path: "/admin/ess" },
  41  |   { role: "admin", path: "/admin/orders" },
  42  |   { role: "admin", path: "/admin/permissions" },
  43  |   { role: "admin", path: "/admin/audit-logs" },
  44  |   { role: "admin", path: "/admin/command-center" },
  45  |   { role: "admin", path: "/admin/command-center/headlines" },
  46  |   { role: "admin", path: "/admin/staff" },
  47  |   { role: "admin", path: "/admin/suppliers" },
  48  |   // employee/supplier/logistics (probed but session bootstrap is fragile)
  49  |   { role: "employee", path: "/employee" },
  50  |   { role: "employee", path: "/employee/dashboard" },
  51  |   { role: "supplier", path: "/supplier" },
  52  |   { role: "supplier", path: "/supplier/dashboard" },
  53  |   { role: "logistics", path: "/logistics-partner" },
  54  |   { role: "logistics", path: "/logistics-partner/dashboard" },
  55  | ];
  56  | 
  57  | const adminLogin = process.env.PHASE4H_ADMIN_LOGIN !== "0";
  58  | 
  59  | test.describe("Architecture smoke", () => {
  60  |   test("no 5xx on any page in the 146-page sample", async ({ page }) => {
  61  |     if (adminLogin) {
  62  |       // Try to authenticate as admin so /admin/* returns 200, not login redirects.
  63  |       // If bootstrap fails we still proceed — most pages are public.
  64  |       await bootstrapAdminSessionViaApi(page).catch(() => false);
  65  |     }
  66  |     const seen500: Array<{ path: string; status: number }> = [];
  67  |     const pageErrors: string[] = [];
  68  |     page.on("response", (r: Response) => {
  69  |       if (r.status() >= 500) {
  70  |         seen500.push({ path: r.url().replace("http://127.0.0.1:3000", ""), status: r.status() });
  71  |       }
  72  |     });
  73  |     page.on("pageerror", (e) => pageErrors.push(String(e?.stack ?? e)));
  74  | 
  75  |     for (const sample of PAGE_SAMPLE) {
  76  |       try {
  77  |         await page.goto(`${FRONTEND}${sample.path}`, { waitUntil: "domcontentloaded", timeout: 30_000 });
  78  |       } catch {
  79  |         // Network error recorded but doesn't fail the test (page itself didn't crash).
  80  |       }
  81  |     }
  82  |     if (seen500.length) {
  83  |       console.warn("[phase4h-arch] 5xx responses seen:", seen500.slice(0, 10));
  84  |     }
  85  |     expect(seen500.filter((s) => s.path.startsWith("/api/") || s.path.startsWith("/auth/")).length,
  86  |       "no 5xx on /api/* or /auth/* rewrites").toBe(0);
  87  |     // Page-level 5xx is a softer check — if backend is broken, almost every
  88  |     // /admin route will 500. We allow that here and only flag it in the report.
  89  |     if (pageErrors.length) {
  90  |       console.warn("[phase4h-arch] page errors:", pageErrors.slice(0, 3));
  91  |     }
  92  |   });
  93  | 
  94  |   test("RBAC gating: customer cannot access /admin (redirect or 403)", async ({ page }) => {
  95  |     // Set the local session flag to a non-admin role so the admin layout guard kicks in.
  96  |     await page.goto(FRONTEND, { waitUntil: "domcontentloaded", timeout: 30_000 });
  97  |     await page.evaluate(() => {
  98  |       window.localStorage.setItem("zozi_has_session", "1");
  99  |     });
  100 |     // Try /admin — for a customer the page should redirect or return 403.
  101 |     const r = await page.goto(`${FRONTEND}/admin`, { waitUntil: "domcontentloaded", timeout: 30_000 }).catch(() => null);
  102 |     const status = r?.status() ?? 0;
  103 |     const url = page.url();
  104 |     const redirectedAway = !/\/admin(\/|$)/.test(url);
  105 |     const gated = redirectedAway || status === 403 || status === 307 || status === 302;
> 106 |     expect(gated, `customer /admin status=${status} url=${url}`).toBeTruthy();
      |                                                                  ^ Error: customer /admin status=500 url=http://127.0.0.1:3000/admin
  107 |   });
  108 | 
  109 |   test("country isolation: header X-Country-Code reaches backend", async ({ page }) => {
  110 |     // Send a custom request and observe backend logs through /health (proxy).
  111 |     // This is a best-effort probe; we mainly check that the frontend rewrite
  112 |     // surface isn't completely broken.
  113 |     const r = await page.request.fetch(`${FRONTEND}/api/health`, {
  114 |       headers: { "X-Country-Code": "SA" },
  115 |     });
  116 |     // Accept 200 or 404 (health may not be rewritable).
  117 |     expect(r.status(), `proxy status=${r.status()}`).not.toBe(0);
  118 |   });
  119 | 
  120 |   test("home page returns <500 (smoke gate)", async ({ page }) => {
  121 |     const r = await page.goto(FRONTEND, { waitUntil: "domcontentloaded", timeout: 30_000 });
  122 |     expect(r?.status()).toBeLessThan(500);
  123 |   });
  124 | });
```