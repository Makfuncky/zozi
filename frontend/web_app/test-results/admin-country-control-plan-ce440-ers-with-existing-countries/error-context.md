# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin-country-control-plane.spec.ts >> Country Ledger & Configuration Workspace >> 1. ledger table renders with existing countries
- Location: e2e\admin-country-control-plane.spec.ts:154:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('heading', { name: /Country Configuration Ledger/i })
Expected: visible
Timeout: 120000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 120000ms
  - waiting for getByRole('heading', { name: /Country Configuration Ledger/i })

```

```yaml
- link "Skip to main content":
  - /url: "#main-content"
- main:
  - complementary:
    - text: ZOZI Admin
    - button "Collapse sidebar"
    - paragraph: Admin
    - paragraph: admin
    - textbox "Search nav..."
    - navigation
    - button "Logout"
  - text: Admin Workspace
  - heading "Countries" [level=1]
  - paragraph: Platform management and operational control
  - button "Open keyboard shortcuts help": "?"
  - button "Toggle theme" [disabled]
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
  57  | 
  58  |     await page.goto("/", { waitUntil: "domcontentloaded" });
  59  |     await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
  60  |     await page.request.get("/api/auth/me", { failOnStatusCode: false });
  61  |     await openProtectedRoute(page, destination, /\/admin\/(dashboard|countries)(?:\?|$)/, 120_000);
  62  |     if (!(await isAdminAccessGateVisible(page))) {
  63  |       return;
  64  |     }
  65  |   }
  66  | 
  67  |   await page.goto("/admin/login", { waitUntil: "domcontentloaded" });
  68  |   const submitButton = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  69  |   await submitButton.waitFor();
  70  |   const form = submitButton.locator("xpath=ancestor::form[1]");
  71  | 
  72  |   const fillAndSubmit = async (username: string, password: string) => {
  73  |     const identifierCandidates = [
  74  |       form.locator("input[name='username']:visible"),
  75  |       form.locator("input[autocomplete='username']:visible"),
  76  |       form.locator("input[required]:not([type='password']):visible"),
  77  |       form.locator("input[type='email']:visible"),
  78  |       form.locator("input:not([type='password']):visible"),
  79  |     ];
  80  | 
  81  |     let identifierFilled = false;
  82  |     for (const candidate of identifierCandidates) {
  83  |       if (await candidate.count()) {
  84  |         await candidate.first().fill(username);
  85  |         identifierFilled = true;
  86  |         break;
  87  |       }
  88  |     }
  89  | 
  90  |     if (!identifierFilled) {
  91  |       throw new Error("Unable to find a visible username/email input on the login form.");
  92  |     }
  93  | 
  94  |     const passwordInput = form.locator("input[type='password']:visible").first();
  95  |     await passwordInput.fill(password);
  96  |     await submitButton.click();
  97  |   };
  98  | 
  99  |   await fillAndSubmit("admin@zozi.com", "admin123");
  100 |   try {
  101 |     await waitForSessionFlag(page, 30_000);
  102 |   } catch {
  103 |     await page.goto("/admin/login", { waitUntil: "domcontentloaded" });
  104 |     await fillAndSubmit("admin", "admin123");
  105 |   }
  106 | 
  107 |   await waitForSessionFlag(page, 60_000);
  108 |   await openProtectedRoute(page, destination, /\/admin\/(dashboard|countries)(?:\?|$)/, 120_000);
  109 | 
  110 |   if (await isAdminAccessGateVisible(page)) {
  111 |     for (const candidate of ["admin@zozi.com", "admin"]) {
  112 |       await bootstrapAdminSessionViaApi(page);
  113 |       await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
  114 |       await page.request.get("/api/auth/me", { failOnStatusCode: false });
  115 |       await openProtectedRoute(page, destination, /\/admin\/(dashboard|countries)(?:\?|$)/, 120_000);
  116 |       if (!(await isAdminAccessGateVisible(page))) {
  117 |         break;
  118 |       }
  119 |     }
  120 |   }
  121 | 
  122 |   if (!(await hasSessionState(page))) {
  123 |     throw new Error("Failed to establish admin session for country control plane test");
  124 |   }
  125 | 
  126 |   await openProtectedRoute(page, destination, /\/admin\/countries(?:\?|$)/, 120_000);
  127 | }
  128 | 
  129 | /* ── Helper: select a country from the ledger table by code ───────────────── */
  130 | async function selectCountryFromLedger(page: Page, code: string) {
  131 |   const row = page.getByTestId(`country-ledger-row-${code}`);
  132 |   await expect(row).toBeVisible({ timeout: 30_000 });
  133 |   await row.click();
  134 |   // Wait for the workspace to load
  135 |   await expect(page.getByText(/Sections/)).toBeVisible({ timeout: 30_000 });
  136 | }
  137 | 
  138 | /* ── Helper: create a draft and expect success ────────────────────────────── */
  139 | async function saveDraft(page: Page, buttonLabel: string | RegExp, expectedActivity: RegExp) {
  140 |   const btn = page.getByRole("button", { name: buttonLabel });
  141 |   await expect(btn).toBeVisible({ timeout: 10_000 });
  142 |   await btn.click();
  143 |   await expect(page.getByTestId("country-activity-message")).toContainText(expectedActivity, { timeout: 30_000 });
  144 |   // Back to Overview after saving
  145 |   await page.getByRole("button", { name: "Overview" }).click();
  146 | }
  147 | 
  148 | /* ────────────────────────────────────────────────────────────────────────────
  149 |    Tests
  150 |    ──────────────────────────────────────────────────────────────────────────── */
  151 | 
  152 | test.describe("Country Ledger & Configuration Workspace", () => {
  153 | 
  154 |   test("1. ledger table renders with existing countries", async ({ page }) => {
  155 |     await loginAsAdmin(page, "/admin/countries");
  156 | 
> 157 |     await expect(page.getByRole("heading", { name: /Country Configuration Ledger/i })).toBeVisible({ timeout: 120_000 });
      |                                                                                        ^ Error: expect(locator).toBeVisible() failed
  158 | 
  159 |     const table = page.locator("table").first();
  160 |     await expect(table).toBeVisible({ timeout: 30_000 });
  161 | 
  162 |     const rows = table.locator("tbody tr");
  163 |     const count = await rows.count();
  164 |     expect(count).toBeGreaterThan(0);
  165 |   });
  166 | 
  167 |   test("2. create a new country via the compact form", async ({ page }) => {
  168 |     await loginAsAdmin(page, "/admin/countries");
  169 | 
  170 |     const testCode = "XZ";
  171 |     const testName = "Testland";
  172 | 
  173 |     // Fill create form
  174 |     await page.getByTestId("create-country-code").fill(testCode);
  175 |     await page.getByTestId("create-country-name").fill(testName);
  176 |     await page.getByTestId("create-country-currency").fill("XZR");
  177 |     await page.getByTestId("create-country-timezone").fill("UTC");
  178 | 
  179 |     // Create
  180 |     await page.getByTestId("create-country-button").click();
  181 | 
  182 |     // Wait for the ledger to include the new entry
  183 |     await expect(page.getByTestId(`country-ledger-row-${testCode}`)).toBeVisible({ timeout: 30_000 });
  184 |     await expect(page.getByText(/Created country/)).toBeVisible({ timeout: 10_000 });
  185 | 
  186 |     // Cleanup — deactivate test country (we leave it in the DB)
  187 |     await selectCountryFromLedger(page, testCode);
  188 |     // Go to overview tab
  189 |     await page.getByRole("button", { name: "Overview" }).click();
  190 |     const activeCheckbox = page.locator("label").filter({ hasText: "Active / Enabled" }).locator("input[type='checkbox']");
  191 |     if (await activeCheckbox.isChecked()) {
  192 |       await activeCheckbox.click();
  193 |       await page.getByRole("button", { name: "Update Identity" }).click();
  194 |       await expect(page.getByTestId("country-activity-message")).toContainText(/updated/i, { timeout: 15_000 });
  195 |     }
  196 |   });
  197 | 
  198 |   test("3. select country from ledger and verify overview tab loads", async ({ page }) => {
  199 |     await loginAsAdmin(page, "/admin/countries");
  200 | 
  201 |     // Pick first available country
  202 |     const firstRow = page.getByTestId(/^country-ledger-row-/).first();
  203 |     await expect(firstRow).toBeVisible({ timeout: 30_000 });
  204 |     await firstRow.click();
  205 | 
  206 |     // Workspace should appear
  207 |     await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });
  208 | 
  209 |     // Overview tab fields should be populated
  210 |     const nameInput = page.locator("label").filter({ hasText: "Display Name" }).locator("input");
  211 |     await expect(nameInput).toBeVisible({ timeout: 10_000 });
  212 |   });
  213 | 
  214 |   test("4. tax preview and tax draft creation", async ({ page }) => {
  215 |     await loginAsAdmin(page, "/admin/countries");
  216 | 
  217 |     // Select first country
  218 |     const firstRow = page.getByTestId(/^country-ledger-row-/).first();
  219 |     await firstRow.click();
  220 |     await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });
  221 | 
  222 |     // Navigate to Tax tab
  223 |     await page.getByRole("button", { name: "Tax & VAT" }).click();
  224 |     await expect(page.getByTestId("country-tax-panel")).toBeVisible({ timeout: 15_000 });
  225 | 
  226 |     // Fill tax preview
  227 |     const previewInput = page.locator("label").filter({ hasText: "Preview Price Amount" }).locator("input");
  228 |     await previewInput.fill("250");
  229 | 
  230 |     await page.getByTestId("preview-tax-button").click();
  231 |     await expect(page.getByTestId("tax-preview-result")).toBeVisible({ timeout: 30_000 });
  232 | 
  233 |     // Create draft
  234 |     await saveDraft(page, /Save Tax Draft/, /Tax draft created/i);
  235 |   });
  236 | 
  237 |   test("5. internal logistics draft creation", async ({ page }) => {
  238 |     await loginAsAdmin(page, "/admin/countries");
  239 | 
  240 |     const firstRow = page.getByTestId(/^country-ledger-row-/).first();
  241 |     await firstRow.click();
  242 |     await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });
  243 | 
  244 |     await page.getByRole("button", { name: "Internal Logistics" }).click();
  245 |     await expect(page.getByTestId("country-logistics-panel")).toBeVisible({ timeout: 15_000 });
  246 | 
  247 |     await saveDraft(page, /Save Logistics Draft/, /Logistics draft created/i);
  248 |   });
  249 | 
  250 |   test("6. delivery partners — add provider and create draft", async ({ page }) => {
  251 |     await loginAsAdmin(page, "/admin/countries");
  252 | 
  253 |     const firstRow = page.getByTestId(/^country-ledger-row-/).first();
  254 |     await firstRow.click();
  255 |     await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });
  256 | 
  257 |     await page.getByRole("button", { name: "Delivery Partners" }).click();
```