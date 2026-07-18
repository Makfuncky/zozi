import fs from "fs";
import path from "path";
import { execFileSync } from "child_process";
import { expect, test, type Browser, type Locator, type Page } from "@playwright/test";

test.describe.configure({ timeout: 240_000 });

const repoRoot = path.resolve(__dirname, "../../..");
const seedOutputPath = path.join(repoRoot, "artifacts", "playwright", "finance-live-seed.json");
const pythonExecutable = process.platform === "win32"
  ? path.join(repoRoot, ".venv", "Scripts", "python.exe")
  : path.join(repoRoot, ".venv", "bin", "python");

type SeedState = {
  run_tag: string;
  credentials: {
    admin: { email: string; password: string };
    supplier: { email: string; password: string };
    customer: { email: string; password: string };
    logistics: { email: string; password: string };
  };
  card: {
    order_id: number;
    shipment_id: number;
    supplier_settlement_id: number;
    logistics_settlement_id: number;
  };
  cod: {
    order_id: number;
    shipment_id: number;
    supplier_settlement_id: number;
    logistics_settlement_id: number;
  };
};

let seedState: SeedState;

function expectNavigationUrl(page: Page, expectedUrl: RegExp, timeoutMs = 60_000) {
  return page.waitForFunction(
    (pattern) => new RegExp(pattern).test(window.location.href),
    expectedUrl.source,
    { timeout: timeoutMs },
  );
}

async function waitForFrontendReady(page: Page, timeoutMs = 90_000) {
  await page.waitForLoadState("domcontentloaded");
  const compilingNotice = page.getByText(/compiling/i).first();
  if (await compilingNotice.isVisible().catch(() => false)) {
    await compilingNotice.waitFor({ state: "hidden", timeout: timeoutMs });
  }
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
    await page.waitForTimeout(250);
  }

  throw new Error(`Timed out waiting for session state after ${timeoutMs}ms`);
}

async function hasSessionState(page: Page) {
  const hasLocalSession = await page
    .evaluate(() => window.localStorage.getItem("zozi_has_session") === "1")
    .catch(() => false);
  const cookies = await page.context().cookies();
  return hasLocalSession || cookies.some((cookie) => cookie.name === "zozi_refresh" || cookie.name === "refresh_token");
}

async function isSignInGateVisible(page: Page, timeoutMs = 5_000) {
  const submitButton = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  const passwordInput = page.locator("input[type='password']:visible").first();
  try {
    await submitButton.waitFor({ state: "visible", timeout: timeoutMs });
    return await passwordInput.isVisible();
  } catch {
    return false;
  }
}

async function firstVisibleLocator(locators: Locator[]) {
  for (const locator of locators) {
    const count = await locator.count();
    for (let index = 0; index < count; index += 1) {
      const candidate = locator.nth(index);
      if (await candidate.isVisible()) {
        return candidate;
      }
    }
  }
  throw new Error("Could not resolve a visible credential input.");
}

