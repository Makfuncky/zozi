/**
 * Tests for web_app/src/lib/api.ts
 * Covers: getErrorMessage, handleApiError, setAccessToken, clearAccessToken,
 *         apiFetch (Bearer token, CSRF header, 401 clear).
 */

import {
  getErrorMessage,
  handleApiError,
  setAccessToken,
  getAccessToken,
  clearAccessToken,
  parseJsonResponse,
  apiFetch,
  isUrlSameOrigin,
} from "@/lib/api";

// ── getErrorMessage ───────────────────────────────────────────────────────────

describe("getErrorMessage", () => {
  it("returns string detail directly", () => {
    expect(getErrorMessage({ detail: "Not found" })).toBe("Not found");
  });

  it("returns first msg from pydantic array detail", () => {
    expect(
      getErrorMessage({ detail: [{ loc: ["body"], msg: "field required", type: "value_error" }] })
    ).toBe("field required");
  });

  it("falls back to message property", () => {
    expect(getErrorMessage({ message: "Something broke" })).toBe("Something broke");
  });

  it("returns fallback string for unrecognised shape", () => {
    expect(getErrorMessage({})).toBe("An error occurred");
  });
});

// ── handleApiError ────────────────────────────────────────────────────────────

describe("handleApiError", () => {
  let spy: jest.SpyInstance;
  beforeEach(() => { spy = jest.spyOn(console, "error").mockImplementation(() => {}); });
  afterEach(() => spy.mockRestore());

  it("logs Error instance message", () => {
    handleApiError(new Error("boom"), "test");
    expect(spy).toHaveBeenCalledWith(
      expect.stringContaining("boom"),
      expect.any(Error)
    );
  });

  it("logs string errors", () => {
    handleApiError("network failure", "ctx");
    expect(spy).toHaveBeenCalledWith(
      expect.stringContaining("network failure"),
      "network failure"
    );
  });

  it("logs Response objects with status", () => {
    const fakeResponse = new Response(null, { status: 404, statusText: "Not Found" });
    handleApiError(fakeResponse);
    expect(spy).toHaveBeenCalledWith(
      expect.stringContaining("404"),
      fakeResponse
    );
  });

  it("logs object errors via getErrorMessage", () => {
    handleApiError({ detail: "Unauthorized" });
    expect(spy).toHaveBeenCalledWith(
      expect.stringContaining("Unauthorized"),
      expect.any(Object)
    );
  });
});

// ── Token helpers ─────────────────────────────────────────────────────────────

describe("access token helpers", () => {
  afterEach(() => clearAccessToken());

  it("is null initially", () => {
    clearAccessToken();
    expect(getAccessToken()).toBeNull();
  });

  it("stores and retrieves a token", () => {
    setAccessToken("abc123");
    expect(getAccessToken()).toBe("abc123");
  });

  it("clears the token", () => {
    setAccessToken("tok");
    clearAccessToken();
    expect(getAccessToken()).toBeNull();
  });
});

// ── parseJsonResponse ────────────────────────────────────────────────────────

describe("parseJsonResponse", () => {
  it("parses a JSON response", async () => {
    const res = new Response(JSON.stringify({ hello: "world" }), {
      headers: { "content-type": "application/json" },
    });
    const data = await parseJsonResponse(res);
    expect(data).toEqual({ hello: "world" });
  });

  it("returns null for non-JSON content-type", async () => {
    const res = new Response("<html>ok</html>", {
      headers: { "content-type": "text/html" },
    });
    const data = await parseJsonResponse(res);
    expect(data).toBeNull();
  });
});

// ── apiFetch ────────────────────────────────────────────────────────────────

