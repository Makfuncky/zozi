# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: admin-country-control-plane.spec.ts >> Country Ledger & Configuration Workspace >> 5. internal logistics draft creation
- Location: e2e\admin-country-control-plane.spec.ts:237:7

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
- generic [active] [ref=f2e1]:
  - generic [ref=f2e5]:
    - complementary [ref=f2e6]:
      - generic [ref=f2e7]:
        - generic [ref=f2e8]: ZOZI Admin
        - button "Collapse sidebar" [ref=f2e9]
      - generic [ref=f2e16]:
        - paragraph [ref=f2e17]: Admin
        - paragraph [ref=f2e18]: admin
      - textbox "Search nav..." [ref=f2e24]
      - navigation [ref=f2e25]
      - button "Logout" [ref=f2e27]
    - generic [ref=f2e32]:
      - banner [ref=f2e33]:
        - generic [ref=f2e35]:
          - generic [ref=f2e37]:
            - generic [ref=f2e38]: Admin Workspace
            - heading "Countries" [level=1] [ref=f2e40]
            - paragraph [ref=f2e41]: Platform management and operational control
          - generic [ref=f2e43]:
            - button "Open keyboard shortcuts help" [ref=f2e44]: "?"
            - button "Switch to dark theme" [ref=f2e45]: 🌙
            - group "Data density" [ref=f2e46]:
              - button "Compact density" [pressed] [ref=f2e47]
              - button "Normal density" [ref=f2e50]
              - button "Expanded density" [ref=f2e54]
            - generic [ref=f2e56]: admin
            - generic [ref=f2e57]: Admin
      - main [ref=f2e61]
  - alert [ref=f2e68]
```

# Test source

```ts
  141 |   await expect(btn).toBeVisible({ timeout: 10_000 });
  142 |   await btn.click();
  143 |   await expect(page.getByTestId("country-activity-message")).toContainText(expectedActivity, { timeout: 30_000 });
  144 |   // Back to Overview after saving
  145 |   await page.getByRole("button", { name: "Overview" }).click();
  146 | }
  147 | 
  148 | /* â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
  149 |    Tests
  150 |    â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */
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
  186 |     // Cleanup â€” deactivate test country (we leave it in the DB)
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
> 241 |     await firstRow.click();
      |                    ^ Error: locator.click: Test timeout of 240000ms exceeded.
  242 |     await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });
  243 | 
  244 |     await page.getByRole("button", { name: "Internal Logistics" }).click();
  245 |     await expect(page.getByTestId("country-logistics-panel")).toBeVisible({ timeout: 15_000 });
  246 | 
  247 |     await saveDraft(page, /Save Logistics Draft/, /Logistics draft created/i);
  248 |   });
  249 | 
  250 |   test("6. delivery partners â€” add provider and create draft", async ({ page }) => {
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
  271 |   test("7. payment gateways â€” add gateway and create draft", async ({ page }) => {
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
  304 |   test("9. regions â€” add region and create draft", async ({ page }) => {
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
  320 |     await expect(page.getByText("Test Region")).toBeVisible({ timeout: 10_000 });
  321 | 
  322 |     await saveDraft(page, /Save Regions Draft/, /regions draft created/i);
  323 |   });
  324 | 
  325 |   test("10. supplier KYC draft creation", async ({ page }) => {
  326 |     await loginAsAdmin(page, "/admin/countries");
  327 | 
  328 |     const firstRow = page.getByTestId(/^country-ledger-row-/).first();
  329 |     await firstRow.click();
  330 |     await expect(page.getByText("Sections")).toBeVisible({ timeout: 30_000 });
  331 | 
  332 |     await page.getByRole("button", { name: "Supplier KYC" }).click();
  333 | 
  334 |     // Toggle a document requirement
  335 |     const docCheckbox = page.locator("label").filter({ hasText: "Commercial Registration" }).locator("input[type='checkbox']");
  336 |     if (!(await docCheckbox.isChecked())) {
  337 |       await docCheckbox.check();
  338 |     }
  339 | 
  340 |     await saveDraft(page, /Save Supplier Rules Draft/, /supplier requirements draft created/i);
  341 |   });
```