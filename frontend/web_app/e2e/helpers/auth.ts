import { expect, type Page } from "@playwright/test";

async function expectNavigation(page: Page, expectedUrl: RegExp, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (expectedUrl.test(page.url())) return;
    await page.waitForTimeout(250);
  }
  throw new Error(`Timed out waiting for ${expectedUrl}, current URL: ${page.url()}`);
}

async function waitForSessionFlag(page: Page, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const hasLocalSession = await page
      .evaluate(() => window.localStorage.getItem("zozi_has_session") === "1")
      .catch(() => false);
    const cookies = await page.context().cookies();
    if (hasLocalSession || cookies.some((c) => c.name === "zozi_refresh" || c.name === "refresh_token")) {
      return;
    }
    const currentUrl = page.url();
    if (!/\/(?:admin\/login|logistics-partner\/login|supplier\/login|login)(?:\?|$)/.test(currentUrl)) {
      return;
    }
    await page.waitForTimeout(250);
  }
  throw new Error(`Timed out waiting for session state after ${timeoutMs}ms`);
}

async function openProtectedRoute(page: Page, path: string, expectedUrl: RegExp, timeoutMs = 120_000) {
  await page.goto(path, { waitUntil: "domcontentloaded", timeout: timeoutMs });
  await expectNavigation(page, expectedUrl, timeoutMs);
}

export async function submitCredentialForm(page: Page, username: string, password: string) {
  const submitButton = page.getByRole("button", { name: /sign in|log in|signin/i }).first();
  await submitButton.waitFor();
  const form = submitButton.locator("xpath=ancestor::form[1]");
  const identifierCandidates = [
    form.locator("input[name='username']:visible"),
    form.locator("input[autocomplete='username']:visible"),
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
  if (!identifierFilled) throw new Error("Unable to find a visible username/email input on the login form.");
  const passwordInput = form.locator("input[type='password']:visible").first();
  await passwordInput.fill(password);
  await expect(passwordInput).toHaveValue(password);
  await expect.poll(async () => submitButton.isEnabled(), { timeout: 15_000 }).toBe(true);
  await submitButton.click();
}

async function bootstrapSessionViaApi(page: Page, candidates: string[], password: string) {
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
  for (const candidate of candidates) {
    const response = await page.request.post("/api/auth/login", {
      form: { username: candidate, password },
      failOnStatusCode: false,
    });
    if (!response.ok()) continue;
    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1"));
    // Persist the auth cookies from the login response into the browser
    // context explicitly. page.request shares the context, but some setups
    // only set the cookie on the request scope; re-adding guarantees the
    // page navigation and subsequent XHRs are authenticated (prevents the
    // mid-test 401 → redirect-to-login that made admin/supplier collapse
    // checks flaky).
    const setCookie = response.headers()["set-cookie"];
    if (setCookie) {
      const cookies = setCookie.split(/,(?=[^ ]+?=)/).map((part) => {
        const [pair, ...attrs] = part.split(";");
        const [name, ...rest] = pair.split("=");
        return {
          name: name.trim(),
          value: rest.join("=").trim(),
          url: page.url(),
          path: attrs.find((a) => a.trim().toLowerCase().startsWith("path="))?.split("=")[1]?.trim() || "/",
          httpOnly: attrs.some((a) => a.trim().toLowerCase() === "httponly"),
          secure: attrs.some((a) => a.trim().toLowerCase() === "secure"),
        } as const;
      });
      try {
        await page.context().addCookies(cookies as any);
      } catch {
        /* best-effort */
      }
    }
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    return true;
  }
  return false;
}

/**
 * Establish an authenticated session robustly: try the API login (fast path),
 * and fall back to submitting the real login form (which reliably sets the
 * session cookie) if the API call is unavailable. Mirrors auth-role-login.spec.ts.
 */
export async function ensurePanelSession(
  page: Page,
  opts: { user: string; pass: string; loginPath: string; landing: string; landingRegex: RegExp },
) {
  const apiUser = opts.user.split("@")[0];
  const hasApiSession = await bootstrapSessionViaApi(page, [opts.user, apiUser], opts.pass);
  if (!hasApiSession) {
    await page.goto(opts.loginPath);
    await submitCredentialForm(page, opts.user, opts.pass);
    await waitForSessionFlag(page);
  }
  await openProtectedRoute(page, opts.landing, opts.landingRegex, 120_000);
}