describe("apiFetch", () => {
  const originalFetch = global.fetch;

  const createJwt = (exp: number) => {
    const encode = (value: object) => Buffer.from(JSON.stringify(value)).toString("base64url");
    return `${encode({ alg: "HS256", typ: "JWT" })}.${encode({ exp })}.signature`;
  };

  beforeEach(() => {
    clearAccessToken();
    localStorage.clear();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
    clearAccessToken();
    localStorage.clear();
  });

  it("refreshes before issuing a request when the access token is already expired", async () => {
    localStorage.setItem("zozi_has_session", "1");
    setAccessToken(createJwt(Math.floor(Date.now() / 1000) - 60));
    const observedAuthorizationHeaders: string[] = [];

    const fetchMock = jest.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      observedAuthorizationHeaders.push(new Headers(init?.headers).get("Authorization") || "");
      if (fetchMock.mock.calls.length === 1) {
        return new Response(JSON.stringify({ access_token: "fresh-token" }), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      }

      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    });

    global.fetch = fetchMock as typeof fetch;

    const response = await apiFetch("/admin/database/overview");

    expect(response.ok).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/auth/refresh");
    expect(fetchMock.mock.calls[1]?.[0]).toBe("http://127.0.0.1:8000/admin/database/overview");
    expect(observedAuthorizationHeaders[0]).toBe("");
    expect(observedAuthorizationHeaders[1]).toBe("Bearer fresh-token");
    expect(getAccessToken()).toBe("fresh-token");
  });

  it("refreshes and retries once after a 401 from a protected request", async () => {
    localStorage.setItem("zozi_has_session", "1");
    setAccessToken("expired-token");
    const observedAuthorizationHeaders: string[] = [];

    const fetchMock = jest.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      observedAuthorizationHeaders.push(new Headers(init?.headers).get("Authorization") || "");
      switch (fetchMock.mock.calls.length) {
        case 1:
          return new Response(JSON.stringify({ detail: "Invalid token" }), {
            status: 401,
            headers: { "content-type": "application/json" },
          });
        case 2:
          return new Response(JSON.stringify({ access_token: "fresh-token" }), {
            status: 200,
            headers: { "content-type": "application/json" },
          });
        default:
          return new Response(JSON.stringify({ ok: true }), {
            status: 200,
            headers: { "content-type": "application/json" },
          });
      }
    });

    global.fetch = fetchMock as typeof fetch;

    const response = await apiFetch("/ai/suggest/async", { method: "POST", body: new FormData() });

    expect(response.ok).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[0]?.[0]).toBe("http://127.0.0.1:8000/ai/suggest/async");
    expect(fetchMock.mock.calls[1]?.[0]).toBe("/api/auth/refresh");
    expect(fetchMock.mock.calls[2]?.[0]).toBe("http://127.0.0.1:8000/ai/suggest/async");
    expect(observedAuthorizationHeaders[0]).toBe("Bearer expired-token");
    expect(observedAuthorizationHeaders[1]).toBe("");
    expect(observedAuthorizationHeaders[2]).toBe("Bearer fresh-token");
    expect(getAccessToken()).toBe("fresh-token");
  });

  it("expires the session when refresh cannot recover a 401", async () => {
    localStorage.setItem("zozi_has_session", "1");
    setAccessToken("expired-token");
    const dispatchSpy = jest.spyOn(window, "dispatchEvent");

    const fetchMock = jest.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "Invalid token" }), {
        status: 401,
        headers: { "content-type": "application/json" },
      }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: null }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }));

    global.fetch = fetchMock as typeof fetch;

    const response = await apiFetch("/ai/suggest/async", { method: "POST", body: new FormData() });

    expect(response.status).toBe(401);
    expect(getAccessToken()).toBeNull();
    expect(localStorage.getItem("zozi_has_session")).toBeNull();
    expect(dispatchSpy).toHaveBeenCalledWith(expect.objectContaining({ type: "zozi:auth-expired" }));
  });

  it("attaches normalized X-Country-Code from persisted currency state", async () => {
    localStorage.setItem("zozi_currency", JSON.stringify({ state: { selectedCountry: "Pakistan" } }));

    const fetchMock = jest.fn(async (_input: RequestInfo | URL, init?: RequestInit) => {
      const headers = new Headers(init?.headers);
      return new Response(JSON.stringify({ ok: true, country: headers.get("X-Country-Code") }), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
    });
    global.fetch = fetchMock as typeof fetch;

    const response = await apiFetch("/products", { disableCache: true });
    const body = await response.json();

    expect(response.ok).toBe(true);
    expect(body.country).toBe("PK");
  });
});

// ── isUrlSameOrigin ──────────────────────────────────────────────────────────

describe("isUrlSameOrigin", () => {
  it("returns true when the URL origin matches the current origin", () => {
    expect(isUrlSameOrigin("http://localhost:8000/products", "http://localhost:8000")).toBe(true);
  });

  it("returns false when the URL origin differs from the current origin", () => {
    expect(isUrlSameOrigin("http://localhost:8000/products", "http://localhost:3000")).toBe(false);
  });
});