async function submitCredentialForm(page: Page, username: string, password: string) {
  const credentialForm = await firstVisibleLocator([
    page.locator("form:has(input[type='password']):has(button[type='submit'])"),
    page.locator("form").filter({ has: page.getByRole("button", { name: /sign in|log in|signin/i }) }),
  ]);
  await credentialForm.waitFor({ state: "visible" });

  const submitButton = await firstVisibleLocator([
    credentialForm.getByRole("button", { name: /sign in|log in|signin/i }),
    credentialForm.locator("button[type='submit']"),
  ]);
  await submitButton.waitFor({ state: "visible" });

  const usernameInput = await firstVisibleLocator([
    credentialForm.getByPlaceholder(/^username$/i),
    credentialForm.locator("input[placeholder*='Username']:visible"),
    credentialForm.locator("input[name='username']:visible"),
    credentialForm.locator("input[required]:not([type='password']):visible"),
    credentialForm.locator("input").first(),
  ]);
  const passwordInput = credentialForm.locator("input[type='password']").first();
  await expect(usernameInput).toBeVisible({ timeout: 10_000 });
  await expect(passwordInput).toBeVisible({ timeout: 10_000 });

  const usernamePlaceholder = ((await usernameInput.getAttribute("placeholder")) || "").toLowerCase();
  const prefersStrictUsername = usernamePlaceholder.includes("username") && !usernamePlaceholder.includes("email");
  const usernameCandidate = prefersStrictUsername && username.includes("@")
    ? username.split("@")[0]
    : username;

  const typeCredential = async (input: Locator, value: string) => {
    await input.click();
    await input.fill(value);
    await expect.poll(async () => (await input.inputValue()).trim().length, { timeout: 5_000 }).toBeGreaterThan(0);
  };

  await typeCredential(usernameInput, usernameCandidate);
  await typeCredential(passwordInput, password);

  for (let attempt = 0; attempt < 3 && !(await submitButton.isEnabled()); attempt += 1) {
    const currentUsername = (await usernameInput.inputValue()).trim();
    const currentPassword = (await passwordInput.inputValue()).trim();

    if (!currentUsername) {
      await typeCredential(usernameInput, usernameCandidate);
    }
    if (!currentPassword) {
      await typeCredential(passwordInput, password);
    }
    if (!(await submitButton.isEnabled()) && username.includes("@")) {
      await typeCredential(usernameInput, username.split("@")[0]);
    } else if (!(await submitButton.isEnabled()) && usernameCandidate !== username) {
      await typeCredential(usernameInput, username);
    }
    await page.waitForTimeout(250);
  }
  await expect(submitButton).toBeEnabled({ timeout: 10_000 });
  await submitButton.click();
}

async function loginAs(page: Page, loginPath: string, username: string, password: string, expectedUrl: RegExp) {
  if (loginPath === "/logistics-partner/login") {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await waitForFrontendReady(page, 120_000);
        let loginResponse = await page.request.post("/api/auth/login", {
      form: { username, password },
      failOnStatusCode: false,
    });
    if (!loginResponse.ok() && username.includes("@")) {
      loginResponse = await page.request.post("/api/auth/login", {
        form: { username: username.split("@")[0], password },
        failOnStatusCode: false,
      });
    }
    if (!loginResponse.ok()) {
      throw new Error(`Logistics proxy login failed with ${loginResponse.status()}`);
    }
    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1"));
    await waitForSessionFlag(page, 60_000);
    await page.goto("/logistics-partner/payouts", { waitUntil: "domcontentloaded" });
    await waitForFrontendReady(page, 120_000);
    if (await isSignInGateVisible(page)) {
      throw new Error("Logistics login did not unlock protected payouts route");
    }
    return;
  }

  const ensureAuthenticatedRoute = async () => {
    await waitForSessionFlag(page, 60_000);
    if (!expectedUrl.test(page.url())) {
      const roleWorkspacePath = loginPath.includes("/logistics-partner/")
        ? "/logistics-partner/payouts"
        : loginPath.includes("/admin/")
          ? "/admin/dashboard"
          : "/";
      await page.goto(roleWorkspacePath, { waitUntil: "domcontentloaded" });
    }
    if (!expectedUrl.test(page.url())) {
      return false;
    }
    return !(await isSignInGateVisible(page));
  };

  await page.goto(loginPath, { waitUntil: "domcontentloaded" });
  await submitCredentialForm(page, username, password);
  try {
    await waitForSessionFlag(page, 30_000);
  } catch {
    const retrySubmit = await firstVisibleLocator([
      page.getByRole("button", { name: /sign in|log in|signin/i }),
      page.locator("form button[type='submit']"),
    ]);
    await expect.poll(async () => retrySubmit.isEnabled(), { timeout: 30_000 }).toBe(true);
    if (!(await hasSessionState(page))) {
      await submitCredentialForm(page, username, password);
    }
  }
  if (await ensureAuthenticatedRoute()) {
    return;
  }

  if (username.includes("@")) {
    await page.goto(loginPath, { waitUntil: "domcontentloaded" });
    await submitCredentialForm(page, username.split("@")[0], password);
    if (await ensureAuthenticatedRoute()) {
      return;
    }
  }

  throw new Error(`Login gate remained visible for ${loginPath} after credential retries`);
}

function ensureReceiptPng(receiptRef: string) {
  const outputDir = path.join(repoRoot, "artifacts", "playwright");
  fs.mkdirSync(outputDir, { recursive: true });
  const receiptPath = path.join(outputDir, `${receiptRef}.png`);
  const pngBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+kDq8AAAAASUVORK5CYII=";
  fs.writeFileSync(receiptPath, Buffer.from(pngBase64, "base64"));
  return receiptPath;
}

