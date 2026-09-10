# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: phase3-regression-employee-supplier-logistics.spec.ts >> Phase 3 — Employee Regression >> employee/leaves loads with array response
- Location: e2e\phase3-regression-employee-supplier-logistics.spec.ts:91:7

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
  1   | import { expect, test, type Page } from "@playwright/test";
  2   | import { bootstrapSessionViaApi } from "./helpers/auth";
  3   | 
  4   | const AUDIT_TAG = "[phase3-regression]";
  5   | 
  6   | const EMPLOYEE_USERS = ["employee0@zozi.com", "employee@zozi.com"];
  7   | const EMPLOYEE_PASSWORD = "employee123";
  8   | const SUPPLIER_USERS = ["supplier@zozi.com", "supplier"];
  9   | const SUPPLIER_PASSWORD = "supplier123";
  10  | const LOGISTICS_USERS = ["logistics@zozi.com", "logistics"];
  11  | const LOGISTICS_PASSWORD = "logistics123";
  12  | 
  13  | async function fulfillJson(page: Page, urlPattern: RegExp, body: unknown, status = 200) {
  14  |   await page.route(urlPattern, async (route) => {
  15  |     if (route.request().method() === "OPTIONS") {
  16  |       await route.fulfill({ status: 204, headers: { "Access-Control-Allow-Origin": "*" } });
  17  |       return;
  18  |     }
  19  |     await route.fulfill({
  20  |       status,
  21  |       contentType: "application/json",
  22  |       headers: { "Access-Control-Allow-Origin": "*" },
  23  |       body: JSON.stringify(body),
  24  |     });
  25  |   });
  26  | }
  27  | 
  28  | async function setupAuthMocks(page: Page, role: "employee" | "supplier" | "logistics" | "customer", user: string) {
  29  |   const meResponse = {
  30  |     id: 1,
  31  |     email: user,
  32  |     role,
  33  |     username: user.split("@")[0],
  34  |     full_name: `${role} demo`,
  35  |     country_code: "AE",
  36  |     is_active: true,
  37  |   };
  38  |   await fulfillJson(page, /\/api\/auth\/me(\?|$)/, meResponse);
  39  |   await fulfillJson(page, /\/api\/auth\/login(\?|$)/, {
  40  |     access_token: "mock.jwt.token",
  41  |     token_type: "bearer",
  42  |     user: meResponse,
  43  |   });
  44  |   await page.goto("/", { waitUntil: "domcontentloaded", timeout: 60_000 });
  45  |   await page.evaluate(
  46  |     ([u, r]) => window.localStorage.setItem("zozi_has_session", "1"),
  47  |     [user, role],
  48  |   );
  49  |   await page.context().addCookies([
  50  |     { name: "zozi_refresh", value: "mock-refresh-token", url: "http://127.0.0.1:3000" },
  51  |   ]);
  52  | }
  53  | 
  54  | async function gotoAndVerify(page: Page, path: string, expectedUrlRegex?: RegExp) {
  55  |   const resp = await page.goto(path, { waitUntil: "domcontentloaded", timeout: 60_000 });
  56  |   if (!resp) throw new Error(`No response from ${path}`);
  57  |   const status = resp.status();
  58  |   const url = page.url();
  59  |   if (expectedUrlRegex && expectedUrlRegex.test(url)) return { status, url, redirected: true };
  60  |   return { status, url, redirected: false };
  61  | }
  62  | 
  63  | test.describe("Phase 3 — Employee Regression", () => {
  64  |   test("employee dashboard loads with 6 endpoints", async ({ page }) => {
  65  |     test.setTimeout(90_000);
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
> 96  |     expect(status).toBeLessThan(500);
      |                    ^ Error: expect(received).toBeLessThan(expected)
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
  166 |     expect(status).toBeLessThan(500);
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
```