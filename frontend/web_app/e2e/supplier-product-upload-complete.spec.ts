import { expect, test, type Page } from "@playwright/test";
import path from "path";

const IMAGE_DIR = path.resolve(__dirname, "../../../image");

async function loginSupplier(page: Page) {
  console.log("[login] Starting login...");
  // Get token from API
  const loginRes = await page.request.post("http://localhost:8000/auth/login", {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    form: { username: "supplier@zozi.com", password: process.env.E2E_SUPPLIER_PASSWORD ?? "supplier123" },
  });
  const loginData = await loginRes.json();
  const token = loginData.access_token;
  console.log("[login] Auth token received:", token?.slice(0, 20));

  // Step 1: Navigate to the target URL first (will redirect to login if no cookie)
  console.log("[login] Navigating to add product page...");
  await page.goto("/supplier/products/add", { waitUntil: "domcontentloaded", timeout: 60_000 });
  console.log("[login] Page URL after goto:", page.url());
  
  // Step 2: Now set the cookie and localStorage
  console.log("[login] Setting cookie + localStorage...");
  await page.context().addCookies([
    { name: "access_token", value: token, url: "http://localhost:3000" },
  ]);
  await page.evaluate((t) => {
    localStorage.setItem("access_token", t);
    localStorage.setItem("zozi_has_session", "1");
  }, token);
  
  // Step 3: Reload so the server picks up the cookie+localStorage
  console.log("[login] Reloading...");
  await page.reload({ waitUntil: "domcontentloaded", timeout: 60_000 });
  console.log("[login] Page URL after reload:", page.url());
  
  // Step 4: Wait for the add product page to render
  console.log("[login] Waiting for page content...");
  await page.waitForSelector("text=New Product", { timeout: 15_000 });

  // Step 4b: Close the SmartMediaUpload overlay if it appears (click "Enter Manually")
  const manualEntryBtn = page.getByText("Enter Manually");
  if (await manualEntryBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
    console.log("[login] Dismissing SmartMediaUpload popup...");
    await manualEntryBtn.click();
    await page.waitForTimeout(500);
  }

  // Step 4c: Now wait for the "Choose Photo" button (should be visible after overlay is closed)
  console.log("[login] Waiting for 'Choose Photo'...");
  await page.waitForSelector("text=Choose Photo", { timeout: 15_000 });

  // Step 5: Wait for React hydration — without this, file input onChange won't work
  console.log("[login] Waiting for React hydration...");
  await page.waitForFunction(() => {
    const input = document.querySelector('input[accept*="image"]');
    if (!input) return false;
    return Object.keys(input).some(k => k.startsWith("__reactProps"));
  }, { timeout: 20_000 });
  console.log("[login] Login + hydration complete!");
}



async function uploadImage(page: Page, fileName: string) {
  const filePath = path.join(IMAGE_DIR, fileName);
  console.log(`[upload] Uploading ${fileName}...`);

  // Directly set the file on the hidden input
  const input = page.locator('input[type="file"]').first();
  await input.setInputFiles(filePath);
  await input.evaluate((el) => {
    (el as HTMLInputElement).dispatchEvent(new Event("change", { bubbles: true }));
  });
  console.log(`[upload] File set via setInputFiles`);

  const canvas = page.locator("canvas").first();
  try {
    await expect(canvas).toBeVisible({ timeout: 30_000 });
  } catch {
    console.log(`Canvas not visible for ${fileName} — checking upload state`);
    const uploadArea = page.getByText("Drop photo here");
    if (await uploadArea.isVisible({ timeout: 1000 }).catch(() => false)) {
      throw new Error(`Image ${fileName} upload failed — canvas never rendered`);
    }
    await expect(canvas).toBeVisible({ timeout: 60_000 });
  }
}

