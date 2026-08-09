import { expect, type Page } from "@playwright/test";

export async function expectNavigation(page: Page, expectedUrl: RegExp, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (expectedUrl.test(page.url())) return;
    await page.waitForTimeout(250);
  }
  throw new Error(`Timed out waiting for ${expectedUrl}, current URL: ${page.url()}`);
}

export async function waitForSessionFlag(page: Page, timeoutMs = 30_000) {
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

export async function openProtectedRoute(page: Page, path: string, expectedUrl: RegExp, timeoutMs = 120_000) {
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

async function apiLogin(page: Page, username: string, password: string): Promise<boolean> {
  const result = await page.evaluate(
    async (creds) => {
      try {
        const resp = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(creds),
          credentials: "include",
        });
        return { ok: resp.ok, status: resp.status, headers: [...resp.headers.entries()], body: await resp.text() };
      } catch (e) {
        return { ok: false, status: 0, error: String(e) };
      }
    },
    { username, password },
  );
  if (!result.ok) return false;
  const setCookie = (result.headers ?? []).find(([k]) => k.toLowerCase() === "set-cookie");
  if (setCookie) {
    const cookieValue = setCookie[1];
    const cookies = cookieValue.split(/,(?=[^ ]+?=)/).map((part) => {
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
  return true;
}

export async function bootstrapSessionViaApi(page: Page, candidates: string[], password: string) {
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 120_000 });
  for (const candidate of candidates) {
    const success = await apiLogin(page, candidate, password);
    if (!success) continue;
    await page.evaluate(() => window.localStorage.setItem("zozi_has_session", "1"));
    await page.request.get("/api/auth/me", { failOnStatusCode: false });
    return true;
  }
  return false;
}

export async function bootstrapAdminSessionViaApi(page: Page) {
  return bootstrapSessionViaApi(page, ["admin@zozi.com", "admin"], "admin123");
}

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