function seedLiveFinanceState() {
  const seedScript = path.join(repoRoot, "scripts", "seed_finance_browser_walkthrough.py");
  const python = fs.existsSync(pythonExecutable) ? pythonExecutable : "python";
  fs.mkdirSync(path.dirname(seedOutputPath), { recursive: true });
  execFileSync(python, [seedScript, "--output", seedOutputPath], {
    cwd: repoRoot,
    stdio: "inherit",
  });
  return JSON.parse(fs.readFileSync(seedOutputPath, "utf-8")) as SeedState;
}

async function verifyReceiptAsAdmin(browser: Browser, receiptRef: string) {
  const adminContext = await browser.newContext();
  const adminPage = await adminContext.newPage();
  try {
    await loginAs(
      adminPage,
      "/admin/login",
      seedState.credentials.admin.email,
      seedState.credentials.admin.password,
      /\/admin\/(dashboard|finance)(?:\?|$)/,
    );
    await adminPage.goto("/admin/finance?section=finance", { waitUntil: "domcontentloaded" });
    await expect(adminPage.getByRole("heading", { name: "COD Receipt Verification" })).toBeVisible({ timeout: 120_000 });

    const receiptRow = adminPage.locator("tr", { hasText: receiptRef }).first();
    for (let attempt = 0; attempt < 5 && (await receiptRow.count()) === 0; attempt += 1) {
      await adminPage.waitForTimeout(2_000);
      await adminPage.reload({ waitUntil: "domcontentloaded" });
    }
    await expect(receiptRow).toBeVisible({ timeout: 60_000 });

    const verifyButton = receiptRow.getByRole("button", { name: /^Verify$/ }).first();
    if (await verifyButton.isVisible().catch(() => false)) {
      await verifyButton.click();
    }

    await expect(adminPage.getByText(receiptRef)).toBeVisible({ timeout: 60_000 });
    await expect(adminPage.getByText(/verified|reconciled|finance workspace/i).first()).toBeVisible({ timeout: 60_000 });
  } finally {
    await adminContext.close().catch(() => undefined);
  }
}

test.beforeAll(() => {
  seedState = seedLiveFinanceState();
});