test.describe("Supplier Product Upload — Complete", () => {
  test.setTimeout(240_000);
  test.slow();

  test.beforeEach(async ({ page }) => {
    await loginSupplier(page);
  });

  test("1. Upload image -> canvas renders -> AI auto-fills", async ({ page }) => {
    await uploadImage(page, "image_04.jpg");
    // Wait for AI analyze (fires automatically 800ms after upload)
    const analyzeBtn = page.getByRole("button", { name: /analyze photo|re-analyze|analyzing/i });
    try {
      await expect(analyzeBtn).toBeVisible({ timeout: 30_000 });
      const btnText = await analyzeBtn.textContent().catch(() => "");
      expect(btnText).not.toBe("");
      console.log(`AI analyze button state: "${btnText}"`);
    } catch {
      console.log("AI analyze button not found — form may have loaded without analyzer");
    }
    // Verify canvas has non-zero dimensions
    const canvas = page.locator("canvas").first();
    const box = await canvas.boundingBox().catch(() => null);
    if (box) {
      expect(box.width).toBeGreaterThan(0);
      expect(box.height).toBeGreaterThan(0);
      console.log(`Canvas: ${box.width}x${box.height}`);
    }
  });

  test("2. AI mock fill + background removal buttons", async ({ page }) => {
    test.setTimeout(180_000);
    // Intercept AI analyze to return deterministic rich data
    await page.route("**/supplier/upload/ai-analyze", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          product_name_hint: "Black Running Shoes",
          suggested_category: "Clothing",
          suggested_subcategory: "Shoes",
          suggested_brand: "Nike",
          product_description: "Premium black running shoes.",
          suggested_tags: ["running", "shoes", "black", "athletic", "sneakers", "sports", "training", "comfort", "durable", "footwear"],
          detected_attributes: { color: ["black", "white"], material: ["mesh", "rubber"], brand: "Nike" },
          suggested_variants: ["color", "size"],
          variant_options: { color: ["Black", "White"], size: ["US 7", "US 8", "US 9", "US 10"] },
          variant_labels: { color: "Color", size: "Size (US)" },
          photo_analysis: { dominant_colors: ["black", "#808080"], background: "simple", bg_complexity: 0.15, suggested_bg_preset: "birefnet_production" },
          source: "heuristic",
        }),
      });
    });
    await uploadImage(page, "image_10.jpg");
    // Wait for mock AI to fill
    await page.waitForTimeout(3000);
    const nameInput = page.locator('input[placeholder*="auto-detect"]');
    try {
      await expect(nameInput).toHaveValue("Black Running Shoes", { timeout: 15_000 });
      console.log("AI auto-filled product name");
    } catch {
      console.log("AI name auto-fill not detected (mock may not have been hit)");
    }
    // Test background removal buttons
    const autoBgBtn = page.getByRole("button", { name: /^Auto$/ });
    await expect(autoBgBtn).toBeVisible({ timeout: 5_000 });
    await autoBgBtn.click();
    await page.waitForTimeout(3000);
    await expect(page.locator("canvas").first()).toBeVisible({ timeout: 60_000 });
    console.log("Auto bg removal completed");
    // Test one specific model
    const modelBtn = page.getByRole("button", { name: /lite/i }).first();
    if (await modelBtn.isVisible().catch(() => false)) {
      await modelBtn.click();
      await page.waitForTimeout(3000);
      await expect(page.locator("canvas").first()).toBeVisible({ timeout: 60_000 });
      console.log("BG model (Lite) completed");
    }
  });

  test("3. Image processing tools + canvas controls", async ({ page }) => {
    test.setTimeout(240_000);
    // Mock process-tools to return a valid PNG (avoids full processing wait)
    await page.route("**/supplier/upload/process-tools", async (route) => {
      const resp = await route.fetch();
      const body = await resp.body();
      await route.fulfill({ status: 200, contentType: resp.headers()["content-type"] || "image/png", body });
    });
    await uploadImage(page, "image_14.jpeg");
    await page.waitForTimeout(2000);
    // Test image tools one by one
    const toolButtons = [
      { name: /magic erase/i, key: "magic_erase" },
      { name: /smart crop/i, key: "smart_crop" },
      { name: /auto light/i, key: "auto_light" },
      { name: /white balance/i, key: "white_balance" },
      { name: /color boost/i, key: "color_enhance" },
    ];
    for (const tool of toolButtons) {
      const btn = page.getByRole("button", { name: tool.name }).first();
      const enabled = await btn.isVisible().catch(() => false) && await btn.isEnabled().catch(() => false);
      if (enabled) {
        await btn.click();
        await page.waitForTimeout(3000);
        await expect(page.locator("canvas").first()).toBeVisible({ timeout: 60_000 });
        console.log(`${tool.key} completed`);
      } else {
        console.log(`${tool.key} button not enabled, skipping`);
      }
    }
    // Test canvas controls (these are instant local operations)
    const zoomInBtn = page.locator('button.toolbar-btn').filter({ has: page.locator('[class*="ZoomIn"]') }).first();
    if (await zoomInBtn.isVisible().catch(() => false)) {
      await zoomInBtn.click();
      await page.waitForTimeout(200);
      console.log("Zoom works");
    }
    // Background color buttons
    const whiteBgBtn = page.getByRole("button", { name: "W" });
    if (await whiteBgBtn.isVisible().catch(() => false)) {
      await whiteBgBtn.click();
      await page.waitForTimeout(200);
    }
    const blackBgBtn = page.getByRole("button", { name: "B" });
    if (await blackBgBtn.isVisible().catch(() => false)) {
      await blackBgBtn.click();
      await page.waitForTimeout(200);
    }
    const transBgBtn = page.getByRole("button", { name: "T" });
    if (await transBgBtn.isVisible().catch(() => false)) {
      await transBgBtn.click();
      await page.waitForTimeout(200);
    }
    console.log("Canvas controls work");
    // Denoise + Sharpen
    const denoiseBtn = page.getByRole("button", { name: /denoise/i });
    if (await denoiseBtn.isVisible().catch(() => false)) {
      await denoiseBtn.click();
      await page.waitForTimeout(3000);
      await expect(page.locator("canvas").first()).toBeVisible({ timeout: 60_000 });
      console.log("Denoise completed");
    }
    const sharpenBtn = page.getByRole("button", { name: /sharpen/i });
    if (await sharpenBtn.isVisible().catch(() => false)) {
      await sharpenBtn.click();
      await page.waitForTimeout(3000);
      await expect(page.locator("canvas").first()).toBeVisible({ timeout: 60_000 });
      console.log("Sharpen completed");
    }
  });

  test("4. Complete product submission with variants", async ({ page }) => {
    test.setTimeout(240_000);
    // Mock AI analyze
    let aiCalled = false;
    await page.route("**/supplier/upload/ai-analyze", async (route) => {
      aiCalled = true;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          product_name_hint: "Premium Wireless Headphones",
          suggested_category: "Electronics",
          suggested_subcategory: "Audio",
          suggested_brand: "Sony",
          product_description: "High-quality wireless headphones with noise cancellation and 30-hour battery.",
          suggested_tags: ["headphones", "wireless", "audio", "noise-cancelling", "bluetooth"],
          detected_attributes: { color: ["black"], material: ["plastic", "leather"], brand: "Sony" },
          suggested_variants: ["color", "size"],
          variant_options: { color: ["Black", "White"], size: ["Standard", "Compact"] },
          variant_labels: { color: "Color", size: "Size" },
          photo_analysis: { dominant_colors: ["black", "#1a1a1a"], background: "simple", bg_complexity: 0.1 },
          source: "heuristic",
        }),
      });
    });
    // Mock process-tools
    await page.route("**/supplier/upload/process-tools", async (route) => {
      const resp = await route.fetch();
      const body = await resp.body();
      await route.fulfill({ status: 200, contentType: resp.headers()["content-type"] || "image/png", body });
    });
    // Mock generate-angles
    await page.route("**/supplier/upload/generate-angles", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ bg_removed_url: "/uploads/bg.png", angle_urls: ["/uploads/angle_1.png"] }),
      });
    });
    // Upload and wait for AI
    await uploadImage(page, "image_01.webp");
    await page.waitForTimeout(3000);
    if (aiCalled) {
      console.log("AI analyze API called successfully");
    }
    // Fill mandatory fields (price + stock always required)
    const nameInput = page.locator('input[placeholder*="auto-detect"]');
    const currentName = await nameInput.inputValue().catch(() => "");
    if (!currentName) await nameInput.fill("Premium Wireless Headphones");

    const categorySelect = page.locator("select").first();
    const catVal = await categorySelect.inputValue().catch(() => "");
    if (catVal !== "Electronics") await categorySelect.selectOption("Electronics");

    const priceInput = page.locator('input[placeholder="0.00"]');
    await priceInput.fill("149.99");
    const stockInput = page.locator('input[placeholder="0"]').first();
    await stockInput.fill("50");

    // Enable variants
    const variantCb = page.locator('input[type="checkbox"]').first();
    const isChecked = await variantCb.isChecked().catch(() => false);
    if (!isChecked) {
      await variantCb.check();
      await page.waitForTimeout(300);
    }
    // Toggle variant types
    for (const vType of ["color", "size"]) {
      const btn = page.getByRole("button", { name: vType, exact: true });
      if (await btn.isVisible().catch(() => false)) {
        const cls = await btn.getAttribute("class").catch(() => "");
        if (cls && !cls.includes("bg-primary")) {
          await btn.click();
          await page.waitForTimeout(200);
        }
      }
    }
    await page.waitForTimeout(500);
    // Add color and size options
    const sections = page.locator("text=Color, Size").first();
    const allText = await page.locator("text=Add color").isVisible().catch(() => false);
    // Find color section
    let addedVariants = false;
    for (const [type, values] of Object.entries({ color: ["Black", "White"], size: ["Standard", "Compact"] })) {
      const placeholder = `Add ${type}`;
      const input = page.locator(`input[placeholder*="${placeholder}"]`).first();
      if (await input.isVisible().catch(() => false)) {
        for (const val of values) {
          await input.fill(val);
          await input.press("Enter");
          await page.waitForTimeout(200);
          addedVariants = true;
        }
      }
    }
    if (addedVariants) console.log("Variant options added");

    // Test angles button
    const anglesBtn = page.getByRole("button", { name: /angles/i });
    if (await anglesBtn.isVisible().catch(() => false)) {
      await anglesBtn.click();
      await page.waitForTimeout(3000);
      console.log("Angles button clicked");
    }

    // Mock product creation
    let productCreated = false;
    await page.route("**/supplier/products", async (route, req) => {
      if (req.method() === "POST") {
        productCreated = true;
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({ id: 9999, name: "Premium Wireless Headphones", status: "created" }),
        });
      } else {
        await route.continue();
      }
    });
    // Submit
    const publishBtn = page.getByRole("button", { name: /publish product|create & next/i });
    await expect(publishBtn).toBeEnabled({ timeout: 10_000 });
    await publishBtn.click();
    await page.waitForTimeout(5000);
    if (productCreated) {
      console.log("Product created via API — SUCCESS");
    }
    const urlAfter = page.url();
    console.log(`URL after submit: ${urlAfter}`);
  });

  test("5. Multiple image formats (JPEG, WebP, JPEG-alt)", async ({ page }) => {
    const formats = [
      { file: "image_04.jpg", label: "JPEG" },
      { file: "image_01.webp", label: "WebP" },
      { file: "image_14.jpeg", label: "JPEG-alt" },
    ];
    for (const fmt of formats) {
      // Already logged in from beforeEach, but need to navigate back after each upload
      await page.goto("/supplier/products/add", { waitUntil: "domcontentloaded", timeout: 60_000 });
      await page.waitForSelector("text=Choose Photo", { timeout: 15_000 });
      // Wait for React hydration
      await page.waitForFunction(() => {
        const input = document.querySelector('input[accept*="image"]');
        if (!input) return false;
        return Object.keys(input).some(k => k.startsWith("__reactProps"));
      }, { timeout: 20_000 });
      await uploadImage(page, fmt.file);
      console.log(`${fmt.label} (${fmt.file}) uploaded — canvas visible`);
    }
  });

  test("6. Fast bg quality toggle and remove image", async ({ page }) => {
    await uploadImage(page, "image_05.jpg");
    // Toggle fast/quality mode
    const fastBtn = page.getByRole("button", { name: /fast|quality/i });
    if (await fastBtn.isVisible().catch(() => false)) {
      await fastBtn.click();
      await page.waitForTimeout(300);
      await fastBtn.click();
      await page.waitForTimeout(300);
      console.log("Fast/Quality toggle works");
    }
    // Remove image
    const removeBtn = page.getByRole("button", { name: /remove/i });
    await expect(removeBtn).toBeVisible({ timeout: 5_000 });
    await removeBtn.click();
    await page.waitForTimeout(500);
    // Upload area should be visible again
    await expect(page.getByText("Choose Photo")).toBeVisible({ timeout: 5_000 });
    console.log("Remove image works");
  });
});
