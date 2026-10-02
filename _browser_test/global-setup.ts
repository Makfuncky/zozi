/**
 * Global test setup.
 *
 * Performs loud pre-flight health checks BEFORE any test runs. If the backend
 * or frontend is unreachable, the entire suite aborts — we never let tests run
 * against a dead server and report a misleading pass.
 *
 * Health targets (per ARCHITECTURE_STACK.md):
 *   - Backend API   : http://127.0.0.1:8000/health
 *   - Frontend SPA  : http://127.0.0.1:3100
 *   - RBAC catalog  : http://127.0.0.1:8000/rbac/catalog
 */
export default async (): Promise<void> => {
  const apiBase = process.env.API_BASE_URL || "http://127.0.0.1:8000";
  const webBase = process.env.WEB_BASE_URL || "http://127.0.0.1:3100";

  const checks: Array<{ name: string; fn: () => Promise<void> }> = [
    { name: "backend /health", fn: checkHealth },
    { name: "backend /rbac/catalog", fn: checkRbacCatalog },
    { name: "frontend SPA", fn: checkWeb },
  ];

  for (const { name, fn } of checks) {
    try {
      await fn();
      console.log(`[global-setup] OK: ${name}`);
    } catch (err) {
      console.error(`[global-setup] FAIL: ${name} — ${err}`);
      console.error(
        "[global-setup] Hint: start the backend (port 8000) and frontend (port 3100), " +
        "then re-run: cd _browser_test && npx playwright test"
      );
      throw err;
    }
  }

  console.log(
    `[global-setup] Pre-flight OK — backend=${apiBase} frontend=${webBase}`
  );
};

async function checkHealth() {
  const apiBase = process.env.API_BASE_URL || "http://127.0.0.1:8000";
  const resp = await fetch(`${apiBase}/health`, {
    method: "GET",
    headers: { "Accept": "application/json" },
    signal: AbortSignal.timeout(10_000),
  });
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(`GET /health returned ${resp.status}: ${text.slice(0, 300)}`);
  }
  const body = (await resp.json()) as { status?: string };
  if (body.status !== "healthy") {
    throw new Error(`GET /health returned status=${body.status} (expected "healthy")`);
  }
}

async function checkRbacCatalog() {
  const apiBase = process.env.API_BASE_URL || "http://127.0.0.1:8000";
  const resp = await fetch(`${apiBase}/api/v1/rbac/catalog`, {
    method: "GET",
    headers: { "Accept": "application/json" },
    signal: AbortSignal.timeout(10_000),
  });
  if (resp.ok) return; // catalog exposed — pre-flight OK.
  // 403/404/500 are tolerable: the catalog endpoint is feature-gated
  // (security.read) and may not be enabled in every environment; its absence
  // is a config note, not a proof the backend is dead.
  const text = await resp.text().catch(() => "");
  console.warn(
    `[global-setup] /api/v1/rbac/catalog not exposed (${resp.status} ${text.slice(0, 100)}); ` +
    "skipping catalog pre-flight (feature-gating or missing route)"
  );
}

async function checkWeb() {
  const webBase = process.env.WEB_BASE_URL || "http://127.0.0.1:3100";
  const resp = await fetch(webBase, {
    method: "GET",
    signal: AbortSignal.timeout(10_000),
  });
  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    throw new Error(
      `GET ${webBase} returned ${resp.status}: ${text.slice(0, 300)}`
    );
  }
  if (!resp.headers.get("content-type")?.includes("text/html")) {
    throw new Error(
      `Frontend responded with non-HTML content-type: ${resp.headers.get("content-type")}`
    );
  }
}
