/**
 * preTestScan — static pre-flight scan of the browser test suite.
 *
 * Runs before Playwright executes and reports:
 *   - Total spec files discovered
 *   - Specs that bypass the fixtures guard (no `commands`/`workflows`/`verify`)
 *   - Specs that lack any `expect`/`verify` assertions (green-signal bypass risk)
 *   - Specs that do not import from "../fixtures" (legacy pattern still in use)
 *
 * Exit code 0 = suite is clean; 1 = issues found (logged but not fatal).
 *
 * Usage: node scripts/preTestScan.js  (from the _browser_test directory)
 */
import { readdir, readFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = fileURLToPath(new URL(".", import.meta.url));

const TESTS_DIR = join(__dirname, "..", "tests");
const RESULTS = {
  total: 0,
  legacyImport: [],
  noWorkflows: [],
  noAssertions: [],
};

async function scanFile(filePath) {
  const source = await readFile(filePath, "utf-8");
  const relative = filePath.replace(TESTS_DIR + "/", "");
  const importFixtures = source.includes('from "../fixtures"') || source.includes('from "@fixtures"');
  const callsCommands = /\bcommands\.(navigate|click|fill|check|uploadFile|selectOption|waitForVisible|getApi|postApi|patchApi|deleteApi)\b/.test(source);
  const callsWorkflows = /\bworkflows\./.test(source);
  const callsVerify = /\bverify\./i.test(source);
  const hasAssert = /\bexpect\.(?:[^.]+\.)?\w+\(/.test(source) || /\bverify\./i.test(source);

  RESULTS.total += 1;

  if (!importFixtures) RESULTS.legacyImport.push(relative);
  if (!callsCommands && !callsWorkflows && !callsVerify) RESULTS.noWorkflows.push(relative);
  if (!hasAssert) RESULTS.noAssertions.push(relative);
}

async function main() {
  const specs = [];
  const walk = async (dir) => {
    try {
      const entries = await readdir(dir, { withFileTypes: true });
      for (const entry of entries) {
        const path = join(dir, entry.name);
        if (entry.isDirectory()) await walk(path);
        else if (entry.isFile() && entry.name.endsWith('.spec.ts')) specs.push(path);
      }
    } catch (err) {
      console.error(`preTestScan: error scanning ${dir}: ${err.message}`);
    }
  };
  await walk(TESTS_DIR);

  const tasks = specs.map(scanFile);
  await Promise.all(tasks);

  console.log(`preTestScan: ${RESULTS.total} spec(s) discovered in tests/`);

  if (RESULTS.legacyImport.length) {
    console.log(`  [legacy-import] ${RESULTS.legacyImport.length} spec(s) not using ../fixtures:`);
    for (const f of RESULTS.legacyImport) console.log(`    - ${f}`);
  }
  if (RESULTS.noWorkflows.length) {
    console.log(`  [no-workflows] ${RESULTS.noWorkflows.length} spec(s) without commands./workflows./verify. (green-signal risk):`);
    for (const f of RESULTS.noWorkflows) console.log(`    - ${f}`);
  }
  if (RESULTS.noAssertions.length) {
    console.log(`  [no-assertions] ${RESULTS.noAssertions.length} spec(s) without expect/verify:`);
    for (const f of RESULTS.noAssertions) console.log(`    - ${f}`);
  }

  const issues = RESULTS.legacyImport.length + RESULTS.noWorkflows.length + RESULTS.noAssertions.length;
  if (issues) {
    console.log(`preTestScan: ${issues} issue(s) found — see report above.`);
    process.exit(1);
  }
  console.log("preTestScan: OK — all specs use the fixtures guard and contain actions + assertions.");
  process.exit(0);
}

main().catch((e) => {
  console.error("preTestScan failed:", e);
  process.exit(1);
});
