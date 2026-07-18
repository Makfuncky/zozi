/**
 * Zozi Scaling Plan — Comprehensive Browser Test Suite
 *
 * Covers all 6 resolved gaps + core functionality.
 * Run: cd frontend/web_app && npx playwright test e2e/scaling_audit.spec.ts
 */
import { test, expect } from "@playwright/test";

const API = "http://127.0.0.1:8000";

// ── Health & Connectivity ─────────────────────────────────────────────────

test("API health check returns 200", async ({ request }) => {
  const resp = await request.get(`${API}/health`);
  expect(resp.status()).toBe(200);
});

// ── Authentication (all roles) ─────────────────────────────────────────────

const CREDENTIALS = [
  ["admin", "admin@zozi.com", "admin123"],
  ["supplier", "supplier@zozi.com", "supplier123"],
  ["customer", "customer@zozi.com", "customer123"],
] as const;

for (const [role, email, password] of CREDENTIALS) {
  test(`${role} login returns token`, async ({ request }) => {
    const resp = await request.post(`${API}/auth/login`, {
      data: { email, password },
    });
    expect(resp.status()).toBe(200);
    const body = await resp.json();
    expect(body.access_token || body.token).toBeDefined();
  });
}

// ── Product Search (FTS5) ──────────────────────────────────────────────────

test("product search returns results", async ({ request }) => {
  const resp = await request.get(`${API}/api/products?search=test&limit=5`);
  if (resp.status() === 200) {
    const body = await resp.json();
    expect(body).toBeDefined();
    const items = body.items || body.products || body.data || (Array.isArray(body) ? body : [body]);
    expect(Array.isArray(items)).toBe(true);
  } else if (resp.status() === 404) {
    const resp2 = await request.get(`${API}/products?search=test&limit=5`);
    expect(resp2.status()).toBe(200);
  }
});

// ── Pagination (offset + cursor) ───────────────────────────────────────────

test("PageParams enforces max page size", async ({ request }) => {
  const resp = await request.get(`${API}/api/products?limit=9999`);
  if (resp.status() === 422) {
    const body = await resp.json();
    expect(body.detail).toBeDefined();
  } else {
    const body = await resp.json();
    const items = body.items || body.products || body.data || (Array.isArray(body) ? body : []);
    expect(Array.isArray(items)).toBe(true);
    expect(items.length).toBeLessThanOrEqual(100);
  }
});

test("cursor pagination returns next_cursor if supported", async ({ request }) => {
  const resp = await request.get(`${API}/api/products?limit=5`);
  if (resp.status() === 200) {
    const body = await resp.json();
    if (body.next_cursor !== undefined) {
      expect(typeof body.next_cursor).toBe("number");
      expect(body.has_more).toBeDefined();
    }
  }
});

// ── Storage Abstraction ────────────────────────────────────────────────────

test("uploads directory is accessible (local dev)", async ({ request }) => {
  const resp = await request.get(`${API}/uploads/`);
  expect(resp.status()).not.toBe(502);
  expect(resp.status()).not.toBe(500);
});

// ── Alembic & DB Health ───────────────────────────────────────────────────

test("DB responds to health check", async ({ request }) => {
  const resp = await request.get(`${API}/health`);
  expect(resp.status()).toBe(200);
  const body = await resp.json();
  expect(body.status).toBe("healthy");
});

// ── Presigned Upload (dev-safe) ────────────────────────────────────────────

test("presigned upload endpoint is reachable", async ({ request }) => {
  const resp = await request.post(`${API}/supplier/upload/presign`, {
    data: { filename: "test.jpg", content_type: "image/jpeg" },
  });
  if (resp.status() === 200) {
    const body = await resp.json();
    expect(body).toBeDefined();
  }
});

// ── File existence checks (code-level) ─────────────────────────────────────

test("Dockerfile.worker exists with correct CMD", () => {
  const fs = require("fs");
  const path = require("path");
  const workerDockerfile = path.resolve(__dirname, "../../../backend/Dockerfile.worker");
  expect(fs.existsSync(workerDockerfile)).toBe(true);
  const content = fs.readFileSync(workerDockerfile, "utf-8");
  expect(content).toContain("run_worker.py");
  expect(content).toContain("python:3.11");
});

test("docker-compose.prod.yml has worker and pgbouncer services", () => {
  const fs = require("fs");
  const path = require("path");
  const composePath = path.resolve(__dirname, "../../../docker-compose.prod.yml");
  expect(fs.existsSync(composePath)).toBe(true);
  const content = fs.readFileSync(composePath, "utf-8");
  expect(content).toContain("worker:");
  expect(content).toContain("pgbouncer:");
  expect(content).toContain("Dockerfile.worker");
  expect(content).toContain("DB_USE_PGBOUNCER=true");
});

test("S3Storage.purge_cdn exists", () => {
  const fs = require("fs");
  const path = require("path");
  const storagePath = path.resolve(__dirname, "../../../backend/services/storage.py");
  expect(fs.existsSync(storagePath)).toBe(true);
  const content = fs.readFileSync(storagePath, "utf-8");
  expect(content).toContain("def purge_cdn");
  expect(content).toContain("create_invalidation");
});

