/**
 * Typed API client using openapi-fetch
 * Provides type-safe API calls based on FastAPI OpenAPI schema
 */

import createClient from "openapi-fetch";
import type { paths } from "../types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Create a typed API client with authentication
 */
export function createApiClient(accessToken?: string) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  return createClient<paths>({
    baseUrl: API_BASE_URL,
    headers,
  });
}

/**
 * Default API client without authentication
 */
export const api = createClient<paths>({
  baseUrl: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * API client factory for server-side usage with token
 */
export function getServerApiClient(token: string) {
  return createClient<paths>({
    baseUrl: API_BASE_URL,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });
}

export default api;
