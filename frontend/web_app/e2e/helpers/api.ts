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

export const API_BASE = process.env.API_BASE_URL || "http://localhost:8000";
export const WEB_BASE = process.env.WEB_BASE_URL || "http://localhost:3000";

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
  return apiPost<RegisterResponse>(page, "/api/auth/register", opts);
}

/**
 * Login via the backend API and return tokens.
 */
export async function loginUser(
  page: Page,
  email: string,
  password: string = TEST_PASSWORD
): Promise<ApiResponse<LoginResponse>> {
  return apiPost<LoginResponse>(page, "/api/auth/login", { email, password });
}

/**
 * Verify a user's token by calling /api/auth/me.
 */
export async function verifyUser(
  page: Page,
  token: string
): Promise<ApiResponse<MeResponse>> {
  return apiGet<MeResponse>(page, "/api/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}
