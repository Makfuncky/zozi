import { createResponseRequestCache, shouldUseShortGetCache } from "@shared/requestCache";

function createMockResponse(body: unknown, status = 200) {
  const bodyString = JSON.stringify(body);
  const headers = new Headers({ "content-type": "application/json" });

  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 404 ? "Not Found" : "OK",
    headers,
    json: async () => body,
    clone() {
      return createMockResponse(body, status);
    },
  } as unknown as Response;
}

describe("shouldUseShortGetCache", () => {
  it("skips short cache for protected admin reads", () => {
    expect(shouldUseShortGetCache("/admin/email/stats", "GET")).toBe(false);
  });

  it("skips short cache for protected email management reads", () => {
    expect(shouldUseShortGetCache("/email/campaigns", "GET")).toBe(false);
  });

  it("still allows short cache for public GET requests", () => {
    expect(shouldUseShortGetCache("/products?featured=true", "GET")).toBe(true);
  });
});

describe("createResponseRequestCache", () => {
  it("caches successful responses", async () => {
    const cache = createResponseRequestCache();
    const loader = jest.fn(async () => createMockResponse({ ok: true }));

    const first = await cache.getOrSet("products", loader, 2500, (response) => response.ok);
    const second = await cache.getOrSet("products", loader, 2500, (response) => response.ok);

    await expect(first.json()).resolves.toEqual({ ok: true });
    await expect(second.json()).resolves.toEqual({ ok: true });
    expect(loader).toHaveBeenCalledTimes(1);
  });

  it("returns non-ok responses without caching them", async () => {
    const cache = createResponseRequestCache();
    const loader = jest.fn(async () => createMockResponse({ detail: "missing" }, 404));

    const first = await cache.getOrSet("missing", loader, 2500, (response) => response.ok);
    const second = await cache.getOrSet("missing", loader, 2500, (response) => response.ok);

    expect(first.status).toBe(404);
    expect(second.status).toBe(404);
    await expect(first.json()).resolves.toEqual({ detail: "missing" });
    await expect(second.json()).resolves.toEqual({ detail: "missing" });
    expect(loader).toHaveBeenCalledTimes(2);
  });
});
