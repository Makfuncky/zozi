import type { FullConfig } from "@playwright/test";

/**
 * Phase 5A: Port-mismatch sanity check.
 *
 * Verifies the backend is reachable on the URL the frontend is configured
 * to proxy to (NEXT_PUBLIC_API_URL, default http://127.0.0.1:8001) before
 * any test runs. Catches the "run_e2e.ps1 started backend on 8000 but
 * .env.local points to 8001" failure mode at startup rather than 30
 * minutes into the suite.
 */
export default async function globalSetup(config: FullConfig) {
  const apiUrl =
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") ??
    "http://127.0.0.1:8001";
  const healthUrl = `${apiUrl}/health`;
  const timeoutMs = 10_000;

  const startedAt = Date.now();
  const tryFetch = async (): Promise<boolean> => {
    try {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), 2000);
      const res = await fetch(healthUrl, { signal: ctrl.signal });
      clearTimeout(t);
      return res.ok;
    } catch {
      return false;
    }
  };

  let ok = false;
  while (Date.now() - startedAt < timeoutMs) {
    if (await tryFetch()) {
      ok = true;
      break;
    }
    await new Promise((r) => setTimeout(r, 500));
  }

  if (!ok) {
    // eslint-disable-next-line no-console
    console.error(
      [
        "",
        "═══════════════════════════════════════════════════════════════",
        "  PORT-MISMATCH / BACKEND NOT REACHABLE",
        "═══════════════════════════════════════════════════════════════",
        `  Tried: ${healthUrl}`,
        `  Frontend .env.local has NEXT_PUBLIC_API_URL=${apiUrl}`,
        "",
        "  Make sure run_e2e.ps1 started the backend on the matching port.",
        "  - run_e2e.ps1 default: backend on 8001 → .env.local should be 8001",
        "  - Manual dev uvicorn:  backend on 8000 → .env.local should be 8000",
        "",
        "  The Playwright suite will now start; expect all tests to fail",
        "  in 'session bootstrap' until this is fixed.",
        "═══════════════════════════════════════════════════════════════",
        "",
      ].join("\n")
    );
    throw new Error(
      `Backend not reachable at ${healthUrl}. Port mismatch between run_e2e.ps1 and frontend/.env.local.`
    );
  }
}
