# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin-country-control-plane.spec.ts >> Country Ledger & Configuration Workspace >> 4. tax preview and tax draft creation
- Location: e2e\admin-country-control-plane.spec.ts:214:7

# Error details

```
Test timeout of 240000ms exceeded.
```

```
Error: locator.click: Test timeout of 240000ms exceeded.
Call log:
  - waiting for getByTestId(/^country-ledger-row-/).first()

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - link "Skip to main content" [ref=e2] [cursor=pointer]:
    - /url: "#main-content"
  - generic:
    - generic:
      - main
  - generic [ref=e8] [cursor=pointer]:
    - button "Open issues overlay" [ref=e9]:
      - img [ref=e11]
      - generic [ref=e13]:
        - generic [ref=e14]: "0"
        - generic [ref=e15]: "1"
      - generic [ref=e16]: Issue
    - button "Collapse issues badge" [ref=e17]:
      - img [ref=e18]
  - alert [ref=e20]
```

# Test source

```ts
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
  157 |     await expect(page.getByRole("heading", { name: /Country Configuration Ledger/i })).toBeVisible({ timeout: 120_000 });
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
> 219 |     await firstRow.click();
      |                    ^ Error: locator.click: Test timeout of 240000ms exceeded.
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
  258 | 
  259 |     // Add a test provider
  260 |     const providerIdInput = page.locator("label").filter({ hasText: "Provider ID" }).locator("input");
  261 |     const providerNameInput = page.locator("label").filter({ hasText: "Provider Name" }).locator("input");
  262 |     await providerIdInput.fill("test_provider");
  263 |     await providerNameInput.fill("Test Delivery Co");
  264 | 
  265 |     await page.getByRole("button", { name: "Add Integration Partner" }).click();
  266 |     await expect(page.getByText("Test Delivery Co")).toBeVisible({ timeout: 10_000 });
  267 | 
  268 |     await saveDraft(page, /Save Delivery Partners Draft/, /partners draft created/i);
  269 |   });
  270 | 
  271 |   test("7. payment gateways — add gateway and create draft", async ({ page }) => {
  272 |     await loginAsAdmin(page, "/admin/countries");
  273 | 
  274 |     const firstRow = page.getByTestId(/^country-ledger-row-/).first();
  275 |     await firstRow.click();
  276 |     await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });
  277 | 
  278 |     await page.getByRole("button", { name: "Payment Gateways" }).click();
  279 | 
  280 |     // Add a test gateway
  281 |     const gwIdInput = page.locator("label").filter({ hasText: "Gateway ID" }).locator("input");
  282 |     const gwNameInput = page.locator("label").filter({ hasText: "Display Name" }).locator("input");
  283 |     await gwIdInput.fill("test_gw");
  284 |     await gwNameInput.fill("Test Gateway");
  285 | 
  286 |     await page.getByRole("button", { name: "Add Gateway Option" }).click();
  287 |     await expect(page.getByText("Test Gateway")).toBeVisible({ timeout: 10_000 });
  288 | 
  289 |     await saveDraft(page, /Save Payment Gateways Draft/, /gateways draft created/i);
  290 |   });
  291 | 
  292 |   test("8. legal rules draft creation", async ({ page }) => {
  293 |     await loginAsAdmin(page, "/admin/countries");
  294 | 
  295 |     const firstRow = page.getByTestId(/^country-ledger-row-/).first();
  296 |     await firstRow.click();
  297 |     await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });
  298 | 
  299 |     await page.getByRole("button", { name: "Legal & Rules" }).click();
  300 | 
  301 |     await saveDraft(page, /Save Legal Rules Draft/, /legal rules draft created/i);
  302 |   });
  303 | 
  304 |   test("9. regions — add region and create draft", async ({ page }) => {
  305 |     await loginAsAdmin(page, "/admin/countries");
  306 | 
  307 |     const firstRow = page.getByTestId(/^country-ledger-row-/).first();
  308 |     await firstRow.click();
  309 |     await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });
  310 | 
  311 |     await page.getByRole("button", { name: "Regions & Cities" }).click();
  312 | 
  313 |     // Add a region
  314 |     const regionInput = page.locator("label").filter({ hasText: "Region / Governorate Name" }).locator("input");
  315 |     const citiesInput = page.locator("label").filter({ hasText: "Cities (comma-separated list)" }).locator("input");
  316 |     await regionInput.fill("Test Region");
  317 |     await citiesInput.fill("City A, City B");
  318 | 
  319 |     await page.getByRole("button", { name: "Add Region Hub" }).click();
```