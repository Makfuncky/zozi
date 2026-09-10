# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: phase3-regression-admin-customer.spec.ts >> Customer Regression (Phase 2C + 2D) >> meet/[room] shows Beta badge
- Location: e2e\phase3-regression-admin-customer.spec.ts:202:9

# Error details

```
Error: status=500

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
  169 |         expect(ok, `status=${status}`).toBeTruthy();
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
> 204 |         expect(ok, `status=${status}`).toBeTruthy();
      |                                        ^ Error: status=500
  205 |     });
  206 | });
```