# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: phase3-regression-employee-supplier-logistics.spec.ts >> Phase 3 — Employee Regression >> employee/payroll shows Decimal payslips
- Location: e2e\phase3-regression-employee-supplier-logistics.spec.ts:156:7

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
  66  |     await setupAuthMocks(page, "employee", EMPLOYEE_USERS[0]);
  67  |     await fulfillJson(page, /\/api\/employee\/dashboard/, {
  68  |       employee: { id: 1, name: "Employee Demo" },
  69  |       tasks: [],
  70  |       schedule: [],
  71  |       kpis: {},
  72  |       notifications: [],
  73  |       upcoming: [],
  74  |     });
  75  |     const { status, url } = await gotoAndVerify(page, "/employee/dashboard", /\/employee\/dashboard/);
  76  |     expect(status, `${AUDIT_TAG} dashboard status`).toBeLessThan(500);
  77  |     expect(url, `${AUDIT_TAG} dashboard url`).toMatch(/\/employee\/dashboard/);
  78  |   });
  79  | 
  80  |   test("employee/attendance loads with history param", async ({ page }) => {
  81  |     test.setTimeout(90_000);
  82  |     await setupAuthMocks(page, "employee", EMPLOYEE_USERS[0]);
  83  |     await fulfillJson(page, /\/api\/employee\/attendance/, {
  84  |       records: [{ id: 1, date: "2026-09-01", status: "present" }],
  85  |       summary: { present: 1, absent: 0 },
  86  |     });
  87  |     const { status } = await gotoAndVerify(page, "/employee/attendance", /\/employee\/attendance/);
  88  |     expect(status).toBeLessThan(500);
  89  |   });
  90  | 
  91  |   test("employee/leaves loads with array response", async ({ page }) => {
  92  |     test.setTimeout(90_000);
  93  |     await setupAuthMocks(page, "employee", EMPLOYEE_USERS[0]);
  94  |     await fulfillJson(page, /\/api\/employee\/leaves/, []);
  95  |     const { status } = await gotoAndVerify(page, "/employee/leaves", /\/employee\/leaves/);
  96  |     expect(status).toBeLessThan(500);
  97  |   });
  98  | 
  99  |   test("employee/performance loads with reviews", async ({ page }) => {
  100 |     test.setTimeout(90_000);
  101 |     await setupAuthMocks(page, "employee", EMPLOYEE_USERS[0]);
  102 |     await fulfillJson(page, /\/api\/employee\/performance/, {
  103 |       reviews: [],
  104 |       goals: [],
  105 |       kpis: {},
  106 |     });
  107 |     const { status } = await gotoAndVerify(page, "/employee/performance", /\/employee\/performance/);
  108 |     expect(status).toBeLessThan(500);
  109 |   });
  110 | 
  111 |   test("employee/profile loads with Pydantic body", async ({ page }) => {
  112 |     test.setTimeout(90_000);
  113 |     await setupAuthMocks(page, "employee", EMPLOYEE_USERS[0]);
  114 |     await fulfillJson(page, /\/api\/employee\/profile/, {
  115 |       id: 1,
  116 |       full_name: "Employee Demo",
  117 |       email: EMPLOYEE_USERS[0],
  118 |       role: "employee",
  119 |     });
  120 |     const { status } = await gotoAndVerify(page, "/employee/profile", /\/employee\/profile/);
  121 |     expect(status).toBeLessThan(500);
  122 |   });
  123 | 
  124 |   test("employee/schedule clock-in works", async ({ page }) => {
  125 |     test.setTimeout(90_000);
  126 |     await setupAuthMocks(page, "employee", EMPLOYEE_USERS[0]);
  127 |     await fulfillJson(page, /\/api\/employee\/schedule/, {
  128 |       shifts: [],
  129 |       today: { date: "2026-09-03" },
  130 |     });
  131 |     const { status } = await gotoAndVerify(page, "/employee/schedule", /\/employee\/schedule/);
  132 |     expect(status).toBeLessThan(500);
  133 |   });
  134 | 
  135 |   test("employee index has no dead links", async ({ page }) => {
  136 |     test.setTimeout(90_000);
  137 |     await setupAuthMocks(page, "employee", EMPLOYEE_USERS[0]);
  138 |     const resp = await page.goto("/employee", { waitUntil: "domcontentloaded", timeout: 60_000 });
  139 |     expect(resp?.status()).toBeLessThan(500);
  140 |     const expectedLinks = [
  141 |       "/employee/dashboard",
  142 |       "/employee/profile",
  143 |       "/employee/payroll",
  144 |       "/employee/leaves",
  145 |       "/employee/attendance",
  146 |       "/employee/performance",
  147 |       "/employee/training",
  148 |       "/employee/documents",
  149 |     ];
  150 |     for (const link of expectedLinks) {
  151 |       const count = await page.locator(`a[href='${link}']`).count();
  152 |       expect(count, `${AUDIT_TAG} employee link ${link}`).toBeGreaterThan(0);
  153 |     }
  154 |   });
  155 | 
  156 |   test("employee/payroll shows Decimal payslips", async ({ page }) => {
  157 |     test.setTimeout(90_000);
  158 |     await setupAuthMocks(page, "employee", EMPLOYEE_USERS[0]);
  159 |     await fulfillJson(page, /\/api\/employee\/payroll/, {
  160 |       payslips: [
  161 |         { id: 1, period: "2026-08", gross: "3500.00", net: "2800.00", currency: "AED" },
  162 |       ],
  163 |       totals: { gross: "3500.00", net: "2800.00" },
  164 |     });
  165 |     const { status } = await gotoAndVerify(page, "/employee/payroll", /\/employee\/payroll/);
> 166 |     expect(status).toBeLessThan(500);
      |                    ^ Error: expect(received).toBeLessThan(expected)
  167 |   });
  168 | });
  169 | 
  170 | test.describe("Phase 3 — Supplier Regression", () => {
  171 |   test("supplier/dashboard loads", async ({ page }) => {
  172 |     test.setTimeout(90_000);
  173 |     await setupAuthMocks(page, "supplier", SUPPLIER_USERS[0]);
  174 |     await fulfillJson(page, /\/api\/supplier\/dashboard/, {
  175 |       stats: { products: 0, orders: 0, revenue: "0.00" },
  176 |       recent: [],
  177 |     });
  178 |     const { status } = await gotoAndVerify(page, "/supplier/dashboard", /\/supplier\/dashboard/);
  179 |     expect(status).toBeLessThan(500);
  180 |   });
  181 | 
  182 |   test("supplier/products/add POST works", async ({ page }) => {
  183 |     test.setTimeout(90_000);
  184 |     await setupAuthMocks(page, "supplier", SUPPLIER_USERS[0]);
  185 |     await fulfillJson(page, /\/api\/supplier\/products/, []);
  186 |     const { status } = await gotoAndVerify(page, "/supplier/products/add", /\/supplier\/products\/add/);
  187 |     expect(status).toBeLessThan(500);
  188 |   });
  189 | 
  190 |   test("supplier/upload uses AI staging (ADR-007)", async ({ page }) => {
  191 |     test.setTimeout(90_000);
  192 |     await setupAuthMocks(page, "supplier", SUPPLIER_USERS[0]);
  193 |     await fulfillJson(page, /\/api\/supplier\/upload/, { staged: [], ai: { enabled: true } });
  194 |     const { status } = await gotoAndVerify(page, "/supplier/upload", /\/supplier\/upload/);
  195 |     expect(status).toBeLessThan(500);
  196 |   });
  197 | 
  198 |   test("supplier/list-product has CoC tree", async ({ page }) => {
  199 |     test.setTimeout(90_000);
  200 |     await setupAuthMocks(page, "supplier", SUPPLIER_USERS[0]);
  201 |     await fulfillJson(page, /\/api\/catalog\/coc-tree/, { tree: [{ id: 1, name: "Root", children: [] }] });
  202 |     const { status } = await gotoAndVerify(page, "/supplier/list-product", /\/supplier\/list-product/);
  203 |     expect(status).toBeLessThan(500);
  204 |   });
  205 | 
  206 |   test("supplier/credibility has badge catalog", async ({ page }) => {
  207 |     test.setTimeout(90_000);
  208 |     await setupAuthMocks(page, "supplier", SUPPLIER_USERS[0]);
  209 |     await fulfillJson(page, /\/api\/supplier\/credibility/, {
  210 |       badges: [{ code: "verified", label: "Verified" }],
  211 |       score: 0,
  212 |     });
  213 |     const { status } = await gotoAndVerify(page, "/supplier/credibility", /\/supplier\/credibility/);
  214 |     expect(status).toBeLessThan(500);
  215 |   });
  216 | 
  217 |   test("supplier/payouts request uses Decimal", async ({ page }) => {
  218 |     test.setTimeout(90_000);
  219 |     await setupAuthMocks(page, "supplier", SUPPLIER_USERS[0]);
  220 |     await fulfillJson(page, /\/api\/supplier\/payouts/, {
  221 |       payouts: [{ id: 1, amount: "150.50", currency: "AED", status: "requested" }],
  222 |       total: "150.50",
  223 |     });
  224 |     const { status } = await gotoAndVerify(page, "/supplier/payouts", /\/supplier\/payouts/);
  225 |     expect(status).toBeLessThan(500);
  226 |   });
  227 | 
  228 |   test("supplier/orders loads", async ({ page }) => {
  229 |     test.setTimeout(90_000);
  230 |     await setupAuthMocks(page, "supplier", SUPPLIER_USERS[0]);
  231 |     await fulfillJson(page, /\/api\/supplier\/orders/, { orders: [] });
  232 |     const { status } = await gotoAndVerify(page, "/supplier/orders", /\/supplier\/orders/);
  233 |     expect(status).toBeLessThan(500);
  234 |   });
  235 | 
  236 |   test("supplier/orders/[id] loads with status update", async ({ page }) => {
  237 |     test.setTimeout(90_000);
  238 |     await setupAuthMocks(page, "supplier", SUPPLIER_USERS[0]);
  239 |     await fulfillJson(page, /\/api\/supplier\/orders\/\d+/, { id: 1, status: "pending" });
  240 |     const { status } = await gotoAndVerify(page, "/supplier/orders/1", /\/supplier\/orders\/1/);
  241 |     expect(status).toBeLessThan(500);
  242 |   });
  243 | 
  244 |   test("supplier/products/[id] loads", async ({ page }) => {
  245 |     test.setTimeout(90_000);
  246 |     await setupAuthMocks(page, "supplier", SUPPLIER_USERS[0]);
  247 |     await fulfillJson(page, /\/api\/supplier\/products\/\d+/, { id: 1, name: "Test product" });
  248 |     const { status } = await gotoAndVerify(page, "/supplier/products/1", /\/supplier\/products\/1/);
  249 |     expect(status).toBeLessThan(500);
  250 |   });
  251 | 
  252 |   test("supplier/support loads", async ({ page }) => {
  253 |     test.setTimeout(90_000);
  254 |     await setupAuthMocks(page, "supplier", SUPPLIER_USERS[0]);
  255 |     await fulfillJson(page, /\/api\/supplier\/support/, { tickets: [] });
  256 |     const { status } = await gotoAndVerify(page, "/supplier/support", /\/supplier\/support/);
  257 |     expect(status).toBeLessThan(500);
  258 |   });
  259 | 
  260 |   test("supplier/notification-preferences loads", async ({ page }) => {
  261 |     test.setTimeout(90_000);
  262 |     await setupAuthMocks(page, "supplier", SUPPLIER_USERS[0]);
  263 |     await fulfillJson(page, /\/api\/supplier\/notification-preferences/, {
  264 |       preferences: { email: true, sms: false, push: true },
  265 |     });
  266 |     const { status } = await gotoAndVerify(page, "/supplier/notification-preferences", /\/supplier\/notification-preferences/);
```