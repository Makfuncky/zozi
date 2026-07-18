import path from "path";
import { expect, test, type Locator, type Page, type Route } from "@playwright/test";

async function fulfillJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function waitForSupplierNavigation(page: Page, expectedUrl: RegExp, timeoutMs = 45_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (expectedUrl.test(page.url())) {
      return;
    }
    await page.waitForTimeout(250);
  }

  throw new Error(`Timed out waiting for ${expectedUrl}. Current URL: ${page.url()}`);
}

async function waitForSessionFlag(page: Page, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const hasLocalSession = await page
      .evaluate(() => window.localStorage.getItem("zozi_has_session") === "1")
      .catch(() => false);
    const cookies = await page.context().cookies();
    if (hasLocalSession || cookies.some((cookie) => cookie.name === "zozi_refresh" || cookie.name === "refresh_token")) {
      return;
    }
    const currentUrl = page.url();
    if (!/\/supplier\/login(?:\?|$)/.test(currentUrl)) {
      return;
    }
    await page.waitForTimeout(250);
  }

  throw new Error(`Timed out waiting for supplier session state after ${timeoutMs}ms`);
}

async function bootstrapSupplierApiSession(page: Page) {
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });

  for (const username of ["supplier@zozi.com", "supplier"]) {
    const response = await page.request.post("/api/auth/login", {
      form: { username, password: "supplier123" },
      failOnStatusCode: false,
    });
    if (!response.ok()) {
      continue;
    }
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
    return true;
  }

  return false;
}

async function loginSupplierViaForm(page: Page) {
  await page.goto("/supplier/login", { waitUntil: "domcontentloaded", timeout: 120_000 });

  for (const username of ["supplier@zozi.com", "supplier"]) {
    const usernameInput = page.getByRole("textbox", { name: /username/i });
    const passwordInput = page.locator("input[type='password']").first();
    const submitButton = page.locator("main").getByRole("button", { name: /^sign in$/i });

    await usernameInput.waitFor({ state: "visible", timeout: 30_000 });
    await usernameInput.fill(username);
    await passwordInput.fill("supplier123");
    await expect.poll(async () => submitButton.isEnabled(), { timeout: 15_000 }).toBe(true);
    await Promise.all([
      page.waitForURL(/\/supplier\/(dashboard|products)(?:\?|$)/, { timeout: 60_000 }).catch(() => undefined),
      submitButton.click(),
    ]);
    await waitForSupplierNavigation(page, /\/supplier\/(dashboard|products)(?:\?|$)/, 60_000).catch(() => undefined);

    if (!/\/supplier\/login(?:\?|$)/.test(page.url())) {
      await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1")).catch(() => undefined);
      return;
    }
  }

  throw new Error("Unable to establish supplier session via login form.");
}

