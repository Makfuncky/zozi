import { expect, test, type Page } from "@playwright/test";
import { bootstrapAdminSessionViaApi } from "./helpers/auth";

test.describe.configure({ timeout: 240_000 });

function escapeRegex(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

async function expectNavigation(page: Page, expectedUrl: RegExp, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (expectedUrl.test(page.url())) {
      return;
    }
    await page.waitForTimeout(250);
  }

  throw new Error(`Timed out waiting for ${expectedUrl}, current URL: ${page.url()}`);
}

async function openProtectedRoute(
  page: Page,
  path: string,
  expectedUrl: RegExp,
  timeoutMs = 60_000,
) {
  await page.goto(path, { waitUntil: "domcontentloaded", timeout: timeoutMs });
  await expectNavigation(page, expectedUrl, timeoutMs);
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

async function isAdminAccessGateVisible(page: Page, timeoutMs = 3_000) {
  try {
    await page.getByRole("heading", { name: /Admin Access/i }).first().waitFor({ state: "visible", timeout: timeoutMs });
    return true;
  } catch {
    return false;
  }
}

async function submitCredentialForm(page: Page, username: string, password: string) {
  const submitButton = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  await submitButton.waitFor();
  const form = submitButton.locator("xpath=ancestor::form[1]");
  const identifierCandidates = [
    form.locator("input[name='username']:visible"),
    form.locator("input[autocomplete='username']:visible"),
    form.locator("input[required]:not([type='password']):visible"),
    form.locator("input[type='email']:visible"),
    form.locator("input:not([type='password']):visible"),
  ];

  let identifierFilled = false;
  for (const candidate of identifierCandidates) {
    if (await candidate.count()) {
      await candidate.first().fill(username);
      await expect(candidate.first()).toHaveValue(username);
      identifierFilled = true;
      break;
    }
  }

  if (!identifierFilled) {
    throw new Error("Unable to find a visible username/email input on the login form.");
  }

  const passwordInput = form.locator("input[type='password']:visible").first();
  await passwordInput.fill(password);
  await expect(passwordInput).toHaveValue(password);
  await expect.poll(async () => submitButton.isEnabled()).toBe(true);
  await submitButton.click();
}

async function loginAsAdmin(page: Page, destination = "/admin/dashboard") {
  for (const candidate of ["admin@zozi.com", "admin"]) {
    await bootstrapAdminSessionViaApi(page);
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1"));
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    await openProtectedRoute(page, destination, /\/admin\/(dashboard|finance)(?:\?|$)/, 120_000);
    if (!(await isAdminAccessGateVisible(page))) {
      return;
    }
  }

  await page.goto("/admin/login", { waitUntil: "domcontentloaded" });
  await submitCredentialForm(page, "admin@zozi.com", "admin123");
  try {
    await waitForSessionFlag(page, 30_000);
  } catch {
    const retrySubmit = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
    await expect.poll(async () => retrySubmit.isEnabled(), { timeout: 30_000 }).toBe(true);
    if (!(await hasSessionState(page))) {
      // Retry once with username-style credentials because some recovered login paths
      // are stricter than email-style identifiers during first-page hydration.
      await submitCredentialForm(page, "admin", "admin123");
    }
  }
  await waitForSessionFlag(page, 60_000);
  await openProtectedRoute(page, destination, /\/admin\/(dashboard|finance)(?:\?|$)/, 120_000);

  if (await isAdminAccessGateVisible(page)) {
    await page.goto("/admin/login", { waitUntil: "domcontentloaded" });
    await submitCredentialForm(page, "admin", "admin123");
    await waitForSessionFlag(page, 60_000);
    await openProtectedRoute(page, destination, /\/admin\/(dashboard|finance)(?:\?|$)/, 120_000);
  }

  if (await isAdminAccessGateVisible(page)) {
    for (const candidate of ["admin@zozi.com", "admin"]) {
      await bootstrapAdminSessionViaApi(page);
      await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1"));
      await page.request.get("/api/auth/me", { failOnStatusCode: false });
      await openProtectedRoute(page, destination, /\/admin\/(dashboard|finance)(?:\?|$)/, 120_000);
      if (!(await isAdminAccessGateVisible(page))) {
        break;
      }
    }
  }

  if (await isAdminAccessGateVisible(page)) {
    throw new Error("Admin login gate remained visible after credential retries");
  }
}

test("admin exports workspace supports data download and backup operations", async ({ page }) => {
  test.setTimeout(300_000);

  await loginAsAdmin(page, "/admin/dashboard?tab=exports");

  await expect(page.getByText("Background Exports")).toBeVisible({ timeout: 120_000 });
  await expect(page.getByText("Database Operations")).toBeVisible({ timeout: 120_000 });
  await expect(page.getByText("Database Tables")).toBeVisible({ timeout: 120_000 });
  await expect(page.getByText("Database Backups")).toBeVisible();

  await page.getByRole("button", { name: "Run database health check" }).click();
  await expect
    .poll(async () => page.locator("[data-database-table]").count(), { timeout: 120_000 })
    .toBeGreaterThan(0);

  await page.getByRole("textbox", { name: "Search database tables" }).fill("users");
  await expect(page.locator("[data-database-table='users']").first()).toBeVisible({ timeout: 120_000 });
  await page.getByRole("textbox", { name: "Search database tables" }).fill("");

  await page.getByRole("button", { name: "Trigger database backup" }).click();

  await expect
    .poll(async () => page.locator("[data-backup-filename]").count(), { timeout: 120_000 })
    .toBeGreaterThan(0);

  const latestRow = page.locator("[data-backup-filename]").first();
  const latestFilename = await latestRow.getAttribute("data-backup-filename");
  expect(latestFilename).toBeTruthy();

  await page.getByRole("button", { name: "Run restore drill for latest backup" }).click();
  await expect(page.getByText(/Restore drill:\s*passed/i).first()).toBeVisible({ timeout: 120_000 });

  await page.getByRole("button", { name: "Download latest database backup" }).click();
  await expect(page.getByText(/Backup downloaded:/i).first()).toBeVisible({ timeout: 120_000 });

  const backupDownloadButton = page.getByRole("button", {
    name: new RegExp(`^Download backup ${escapeRegex(String(latestFilename))}$`),
  }).first();
  await expect(backupDownloadButton).toBeVisible({ timeout: 120_000 });
  await backupDownloadButton.click();
  await expect(page.getByText(new RegExp(`Backup downloaded:\\s*${escapeRegex(String(latestFilename))}`, "i")).first()).toBeVisible({ timeout: 120_000 });

  await page.getByRole("button", { name: "Export Users" }).click();
  await expect(page.getByText(/Users export downloaded/i).first()).toBeVisible({ timeout: 120_000 });
  await expect(page.getByText(/Last file:\s*.*user/i).first()).toBeVisible({ timeout: 120_000 });
});