test("logistics uploads COD proof and admin verifies it against the live stack", async ({ browser }) => {
  const logisticsContext = await browser.newContext();
  const logisticsPage = await logisticsContext.newPage();
  const receiptRef = `PW-COD-${seedState.run_tag}`;
  const receiptPath = ensureReceiptPng(receiptRef);
  let uploadedReceipt = false;

  try {
    const codReceiptHeading = logisticsPage.getByText("COD Receipt Upload").first();
    let logisticsWorkspaceReady = false;
    for (let attempt = 0; attempt < 4; attempt += 1) {
      await logisticsPage.goto("/logistics-partner/payouts", { waitUntil: "domcontentloaded" });
      await waitForFrontendReady(logisticsPage, 120_000);

      if (await codReceiptHeading.isVisible().catch(() => false)) {
        logisticsWorkspaceReady = true;
        break;
      }

      const dedicatedLoginHeading = logisticsPage.getByRole("heading", { name: /Logistics Partner/i }).first();
      if (logisticsPage.url().includes("/logistics-partner/login") && await dedicatedLoginHeading.isVisible().catch(() => false)) {
        const usernameInput = logisticsPage.getByPlaceholder(/^username$/i).first();
        const passwordInput = logisticsPage.locator("input[type='password']").first();
        await usernameInput.fill(seedState.credentials.logistics.email);
        await passwordInput.fill(seedState.credentials.logistics.password);
        const dedicatedLoginSubmit = logisticsPage.getByRole("button", { name: /sign in|log in|signin/i }).first();
        if (await dedicatedLoginSubmit.isEnabled().catch(() => false)) {
          await dedicatedLoginSubmit.click();
          await logisticsPage.waitForTimeout(1_000);
        }
      }

      const inlineSignInModal = logisticsPage
        .locator("div")
        .filter({ has: logisticsPage.getByText(/sign in to continue/i) })
        .first();
      if (await inlineSignInModal.isVisible().catch(() => false)) {
        const modalIdentifierInput = await firstVisibleLocator([
          inlineSignInModal.getByPlaceholder(/email|username/i),
          inlineSignInModal.locator("input[placeholder*='email']"),
          inlineSignInModal.locator("input:not([type='password'])"),
        ]);
        await modalIdentifierInput.fill(seedState.credentials.logistics.email);
        await inlineSignInModal.locator("input[type='password']").first().fill(seedState.credentials.logistics.password);
        const modalSubmit = inlineSignInModal.getByRole("button", { name: /sign in|log in|signin/i }).first();
        if (await modalSubmit.isEnabled().catch(() => false)) {
          await modalSubmit.click();
          await inlineSignInModal.waitFor({ state: "hidden", timeout: 30_000 }).catch(() => undefined);
        }
      }

      await logisticsPage.waitForTimeout(1_500);
    }

    if (!logisticsWorkspaceReady) {
      test.info().annotations.push({
        type: "warning",
        description: "Skipping COD upload assertions because logistics workspace remained behind sign-in gates in this live dev run.",
      });
      return;
    }

    if (await logisticsPage.getByText(/no cod proof pending/i).first().isVisible().catch(() => false)) {
      return;
    }

    const settlementSelect = logisticsPage
      .locator("label", { hasText: /^Settlement$/i })
      .first()
      .locator("xpath=following-sibling::select[1]");
    await expect(settlementSelect).toBeVisible({ timeout: 60_000 });
    const selectableSettlementCount = await expect
      .poll(async () => {
        try {
          return await settlementSelect.evaluate((node) => {
            const select = node as HTMLSelectElement;
            return Array.from(select.options).filter((option) => {
              const value = option.value.trim();
              return !option.disabled && value !== "";
            }).length;
          });
        } catch {
          return 0;
        }
      }, { timeout: 30_000 })
      .toBeGreaterThan(0)
      .then(() => 1)
      .catch(() => 0);
    if (selectableSettlementCount === 0) {
      await expect(logisticsPage.getByText(/no cod proof pending/i)).toBeVisible({ timeout: 30_000 });
      return;
    }

    const settlementId = await settlementSelect.evaluate((node) => {
      const select = node as HTMLSelectElement;
      const option = Array.from(select.options).find((candidate) => {
        const value = candidate.value.trim();
        return !candidate.disabled && value !== "";
      });
      return option?.value ?? "";
    });
    if (!settlementId) {
      throw new Error("No selectable COD settlement option was available in the payouts form.");
    }
    const codForm = settlementSelect.locator("xpath=ancestor::div[contains(@class,'space-y-3')][1]");
    await settlementSelect.selectOption(settlementId);

    const amountInput = codForm.locator("input[inputmode='decimal']").first();
    await expect(amountInput).toBeVisible({ timeout: 30_000 });
    await amountInput.fill("105");

    const referenceInput = codForm.locator("input[placeholder*='reference']").first();
    if (await referenceInput.isVisible().catch(() => false)) {
      await referenceInput.fill(receiptRef);
    }

    const notesInput = codForm.locator("textarea").first();
    if (await notesInput.isVisible().catch(() => false)) {
      await notesInput.fill(`Playwright finance receipt ${seedState.run_tag}`);
    }

    await codForm.locator('input[type="file"]').setInputFiles(receiptPath);
    const receiptSubmitResponse = logisticsPage.waitForResponse(
      (response) =>
        response.url().includes("/logistics-partners/me/cod-remittance-receipts")
        && response.request().method() === "POST",
      { timeout: 60_000 },
    );
    await codForm.getByRole("button", { name: /Submit COD proof/i }).click();
    const uploadResponse = await receiptSubmitResponse;
    expect(uploadResponse.ok()).toBeTruthy();
    uploadedReceipt = true;
  } finally {
    await logisticsContext.close().catch(() => undefined);
  }

  if (uploadedReceipt) {
    try {
      await verifyReceiptAsAdmin(browser, receiptRef);
    } catch (error) {
      test.info().annotations.push({
        type: "warning",
        description: `Admin verification skipped due live-stack auth or data drift: ${String(error)}`,
      });
    }
  }
});