async function bootstrapSupplierSession(page: Page) {
  let lastError: unknown;

  for (let attempt = 1; attempt <= 2; attempt += 1) {
    try {
      await page.context().clearCookies();
      await page.evaluate(() => window.localStorage.removeItem("zozi_has_session")).catch(() => undefined);

      if (await bootstrapSupplierApiSession(page)) {
        await page.goto("/supplier/dashboard", { waitUntil: "domcontentloaded", timeout: 120_000 });
        await waitForSupplierNavigation(page, /\/supplier\/dashboard(?:\?|$)/, 120_000);
        return;
      }

      await loginSupplierViaForm(page);
      await waitForSessionFlag(page, 15_000);
      if (!/\/supplier\/dashboard(?:\?|$)/.test(page.url())) {
        await page.goto("/supplier/dashboard", { waitUntil: "domcontentloaded", timeout: 120_000 });
      }
      await waitForSupplierNavigation(page, /\/supplier\/dashboard(?:\?|$)/, 120_000);
      return;
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError;
}

async function mockSupplierSession(page: Page) {
  await page.route("**/cart/", async (route) => {
    await fulfillJson(route, []);
  });

  await page.route("**/notifications**", async (route) => {
    await fulfillJson(route, []);
  });

  await page.route("**/api/notifications**", async (route) => {
    await fulfillJson(route, []);
  });

  await page.route("**/supplier/regions**", async (route) => {
    if (route.request().method() !== "GET") {
      await route.continue();
      return;
    }
    await fulfillJson(route, { operating_regions: ["United Arab Emirates", "Saudi Arabia"] });
  });

  await bootstrapSupplierSession(page);

  await page.goto("/supplier/bulk", { waitUntil: "domcontentloaded", timeout: 120_000 });

  if (/\/supplier\/login(?:\?|$)/.test(page.url())) {
    await bootstrapSupplierSession(page);
    await page.goto("/supplier/bulk", { waitUntil: "domcontentloaded", timeout: 120_000 });
  }

  await waitForSupplierNavigation(page, /\/supplier\/bulk(?:\?|$)/, 60_000);
  await page.waitForLoadState("networkidle");
  if (/\/supplier\/login(?:\?|$)/.test(page.url())) {
    await bootstrapSupplierSession(page);
    await page.goto("/supplier/bulk", { waitUntil: "domcontentloaded", timeout: 120_000 });
    await waitForSupplierNavigation(page, /\/supplier\/bulk(?:\?|$)/, 60_000);
  }
  await expect(page.getByText("Core Details").first()).toBeVisible({ timeout: 15_000 });
}

async function stableClick(locator: Locator) {
  await locator.waitFor({ state: "visible", timeout: 10_000 });
  try {
    await locator.click({ timeout: 10_000 });
  } catch {
    await locator.evaluate((element) => {
      (element as HTMLButtonElement).click();
    });
  }
}

async function ensureAdvancedOpen(page: Page) {
  const hideAdvancedButton = page.getByRole("button", { name: /hide advanced/i }).first();
  if (await hideAdvancedButton.isVisible().catch(() => false)) {
    return;
  }

  const showAdvancedButton = page.getByRole("button", { name: /show advanced/i }).first();
  if (await showAdvancedButton.isVisible().catch(() => false)) {
    await stableClick(showAdvancedButton);
    return;
  }

  throw new Error("Advanced details toggle was not available on the supplier bulk page.");
}

function getBulkUploadButton(page: Page) {
  return page.getByRole("button", { name: /upload/i }).last();
}

async function setPrimaryImageViaChooser(page: Page, file: string) {
  const fileChooserPromise = page.waitForEvent("filechooser");
  await stableClick(page.getByText("Upload photos").first());
  const fileChooser = await fileChooserPromise;
  await fileChooser.setFiles(file);
}

async function openComboBox(page: Page, selector: string) {
  const comboBox = page.locator(selector).first();
  await stableClick(comboBox);
}

test.describe("supplier bulk upload", () => {
  test("ai assist accepts a real workspace image and normalizes the response into the card", async ({ page }) => {
    await mockSupplierSession(page);

    const realProductImage = path.resolve(__dirname, "../../../documents/snap/Product/brown-rectangular-wooden-cupboard.jpg");
    let aiRequestBody = "";

    await page.route("**/ai/suggest", async (route) => {
      aiRequestBody = route.request().postDataBuffer()?.toString("utf8") || "";
      await fulfillJson(route, {
        name: "Brown Rectangular Wooden Cupboard",
        category: "Furniture",
        color: "Gray",
        color_candidates: ["Gray", "Brown"],
        tags_string: "cupboard, storage, bedroom",
        material_suggestions: ["Engineered wood", "Laminate finish"],
        variant_template: "home-furniture",
        variant_options: ["Small", "Large"],
        description: "Storage cupboard for bedrooms and home organization.",
        ai_powered: false,
      });
    });

      await setPrimaryImageViaChooser(page, realProductImage);
    await expect(page.getByAltText("preview").first()).toBeVisible({ timeout: 15_000 });
    await stableClick(page.getByRole("button", { name: /use ai from photo/i }).first());

    await expect(page.locator("#supplier-bulk-draft-initial-name")).toHaveValue("Brown Rectangular Wooden Cupboard");
    await expect(page.locator("#supplier-bulk-draft-initial-category")).toContainText("Furniture");
    await expect(page.locator("#supplier-bulk-draft-initial-subcategory")).toContainText("Storage");
    await expect(page.locator("#supplier-bulk-draft-initial-color")).toHaveValue("Grey");
    await expect(page.locator("#supplier-bulk-draft-initial-custom-sizes")).toHaveValue("");
    await expect(page.getByText(/smart suggestions applied using fallback rules/i)).toBeVisible();
  });

  test("manual upload uses currency-aware payloads and variant table rows", async ({ page }) => {
    await mockSupplierSession(page);

    let uploadBody = "";

    await page.route("**/supplier/products/bulk-upload", async (route) => {
      uploadBody = route.request().postDataBuffer()?.toString("utf8") || "";
      expect(route.request().method()).toBe("POST");
      await fulfillJson(route, {
        created_count: 1,
        error_count: 0,
        products: [{ id: 301, name: "Playwright Accent Chair", category: "Furniture", tags: "accent chair, living room, linen" }],
        errors: [],
        ai_used: false,
      });
    });

    await expect(page.getByText("AI Auto-Enrichment")).toHaveCount(0);
    await expect(page.getByRole("button", { name: /suggest all/i })).toHaveCount(0);
    await expect(page.getByText("Media").first()).toBeVisible();
    await expect(page.getByText("Core Details").first()).toBeVisible();
    await expect(page.getByText("Variants").first()).toBeVisible();

      const imageInput = page.locator("#supplier-bulk-draft-initial-image-trigger");
    await imageInput.setInputFiles({
      name: "chair.jpg",
      mimeType: "image/jpeg",
      buffer: Buffer.from("playwright-chair-image"),
    });

    await page.locator("#supplier-bulk-draft-initial-name").fill("Playwright Accent Chair");
    await expect(page.locator("#supplier-bulk-draft-initial-name")).toHaveValue("Playwright Accent Chair");
    await page.locator("#supplier-bulk-draft-initial-price").fill("249.99");
    await expect(page.locator("#supplier-bulk-draft-initial-price")).toHaveValue("249.99");
    await page.locator("#supplier-bulk-draft-initial-currency").selectOption("USD");
    await openComboBox(page, "#supplier-bulk-draft-initial-category");
    await page.getByPlaceholder("Search categories").fill("furn");
    await page.getByRole("option", { name: "Furniture" }).click();
    await openComboBox(page, "#supplier-bulk-draft-initial-subcategory");
    await page.getByPlaceholder("Search sub-categories").fill("chair");
    await page.getByRole("option", { name: "Chairs" }).click();
    await page.locator("#supplier-bulk-draft-initial-stock").fill("12");
    // Select color from the chip picker (Ivory is a preset)
    await stableClick(page.getByRole("button", { name: /^Ivory$/i }).first());
    await ensureAdvancedOpen(page);
    await page.locator("#supplier-bulk-draft-initial-return-window").fill("18");
    await page.locator("#supplier-bulk-draft-initial-custom-sizes").fill("Standard");
    // Expand shapes section then select Round
    await stableClick(page.getByRole("button", { name: /add shape variants/i }).first());
    await stableClick(page.getByRole("button", { name: /^round$/i }).first());
    await page.locator("#supplier-bulk-draft-initial-materials").fill("Linen upholstery over hardwood frame");
    await page.locator("#supplier-bulk-draft-initial-weight").fill("18.5");
    await page.locator("#supplier-bulk-draft-initial-dimensions").fill("92 x 84 x 88 cm");
    await expect(getBulkUploadButton(page)).toBeEnabled({ timeout: 15_000 });
    await stableClick(getBulkUploadButton(page));

    await expect.poll(() => uploadBody.includes("Playwright Accent Chair")).toBe(true);
    await expect.poll(() => uploadBody.includes('"currency":"USD"')).toBe(true);
    await expect.poll(() => uploadBody.includes('"subcategory":"Chairs"')).toBe(true);
    await expect.poll(() => uploadBody.includes('"visibility_regions":["United Arab Emirates","Saudi Arabia"]')).toBe(true);
    await expect.poll(() => uploadBody.includes('"attributes_json":{"shape":"Round"}')).toBe(true);
    await expect.poll(() => uploadBody.includes('"sku"')).toBe(false);
    await expect.poll(() => uploadBody.includes('"barcode"')).toBe(false);
    await expect.poll(() => uploadBody.includes("compare_price")).toBe(false);
    await expect.poll(() => uploadBody.includes("use_ai")).toBe(false);
    await expect(page.getByText(/1 created/i)).toBeVisible();
  });

  test("json import and draft duplication support repeat listing uploads", async ({ page }) => {
    await mockSupplierSession(page);

    let uploadBody = "";

    await page.route("**/supplier/products/bulk-upload", async (route) => {
      uploadBody = route.request().postDataBuffer()?.toString("utf8") || "";
      await fulfillJson(route, {
        created_count: 2,
        error_count: 0,
        products: [
          { id: 401, name: "Imported Storage Bin", category: "General", tags: "storage, home" },
          { id: 402, name: "Imported Storage Bin Copy", category: "General", tags: "storage, home" },
        ],
        errors: [],
        ai_used: false,
      });
    });

    const importPayload = JSON.stringify([
      {
        name: "Imported Storage Bin",
        price: 89.5,
        currency: "SAR",
        stock: 32,
        category: "General",
        description: "Stackable storage bin for repeat supplier imports.",
        brand: "Zozi House",
        color: "Sand",
        tags: "storage, home",
        materials: "Recycled plastic",
        weight: 1.2,
        dimensions: "40 x 30 x 28 cm",
      },
    ]);

      const fileChooserPromise = page.waitForEvent("filechooser");
      await stableClick(page.getByRole("button", { name: /import json/i }).first());
      const fileChooser = await fileChooserPromise;
      await fileChooser.setFiles({
      name: "bulk-import.json",
      mimeType: "application/json",
      buffer: Buffer.from(importPayload),
    });
    const nameInputs = page.getByPlaceholder("e.g. Wireless Bluetooth Earphones");
    await expect(nameInputs).toHaveCount(1);
  await expect.poll(async () => nameInputs.first().inputValue(), { timeout: 15_000 }).toBe("Imported Storage Bin");
  await expect.poll(async () => page.getByLabel("Currency").first().inputValue(), { timeout: 15_000 }).toBe("SAR");

    await stableClick(page.getByRole("button", { name: /duplicate draft/i }).first());
    await expect(nameInputs).toHaveCount(2);
    await expect(nameInputs.nth(1)).toHaveValue("Imported Storage Bin");
    await expect(page.getByLabel("Currency").nth(1)).toHaveValue("SAR");

    await nameInputs.nth(1).fill("Imported Storage Bin Copy");
    await stableClick(page.getByRole("button", { name: /upload 2 products/i }).first());

    await expect(page.getByText(/2 created/i)).toBeVisible();
    await expect.poll(() => uploadBody.includes("Imported Storage Bin Copy")).toBe(true);
    await expect.poll(() => uploadBody.includes("Imported Storage Bin")).toBe(true);
    await expect.poll(() => uploadBody.includes('"currency":"SAR"')).toBe(true);
  });

  test("invalid fashion upload focuses the first blocking field", async ({ page }) => {
    await mockSupplierSession(page);
    await openComboBox(page, "#supplier-bulk-draft-initial-category");
    await page.getByPlaceholder("Search categories").fill("fashion");
    await page.getByRole("option", { name: "Fashion" }).click();
    await ensureAdvancedOpen(page);
    await page.locator("#supplier-bulk-draft-initial-name").fill("Focus Test Fashion Item");
    await expect(page.locator("#supplier-bulk-draft-initial-name")).toHaveValue("Focus Test Fashion Item");
    await page.locator("#supplier-bulk-draft-initial-price").fill("59.99");
    await expect(page.locator("#supplier-bulk-draft-initial-price")).toHaveValue("59.99");
    await expect(getBulkUploadButton(page)).toBeEnabled({ timeout: 15_000 });
    await stableClick(getBulkUploadButton(page));

    await expect(page.getByText(/draft 1 needs attention: apparel products require material composition/i).first()).toBeVisible();
    await expect.poll(async () => page.evaluate(() => document.activeElement?.id)).toBe("supplier-bulk-draft-initial-materials");
  });
});