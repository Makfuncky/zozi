/**
 * Shared API helpers for Playwright E2E tests.
 *
 * Uses `page.request` (Playwright-native HTTP client) instead of
 * `page.evaluate(() => fetch(...))`. Benefits:
 *   - Runs outside the browser context (faster, no serialization)
 *   - Inherits cookies/auth from the page's browser context automatically
 *   - Works with network interception and route mocking
 *   - Proper error handling and TypeScript types
 *
 * Usage:
 *   import { apiPost, apiGet, registerUser, loginUser } from "./helpers/api";
 *   const { status, body } = await apiPost(page, "/api/auth/register", { email, password });
 */
import type { Page } from "@playwright/test";

// ── Types ──────────────────────────────────────────────────────────

export interface ApiResponse<T = Record<string, unknown>> {
  status: number;
  body: T;
}

// ── Low-level helpers ──────────────────────────────────────────────

export const API_BASE = process.env.API_BASE_URL || "http://127.0.0.1:8000";
export const WEB_BASE = process.env.WEB_BASE_URL || "http://127.0.0.1:3100";

/**
 * POST request via page.request (inherits cookies from browser context).
 */
export async function apiPost<T = Record<string, unknown>>(
  page: Page,
  path: string,
  data?: unknown,
  opts?: { headers?: Record<string, string>; timeout?: number }
): Promise<ApiResponse<T>> {
  try {
    const response = await page.request.post(`${API_BASE}${path}`, {
      data,
      headers: {
        "Content-Type": "application/json",
        ...opts?.headers,
      },
      timeout: opts?.timeout ?? 30_000,
      failOnStatusCode: false,
    });
    const body = (await response.json().catch(() => ({}))) as T;
    return { status: response.status(), body };
  } catch (e) {
    return { status: 0, body: { error: String(e) } as T };
  }
}

/**
 * GET request via page.request.
 */
export async function apiGet<T = Record<string, unknown>>(
  page: Page,
  path: string,
  opts?: { headers?: Record<string, string>; timeout?: number }
): Promise<ApiResponse<T>> {
  try {
    const response = await page.request.get(`${API_BASE}${path}`, {
      headers: opts?.headers,
      timeout: opts?.timeout ?? 30_000,
      failOnStatusCode: false,
    });
    const body = (await response.json().catch(() => ({}))) as T;
    return { status: response.status(), body };
  } catch (e) {
    return { status: 0, body: { error: String(e) } as T };
  }
}

/**
 * PATCH request via page.request.
 */
export async function apiPatch<T = Record<string, unknown>>(
  page: Page,
  path: string,
  data?: unknown,
  opts?: { headers?: Record<string, string>; timeout?: number }
): Promise<ApiResponse<T>> {
  try {
    const response = await page.request.patch(`${API_BASE}${path}`, {
      data,
      headers: {
        "Content-Type": "application/json",
        ...opts?.headers,
      },
      timeout: opts?.timeout ?? 30_000,
      failOnStatusCode: false,
    });
    const body = (await response.json().catch(() => ({}))) as T;
    return { status: response.status(), body };
  } catch (e) {
    return { status: 0, body: { error: String(e) } as T };
  }
}

/**
 * DELETE request via page.request.
 */
export async function apiDelete<T = Record<string, unknown>>(
  page: Page,
  path: string,
  opts?: { headers?: Record<string, string>; timeout?: number }
): Promise<ApiResponse<T>> {
  try {
    const response = await page.request.delete(`${API_BASE}${path}`, {
      headers: opts?.headers,
      timeout: opts?.timeout ?? 30_000,
      failOnStatusCode: false,
    });
    const body = (await response.json().catch(() => ({}))) as T;
    return { status: response.status(), body };
  } catch (e) {
    return { status: 0, body: { error: String(e) } as T };
  }
}

// ── Loud wrappers (throw on network failure or unexpected status) ────────────
// These MUST be used for assertions so a 404/timeout cannot be silently ignored.

export async function apiGetLoud<T = Record<string, unknown>>(
  page: Page,
  path: string,
  expectedStatus: number = 200,
  opts?: { headers?: Record<string, string>; timeout?: number }
): Promise<{ status: number; body: T; headers: Record<string, string> }> {
  try {
    const response = await page.request.get(`${API_BASE}${path}`, {
      headers: opts?.headers,
      timeout: opts?.timeout ?? 30_000,
      failOnStatusCode: false,
    });
    const status = response.status();
    if (status === 0) {
      throw new ApiError(`Network request failed: GET ${API_BASE}${path}`);
    }
    if (status !== expectedStatus) {
      const raw = await response.text().catch(() => "");
      throw new ApiError(
        `GET ${path} returned ${status} (expected ${expectedStatus}). Body: ${raw.slice(0, 500)}`
      );
    }
    const body = (await response.json().catch(() => ({}))) as T;
    const headers: Record<string, string> = {};
    response.headersArray().forEach((h) => {
      headers[h.name.toLowerCase()] = h.value;
    });
    return { status, body, headers };
  } catch (e) {
    if (e instanceof ApiError) throw e;
    throw new ApiError(`Network request failed: GET ${path}. Error: ${String(e)}`);
  }
}

