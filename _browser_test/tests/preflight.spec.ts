import { expect, test, chromium } from "@playwright/test";
import { apiGet } from "../src/api";
import { bootstrapAdminSessionViaApi } from "../src/auth";

test.describe.configure({ timeout: 120_000 });

test("Playwright browsers are installed", async () => {
  const launched = await chromium.launch().catch(() => null);
  if (launched) {
    await launched.close();
  }
  expect(launched).not.toBeNull();
});

test("Backend health endpoint returns 200", async ({ page }) => {
  const { status, body } = await apiGet(page, "/health", { timeout: 30_000 });
  expect(status).toBe(200);
  expect(body).toMatchObject({ status: "healthy" });
});

test("Backend /health/deps reports Valkey and DB as connected", async ({ page }) => {
  const { status, body } = await apiGet(page, "/health/deps", { timeout: 30_000 });
  expect(status).toBe(200);
  const deps = (body as any).dependencies ?? body;
  expect(deps).toBeDefined();
  expect(deps.database?.status ?? deps.database).toBe("ok");
  expect(deps.valkey?.status ?? deps.valkey).toBe("ok");
});

test("Frontend is serving on configured port", async ({ page }) => {
  const response = await page.request.get("http://127.0.0.1:3100", {
    timeout: 30_000,
  });
  expect(response.status()).toBe(200);
  expect(response.headers()["content-type"]).toContain("text/html");
});

test("Rbac catalog endpoint is reachable", async ({ page }) => {
  await bootstrapAdminSessionViaApi(page);
  const { status, body } = await apiGet(page, "/api/v1/rbac/catalog", {
    timeout: 30_000,
  });
  expect(status).toBe(200);
  const catalog = body as any;
  expect(
    Array.isArray(catalog.feature_list) ||
      (catalog.features && typeof catalog.features === "object"),
  ).toBe(true);
});

test("Database responds to a simple query", async ({ page }) => {
  const { body } = await apiGet(page, "/health", { timeout: 30_000 });
  const deps = (body as any).dependencies ?? body;
  expect(deps.database?.status ?? deps.database).toBe("ok");
});

test("Valkey is reachable", async ({ page }) => {
  const { body } = await apiGet(page, "/health/deps", { timeout: 30_000 });
  const deps = (body as any).dependencies ?? body;
  expect(deps.valkey?.status ?? deps.valkey).toBe("ok");
});
