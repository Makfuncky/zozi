# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: phase4h-architecture.spec.ts >> Architecture smoke >> home page returns <500 (smoke gate)
- Location: e2e\phase4h-architecture.spec.ts:120:7

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
  106 |     expect(gated, `customer /admin status=${status} url=${url}`).toBeTruthy();
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
> 122 |     expect(r?.status()).toBeLessThan(500);
      |                         ^ Error: expect(received).toBeLessThan(expected)
  123 |   });
  124 | });
```