/**
 * In-memory auth token management, silent refresh, and session state.
 *
 * Token strategy (XSS hardening):
 *   - ACCESS token: stored only in memory (module-level variable).
 *     Never written to localStorage or a non-httpOnly cookie.
 *   - REFRESH token: lives in an httpOnly cookie set by the backend,
 *     never readable from JavaScript.
 *   - `zozi_has_session`: non-sensitive boolean in localStorage that tells
 *     the frontend whether to attempt a silent refresh on page load.
 */

import { responseCache, apiFetch } from "./client";

// ── Token store ──────────────────────────────────────────────────────────

const _store = {
  accessToken: null as string | null,
  refreshPromise: null as Promise<RefreshResult> | null,
  traceId: null as string | null,
};

export type RefreshResult =
  | { status: "ok"; accessToken: string }
  | { status: "no_session" }
  | { status: "rejected" }
  | { status: "network" };

/** Set the in-memory access token after a successful login or token refresh. */
export function setAccessToken(token: string | null): void {
  _store.accessToken = token;
  responseCache.invalidateAll();
}

/** Read the current in-memory access token. */
export function getAccessToken(): string | null {
  return _store.accessToken;
}

/** Clear the in-memory access token on logout / 401. */
export function clearAccessToken(): void {
  _store.accessToken = null;
  responseCache.invalidateAll();
}

/** Expose trace ID storage for the trace-context module. */
export function _getTraceIdStore() {
  return _store;
}

// ── Silent refresh ──────────────────────────────────────────────────────

const REFRESH_NETWORK_RETRIES = 2;
const REFRESH_RETRY_DELAY_MS = 300;

export async function silentlyRefreshAccessToken(): Promise<RefreshResult> {
  if (typeof window === "undefined") return { status: "network" };
  if (localStorage.getItem("zozi_has_session") !== "1") return { status: "no_session" };

  if (_store.refreshPromise) {
    return _store.refreshPromise;
  }


  const attempt = async (triesLeft: number): Promise<RefreshResult> => {
    try {
      const res = await apiFetch("/auth/refresh", {
        method: "POST",
      });
      if (!res.ok) {
        clearSessionState();
        return { status: "rejected" };
      }
      const data = await res.json();
      if (!data?.access_token) {
        clearSessionState();
        return { status: "rejected" };
      }
      setAccessToken(data.access_token);
      localStorage.setItem("zozi_has_session", "1");
      return { status: "ok", accessToken: data.access_token };
    } catch {
      if (triesLeft > 0) {
        await new Promise((resolve) => setTimeout(resolve, REFRESH_RETRY_DELAY_MS));
        return attempt(triesLeft - 1);
      }
      return { status: "network" };
    }
  };

  _store.refreshPromise = attempt(REFRESH_NETWORK_RETRIES);
  try {
    return await _store.refreshPromise;
  } finally {
    _store.refreshPromise = null;
  }
}

// ── JWT helpers ─────────────────────────────────────────────────────────

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  const [, payloadSegment] = token.split(".");
  if (!payloadSegment) return null;

  try {
    const normalized = payloadSegment.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    const decoded = atob(padded);
    const payload = JSON.parse(decoded);
    return payload && typeof payload === "object" ? (payload as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

export function isAccessTokenExpiringSoon(token: string, skewSeconds = 30): boolean {
  const payload = decodeJwtPayload(token);
  const exp = payload?.exp;
  if (typeof exp !== "number") return false;
  return exp * 1000 <= Date.now() + skewSeconds * 1000;
}

// ── Session state ───────────────────────────────────────────────────────

export async function ensureAccessToken(): Promise<void> {
  if (_store.accessToken && !isAccessTokenExpiringSoon(_store.accessToken)) return;
  await silentlyRefreshAccessToken();
}

export function clearSessionState(): void {
  clearAccessToken();
  if (typeof window !== "undefined") {
    localStorage.removeItem("zozi_has_session");
  }
}
