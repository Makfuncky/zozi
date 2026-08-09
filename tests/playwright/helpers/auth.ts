import { expect, type Page } from "@playwright/test";

export async function loginAs(page: Page, email: string, password: string): Promise<void> {
  const token = await apiLogin(page, email, password);
  await page.route("**/*", async (route) => {
    const headers = { ...route.request().headers() };
    if (!headers["authorization"]) {
      headers["authorization"] = `Bearer ${token}`;
    }
    route.continue({ headers });
  });
  await page.goto("/", { waitUntil: "domcontentloaded", timeout: 60_000 });
}

export async function expectApiJson(page: Page, url: string, expectedStatus: number) {
  const resp = await page.request.get(url);
  expect(resp.status()).toBe(expectedStatus);
  return await resp.json();
}

export async function apiLogin(page: Page, email: string, password: string) {
  const resp = await page.request.post("/auth/login", {
    json: { username: email, password },
    failOnStatusCode: false,
  });
  expect(resp.ok()).toBe(true);
  const data = await resp.json();
  return data.access_token as string;
}