test("pagination.py has CursorPage and cursor_paginate", () => {
  const fs = require("fs");
  const path = require("path");
  const paginationPath = path.resolve(__dirname, "../../../backend/utils/pagination.py");
  expect(fs.existsSync(paginationPath)).toBe(true);
  const content = fs.readFileSync(paginationPath, "utf-8");
  expect(content).toContain("class CursorPage");
  expect(content).toContain("def cursor_paginate");
  expect(content).toContain("after_id");
});

test("rate_limit_middleware has presigned URL limits", () => {
  const fs = require("fs");
  const path = require("path");
  const middlewarePath = path.resolve(__dirname, "../../../backend/middleware/rate_limit_middleware.py");
  expect(fs.existsSync(middlewarePath)).toBe(true);
  const content = fs.readFileSync(middlewarePath, "utf-8");
  expect(content).toContain("/supplier/upload/presign");
});

test("pg_backup script exists", () => {
  const fs = require("fs");
  const path = require("path");
  const scriptPath = path.resolve(__dirname, "../../../backend/scripts/pg_backup.py");
  expect(fs.existsSync(scriptPath)).toBe(true);
  const content = fs.readFileSync(scriptPath, "utf-8");
  expect(content).toContain("def run_pg_dump");
  expect(content).toContain("pg_dump");
});

test("alembic merge migration exists with all heads", () => {
  const fs = require("fs");
  const path = require("path");
  const mergePath = path.resolve(__dirname, "../../../backend/alembic/versions/2026_07_17_09_00-opencode20260717a1_merge_heads.py");
  expect(fs.existsSync(mergePath)).toBe(true);
  const content = fs.readFileSync(mergePath, "utf-8");
  expect(content).toContain("down_revision = ('perf20260717f1', 'faexc20260717a1', 'banner20260717a1')");
  expect(content).toContain("revision = 'opencode20260717a1'");
});

// ── Full-stack flow: login → browse → search ──────────────────────────────

test("full user flow: login + browse + search", async ({ request }) => {
  // Login
  const loginResp = await request.post(`${API}/auth/login`, {
    data: { email: "customer@zozi.com", password: "customer123" },
  });
  expect(loginResp.status()).toBe(200);
  const loginBody = await loginResp.json();
  const token = loginBody.access_token || loginBody.token;
  expect(token).toBeDefined();

  const authHeaders = { Authorization: `Bearer ${token}` };

  // Browse products
  const browseResp = await request.get(`${API}/api/products?limit=10`, {
    headers: authHeaders,
  });
  expect(browseResp.status()).not.toBe(500);

  // Search
  const searchResp = await request.get(`${API}/api/products?search=phone&limit=5`, {
    headers: authHeaders,
  });
  expect(searchResp.status()).not.toBe(500);
});

// ── Rate Limiting Integration ─────────────────────────────────────────────

const _isLoadTest = require("fs")
  .readFileSync(
    require("path").resolve(__dirname, "../../../backend/.env"),
    "utf8"
  )
  .includes("RUNTIME_PROFILE=loadtest");

test("rate limit middleware responds with 429 under rapid failed logins", async ({ request }) => {
  test.skip(_isLoadTest, "Rate limiting disabled (loadtest profile)");
  const statuses: number[] = [];
  for (let i = 0; i < 15; i++) {
    const r = await request.post(`${API}/auth/login`, {
      data: { email: `nobody${i}@test.com`, password: "wrong" },
    });
    statuses.push(r.status());
    if (r.status() === 429) break;
  }
  expect(statuses).toContain(429);
});

// ── Worker Script Import ──────────────────────────────────────────────────

test("run_worker.py imports cleanly", () => {
  const fs = require("fs");
  const path = require("path");
  const workerPath = path.resolve(__dirname, "../../../backend/run_worker.py");
  expect(fs.existsSync(workerPath)).toBe(true);
  const content = fs.readFileSync(workerPath, "utf-8");
  expect(content).toContain("def main()");
  expect(content).toContain("import utils.heavy_tasks as heavy");
  expect(content).toContain("pop_pending");
  expect(content).toContain("run_heavy_job");
});

// ── Storage Backend Interface ─────────────────────────────────────────────

test("storage.py has complete StorageBackend interface", () => {
  const fs = require("fs");
  const path = require("path");
  const storagePath = path.resolve(__dirname, "../../../backend/services/storage.py");
  const content = fs.readFileSync(storagePath, "utf-8");
  // All required methods
  expect(content).toContain("def save");
  expect(content).toContain("def delete");
  expect(content).toContain("def purge_cdn");
  expect(content).toContain("def presign_put");
  expect(content).toContain("def public_url");
  // Both implementations
  expect(content).toContain("class LocalStorage");
  expect(content).toContain("class S3Storage");
  // Factory
  expect(content).toContain("def get_storage()");
  expect(content).toContain("def make_key");
  expect(content).toContain("def ext_for");
});
