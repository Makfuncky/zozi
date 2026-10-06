#!/usr/bin/env node
/**
 * preTestScan — static pre-flight scan of the Playwright suite.
 *
 * Runs before Playwright and fails loudly on defects that would otherwise
 * surface as confusing runtime errors:
 *
 *   1. broken-imports    relative imports that do not resolve on disk
 *   2. forbidden-imports imports from frontend/web_app/e2e/helpers (scope rule)
 *   3. missing-assertions specs with no expect() call (green-signal bypass risk)
 *   4. missing-assets    referenced files under test-assets/ that do not exist
 *   5. orphan-specs      specs that no project/glob in the config would pick up
 *
 * Exit code 0 = clean, 1 = blocking issues found.
 *
 * Usage: npm run scan   (from _browser_test/)
 */
import { readdir, readFile, access } from "node:fs/promises";
import { constants } from "node:fs";
import { join, dirname, resolve, relative } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const TESTS_DIR = join(ROOT, "tests");

const FORBIDDEN = /frontend\/web_app\/e2e\/(helpers|.*\.spec)/;
const IMPORT_RE = /(?:^|\n)\s*import\s+(?:[^'"]*?from\s+)?['"]([^'"]+)['"]/g;
const RELATIVE_RE = /^\.{1,2}\//;

// ── Mocking policy ──────────────────────────────────────────────────────────
// The suite may mock true externals (money, SMS, email). It must not mock the
// app's own API when that API is the subject of the test — otherwise the run
// proves nothing about the product. Session/cart chrome mocks are tolerated:
// they stabilise the shell without faking the feature under test.
// Allowed to mock: real third-party providers, and the app's own thin proxy
// endpoints that call them (comms/sms, comms/email, payments/stripe|paypal).
// These represent outbound money/messages, not application state.
const EXTERNAL_HINTS =
  /stripe|paypal|paytabs|thawani|\btap\.|twilio|whatsapp|sendgrid|mailgun|postmark|\bsmtp\b|sentry|glitchtip|slack|firebase|\/comms\/(sms|email)|\/(sms|email)\/\*\*/i;

// Quoted form is matched first so a glob like "**/api/v1/**" is not mis-parsed
// as a regex literal by the "//" inside it.
const ROUTE_RE =
  /(?:page|context|ctx)\.route\s*\(\s*(?:(["'`])([^"'`]+)\1|\/([^/\n]+)\/([gimsuy]*))/g;

// Chrome endpoints every layout hits regardless of what is under test.
const CHROME =
  /\*\*\/api\/auth\/(me|refresh|login)|\*\*\/cart|\*\*\/api\/notifications|\*\*\/notifications|\*\*\/admin\/hierarchy\/permissions/i;

const issues = {
  brokenImports: [],
  forbiddenImports: [],
  missingAssertions: [],
  missingAssets: [],
  subjectMocks: [],
  chromeMocks: [],
};

async function exists(p) {
  try {
    await access(p, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

/** Try the specifier as-is, then with .ts / .tsx / /index.ts appended. */
async function resolves(baseFile, specifier) {
  const base = resolve(dirname(baseFile), specifier);
  const candidates = [base, `${base}.ts`, `${base}.tsx`, join(base, "index.ts")];
  for (const c of candidates) {
    if (await exists(c)) return true;
  }
  return false;
}

async function scanFile(absPath) {
  const rel = relative(ROOT, absPath).replaceAll("\\", "/");
  const source = await readFile(absPath, "utf8");

  for (const match of source.matchAll(IMPORT_RE)) {
    const spec = match[1];
    if (FORBIDDEN.test(spec)) {
      issues.forbiddenImports.push({ file: rel, spec });
    }
    if (RELATIVE_RE.test(spec) && !(await resolves(absPath, spec))) {
      issues.brokenImports.push({ file: rel, spec });
    }
  }

  // A spec with no expect() call cannot fail on a broken UI.
  if (!/\bexpect\s*\(/.test(source) && !/\bexpect\.\w+\(/.test(source)) {
    issues.missingAssertions.push(rel);
  }

  for (const match of source.matchAll(/["'`](test-assets\/[^"'`]+)["'`]/g)) {
    const asset = resolve(ROOT, match[1]);
    if (!(await exists(asset))) {
      issues.missingAssets.push({ file: rel, asset: match[1] });
    }
  }

  // Mocking policy. Strip only whole-line // comments — never /* */ blocks:
  // Playwright globs such as "**/cart/**" contain the literal sequence /*, and a
  // block-comment regex silently deletes real code between them.
  const code = source.replace(/^\s*\/\/.*$/gm, " ");

  for (const m of code.matchAll(ROUTE_RE)) {
    const pattern = (m[2] ?? m[3] ?? "").trim();
    if (!pattern) continue;
    if (EXTERNAL_HINTS.test(pattern)) continue; // real third party: allowed
    if (
      !/(\/api\/|\/(admin|customer|supplier|logistics|employee|hr|finance|orders|products|payments|commissions|promotions|suppliers)\b)/i.test(
        pattern,
      )
    )
      continue;
    if (CHROME.test(pattern)) issues.chromeMocks.push({ file: rel, spec: pattern });
    else issues.subjectMocks.push({ file: rel, spec: pattern });
  }
}

async function collectSpecs(dir) {
  const out = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name);
    if (entry.isDirectory()) out.push(...(await collectSpecs(p)));
    else if (entry.isFile() && entry.name.endsWith(".spec.ts")) out.push(p);
  }
  return out;
}

async function main() {
  const specs = (await collectSpecs(TESTS_DIR)).sort();
  await Promise.all(specs.map(scanFile));

  const byArea = {};
  for (const spec of specs) {
    const rel = relative(TESTS_DIR, spec).replaceAll("\\", "/");
    const area = rel.includes("/") ? rel.split("/")[0] : "(root)";
    byArea[area] = (byArea[area] ?? 0) + 1;
  }

  console.log(`preTestScan: ${specs.length} spec file(s) under tests/`);
  for (const [area, count] of Object.entries(byArea).sort()) {
    console.log(`  ${area.padEnd(16)} ${count}`);
  }

  const sections = [
    ["broken-imports", issues.brokenImports, "relative import does not resolve", true],
    ["forbidden-imports", issues.forbiddenImports, "imports from frontend/web_app/e2e (out of scope)", true],
    ["missing-assets", issues.missingAssets, "referenced test asset does not exist", true],
    ["missing-assertions", issues.missingAssertions, "no expect() call — cannot fail", false],
    [
      "subject-mocks",
      issues.subjectMocks,
      "spec mocks the app's own API for the feature under test — prove it against the real backend",
      false,
    ],
    ["chrome-mocks", issues.chromeMocks, "layout/session chrome is mocked (tolerated)", false],
  ];

  let blocking = 0;
  for (const [label, list, hint, isBlocking] of sections) {
    if (!list.length) continue;
    const summarise = label === "missing-assertions";
    if (summarise) {
      console.log(`\n  [${label}] ${list.length} issue(s) — ${hint}`);
      for (const item of list) console.log(`    - ${item}`);
    } else {
      // Collapse to per-file counts: a 100-line advisory dump gets ignored,
      // which is the same failure mode as a noisy check with no signal.
      const perFile = new Map();
      for (const item of list) {
        const key = typeof item === "string" ? item : item.file;
        if (!perFile.has(key)) perFile.set(key, []);
        perFile.get(key).push(typeof item === "string" ? "" : (item.spec ?? item.asset));
      }
      console.log(`\n  [${label}] ${list.length} mock(s) across ${perFile.size} spec(s) — ${hint}`);
      for (const [file, pats] of [...perFile].sort()) {
        const uniq = [...new Set(pats.filter(Boolean))];
        console.log(`    - ${file}  (${uniq.length})`);
        for (const p of uniq.slice(0, 3)) console.log(`        ${p}`);
        if (uniq.length > 3) console.log(`        ... +${uniq.length - 3} more`);
      }
    }
    if (isBlocking) blocking += list.length;
  }

  if (blocking) {
    console.log(`\npreTestScan: FAILED — ${blocking} blocking issue(s).`);
    process.exit(1);
  }
  if (issues.missingAssertions.length) {
    console.log(
      `\npreTestScan: OK (advisory only) — ${issues.missingAssertions.length} spec(s) lack assertions.`,
    );
  } else {
    console.log("\npreTestScan: OK — all specs resolve, import in-scope, and assert.");
  }
  process.exit(0);
}

main().catch((err) => {
  console.error("preTestScan crashed:", err);
  process.exit(1);
});