export async function apiPostLoud<T = Record<string, unknown>>(
  page: Page,
  path: string,
  data?: unknown,
  expectedStatus: number = 200,
  opts?: { headers?: Record<string, string>; timeout?: number }
): Promise<{ status: number; body: T; headers: Record<string, string> }> {
  try {
    const response = await page.request.post(`${API_BASE}${path}`, {
      data,
      headers: {
        "Content-Type": "application/json",
        ...opts?.headers,
      },
      timeout: opts?.timeout ?? 30_000,
      failOnStatusCode: false,
    });
    const status = response.status();
    if (status === 0) {
      throw new ApiError(`Network request failed: POST ${API_BASE}${path}`);
    }
    if (status !== expectedStatus) {
      const raw = await response.text().catch(() => "");
      throw new ApiError(
        `POST ${path} returned ${status} (expected ${expectedStatus}). Body: ${raw.slice(0, 500)}`
      );
    }
    const body = (await response.json().catch(() => ({}))) as T;
    const headers: Record<string, string> = {};
    response.headersArray().forEach((h) => {
      headers[h.name.toLowerCase()] = h.value;
    });
    return { status, body, headers };
  } catch (e) {
    if (e instanceof ApiError) throw e;
    throw new ApiError(`Network request failed: POST ${path}. Error: ${String(e)}`);
  }
}

export async function apiPatchLoud<T = Record<string, unknown>>(
  page: Page,
  path: string,
  data?: unknown,
  expectedStatus: number = 200,
  opts?: { headers?: Record<string, string>; timeout?: number }
): Promise<{ status: number; body: T; headers: Record<string, string> }> {
  try {
    const response = await page.request.patch(`${API_BASE}${path}`, {
      data,
      headers: {
        "Content-Type": "application/json",
        ...opts?.headers,
      },
      timeout: opts?.timeout ?? 30_000,
      failOnStatusCode: false,
    });
    const status = response.status();
    if (status === 0) {
      throw new ApiError(`Network request failed: PATCH ${API_BASE}${path}`);
    }
    if (status !== expectedStatus) {
      const raw = await response.text().catch(() => "");
      throw new ApiError(
        `PATCH ${path} returned ${status} (expected ${expectedStatus}). Body: ${raw.slice(0, 500)}`
      );
    }
    const body = (await response.json().catch(() => ({}))) as T;
    const headers: Record<string, string> = {};
    response.headersArray().forEach((h) => {
      headers[h.name.toLowerCase()] = h.value;
    });
    return { status, body, headers };
  } catch (e) {
    if (e instanceof ApiError) throw e;
    throw new ApiError(`Network request failed: PATCH ${path}. Error: ${String(e)}`);
  }
}

export async function apiDeleteLoud<T = Record<string, unknown>>(
  page: Page,
  path: string,
  expectedStatus: number = 200,
  opts?: { headers?: Record<string, string>; timeout?: number }
): Promise<{ status: number; body: T; headers: Record<string, string> }> {
  try {
    const response = await page.request.delete(`${API_BASE}${path}`, {
      headers: opts?.headers,
      timeout: opts?.timeout ?? 30_000,
      failOnStatusCode: false,
    });
    const status = response.status();
    if (status === 0) {
      throw new ApiError(`Network request failed: DELETE ${API_BASE}${path}`);
    }
    if (status !== expectedStatus) {
      const raw = await response.text().catch(() => "");
      throw new ApiError(
        `DELETE ${path} returned ${status} (expected ${expectedStatus}). Body: ${raw.slice(0, 500)}`
      );
    }
    const body = (await response.json().catch(() => ({}))) as T;
    const headers: Record<string, string> = {};
    response.headersArray().forEach((h) => {
      headers[h.name.toLowerCase()] = h.value;
    });
    return { status, body, headers };
  } catch (e) {
    if (e instanceof ApiError) throw e;
    throw new ApiError(`Network request failed: DELETE ${path}. Error: ${String(e)}`);
  }
}

export class ApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiError";
  }
}

// ── Domain helpers ─────────────────────────────────────────────────

const TEST_PASSWORD = process.env.E2E_TEST_PASSWORD || "TestPass123!";

export function uniqueEmail(role: string) {
  return `e2e_${role}_${Date.now()}@zozi-test.com`;
}

export function uniqueUsername(role: string) {
  return `e2e_${role}_${Date.now()}`;
}

// ── Response types ─────────────────────────────────────────────────

export interface RegisterResponse {
  id?: number;
  email?: string;
  username?: string;
  role?: string;
  detail?: string;
}

export interface LoginResponse {
  access_token?: string;
  refresh_token?: string;
  detail?: string;
}

export interface MeResponse {
  id?: number;
  email?: string;
  username?: string;
  role?: string;
}

/**
 * Register a user via the backend API.
 */
export async function registerUser(
  page: Page,
  opts: {
    email: string;
    username: string;
    password: string;
    role: string;
    business_name?: string;
    phone?: string;
  }
): Promise<ApiResponse<RegisterResponse>> {
  return apiPost<RegisterResponse>(page, "/api/v1/auth/register", opts);
}

/**
 * Login via the backend API and return tokens.
 */
export async function loginUser(
  page: Page,
  identifier: string,
  password: string = TEST_PASSWORD
): Promise<ApiResponse<LoginResponse>> {
  // The admin/supplier/customer/logistics frontend forms all send
  // { username, password }; the backend coerces username -> email when email
  // is absent, so the identifier (email or username) is passed as username.
  return apiPost<LoginResponse>(page, "/api/v1/auth/login", { username: identifier, password });
}

/**
 * Verify a user's token by calling /api/v1/auth/me.
 */
export async function verifyUser(
  page: Page,
  token: string
): Promise<ApiResponse<MeResponse>> {
  return apiGet<MeResponse>(page, "/api/v1/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}
