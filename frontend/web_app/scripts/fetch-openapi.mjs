#!/usr/bin/env node
// scripts/fetch-openapi.mjs
// Fetch the live OpenAPI schema from the running backend into ./openapi.json.
// The backend exposes /openapi.json natively via FastAPI when not in production.
// Usage: node scripts/fetch-openapi.mjs [base_url]
//   base_url defaults to http://127.0.0.1:8000

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "..");

const baseUrl = (process.argv[2] || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const out = path.join(ROOT, "openapi.json");

async function main() {
  const url = `${baseUrl}/openapi.json`;
  process.stdout.write(`[openapi] GET ${url} ... `);
  const res = await fetch(url, { headers: { accept: "application/json" } });
  if (!res.ok) {
    process.stdout.write(`FAIL (${res.status})\n`);
    process.stderr.write(`Failed to fetch OpenAPI schema from ${url}\n`);
    process.exit(1);
  }
  const text = await res.text();
  fs.writeFileSync(out, text, "utf8");
  process.stdout.write(`OK (${text.length.toLocaleString()} bytes) -> ${path.relative(ROOT, out)}\n`);
}

main().catch((err) => {
  process.stderr.write(`[openapi] error: ${err?.message || String(err)}\n`);
  process.exit(1);
});