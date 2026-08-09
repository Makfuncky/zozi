/**
 * Barrel re-export — keeps all existing `import { ... } from "@/lib/api"`
 * and `import { ... } from "./api"` paths working unchanged.
 */

export { apiFetch, API_URL, DEFAULT_API_TIMEOUT_MS, parseJsonResponse, isUrlSameOrigin } from "./client";
export { setAccessToken, getAccessToken, clearAccessToken, silentlyRefreshAccessToken, clearSessionState, type RefreshResult } from "./auth";
export { getErrorMessage, categorizeError, handleApiError } from "./errors";
export { detectCountryFromIP, getEffectiveCountryCode, getAutoDetectedCountry, setAutoDetectedCountry, STORAGE_KEY } from "./country";
