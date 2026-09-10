#!/usr/bin/env node
// scripts/generate-openapi-types.mjs
// Generates TypeScript types from the OpenAPI schema into src/lib/api/schema.d.ts
// using openapi-typescript. If no openapi.json is present locally, this script
// first attempts to fetch one from the running backend via fetch-openapi.mjs.
// Usage: node scripts/generate-openapi-types.mjs

import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, "..");

const SCHEMA_SRC = path.join(ROOT, "openapi.json");
const OUT_FILE = path.join(ROOT, "src", "lib", "api", "schema.d.ts");
const FETCHER = path.join(__dirname, "fetch-openapi.mjs");

function run(cmd, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, { stdio: "inherit", cwd: ROOT, shell: true });
    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${cmd} ${args.join(" ")} exited with code ${code}`));
    });
  });
}

async function ensureSchema() {
  if (fs.existsSync(SCHEMA_SRC)) return;
  process.stdout.write("[openapi] openapi.json missing; attempting live fetch...\n");
  try {
    await run("node", [FETCHER]);
  } catch {
    // Live fetch is best-effort. Fall back to a minimal stub so type generation
    // does not break offline builds. The stub exposes a single `paths` object
    // so openapi-typescript emits a valid (empty) `paths` type.
    process.stdout.write("[openapi] live fetch failed; writing minimal stub openapi.json\n");
    fs.writeFileSync(SCHEMA_SRC, JSON.stringify({ openapi: "3.0.0", info: { title: "stub", version: "0.0.0" }, paths: {} }), "utf8");
  }
}

async function main() {
  await ensureSchema();
  process.stdout.write(`[openapi] generating types -> ${path.relative(ROOT, OUT_FILE)}\n`);
  await run("npx", ["--yes", "openapi-typescript", SCHEMA_SRC, "--output", OUT_FILE]);
  process.stdout.write("[openapi] done.\n");
}

main().catch((err) => {
  process.stderr.write(`[openapi] generation failed: ${err?.message || String(err)}\n`);
  process.exit(1);
});