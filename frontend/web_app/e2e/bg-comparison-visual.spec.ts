/**
 * BG Strategy Comparison — Visual Regression Test
 *
 * Captures each side-by-side strategy grid from the comparison HTML report
 * and diffs them against stored baselines using Playwright's built-in
 * ``toHaveScreenshot()``.  First run creates baselines; subsequent runs
 * fail on any pixel difference beyond the tolerance (maxDiffPixels).
 *
 * Grid sections captured (12 total):
 *   - 4 Clothing grids  (casual wear, warm-toned, fashion, textile)
 *   - 4 Electronics grids (gadget, dark device, component, tech)
 *   - 4 Beauty grids    (blue-tone, red/orange cosmetic, pink, personal care)
 *
 * Also captures:
 *   - Full-page screenshot of the report
 *   - Per-category winner table
 *   - Detailed metrics table
 *
 * Prerequisites — generate the comparison report first (≈5 min):
 *   cd backend && python ../provider_test/run_bg_comparison.py
 *
 * Run (first run creates baselines, subsequent runs diff):
 *   cd frontend/web_app
 *   npx playwright test e2e/bg-comparison-visual.spec.ts
 *
 * Update baselines after intentional changes to bg removal strategies:
 *   npx playwright test e2e/bg-comparison-visual.spec.ts --update-snapshots
 */

import { expect, test, type Page } from "@playwright/test";
import http from "http";
import fs from "fs";
import path from "path";

// ── Server lifecycle ────────────────────────────────────────────────
// Serve the comparison report directory via a local HTTP server so that
// the browser loads images without CORS/file-protocol restrictions.

const REPORT_DIR = path.resolve(__dirname, "../../../provider_test/bg_comparison");
const REPORT_FILE = path.join(REPORT_DIR, "index.html");

const BASE_PORT = 7171;
const MAX_PORT_ATTEMPTS = 5;
let serverPort = BASE_PORT;
let server: http.Server | null = null;

function startServer(): Promise<void> {
  return new Promise((resolve, reject) => {
    const tryPort = (port: number) => {
      server = http.createServer((req, res) => {
      // Map the request URL to a file path in REPORT_DIR
      const safePath = req.url
        ? decodeURIComponent(req.url).split("?")[0].split("#")[0]
        : "/";
      const filePath = path.join(
        REPORT_DIR,
        safePath === "/" ? "index.html" : safePath,
      );

      // Security: ensure resolved path stays within REPORT_DIR
      if (!filePath.startsWith(REPORT_DIR)) {
        res.writeHead(403);
        res.end("Forbidden");
        return;
      }

      if (!fs.existsSync(filePath)) {
        res.writeHead(404);
        res.end("Not found");
        return;
      }

      // Determine content type from extension
      const ext = path.extname(filePath).toLowerCase();
      const mimeTypes: Record<string, string> = {
        ".html": "text/html; charset=utf-8",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".json": "application/json",
        ".css": "text/css",
        ".js": "application/javascript",
      };
      const contentType = mimeTypes[ext] || "application/octet-stream";

      res.writeHead(200, { "Content-Type": contentType });
      fs.createReadStream(filePath).pipe(res);
    });

      server!.listen(port, "127.0.0.1", () => {
        serverPort = port;
        resolve();
      });
      server!.on("error", (err: NodeJS.ErrnoException) => {
        if (err.code === "EADDRINUSE" && port - BASE_PORT < MAX_PORT_ATTEMPTS - 1) {
          server!.close();
          server = null;
          tryPort(port + 1);
        } else {
          reject(err);
        }
      });
    };
    tryPort(BASE_PORT);
  });
}

function stopServer(): void {
  if (server) {
    server.close();
    server = null;
  }
}

test.beforeAll(async () => {
  // Verify the comparison report exists
  if (!fs.existsSync(REPORT_FILE)) {
    throw new Error(
      `Comparison report not found at ${REPORT_FILE}\n\n` +
        "Generate it first:\n" +
        "  cd backend && python ../provider_test/run_bg_comparison.py\n" +
        "(This takes ~5 minutes and runs all 6 strategies on 12 images.)",
    );
  }

  // Verify grid images exist
  const gridFiles = fs
    .readdirSync(REPORT_DIR)
    .filter((f) => f.startsWith("strategy_grid_") && f.endsWith(".png"));
  if (gridFiles.length === 0) {
    throw new Error(
      "No strategy grid PNGs found in the comparison report directory.\n" +
        "The report may be incomplete. Regenerate it:\n" +
        "  cd backend && python ../provider_test/run_bg_comparison.py",
    );
  }

  await startServer();
});

test.afterAll(() => {
  stopServer();
});

// ── Helper: load the report page ────────────────────────────────────

async function loadReport(page: Page) {
  await page.goto(`http://127.0.0.1:${serverPort}/`);
  // Wait for the report heading to confirm full render
  await expect(page.locator("h1")).toContainText("BG Strategy Comparison", {
    timeout: 15_000,
  });
  // Let all grid images finish loading (each is a 3-row × 3-col composite)
  await page.waitForTimeout(2_000);
}

// ── Grid Section Definitions ────────────────────────────────────────
// Each entry is matched by its text content in <h2> headings:
//   "Clothing — <em>Casual Wear (Light)</em>"
//   "Electronics — <em>Gadget (Neutral)</em>"
//   "Beauty & Personal Care — <em>Blue-tone Product</em>"

interface GridSection {
  /** Full category heading text as it appears in the <h2> */
  matchText: string;
  /** Short safe filename (no spaces/special chars) for the baseline PNG */
  filename: string;
}

const GRID_SECTIONS: GridSection[] = [
  // Clothing
  { matchText: "Clothing",       filename: "Clothing-05" },
  { matchText: "Warm-toned",     filename: "Clothing-07" },
  { matchText: "Fashion Product", filename: "Clothing-08" },
  { matchText: "Textile Close-up", filename: "Clothing-12" },
  // Electronics
  { matchText: "Gadget",            filename: "Electronics-04" },
  { matchText: "Dark Device",       filename: "Electronics-15" },
  { matchText: "Electronic Component", filename: "Electronics-17" },
  { matchText: "Tech Product",      filename: "Electronics-23" },
  // Beauty & Personal Care
  { matchText: "Blue-tone Product",   filename: "Beauty-14" },
  { matchText: "Red/Orange Cosmetic", filename: "Beauty-16" },
  { matchText: "Pink Beauty Item",    filename: "Beauty-29" },
  { matchText: "Personal Care",       filename: "Beauty-30" },
];

// ══════════════════════════════════════════════════════════════════════
// Tests — single page load, sequential screenshots
// ══════════════════════════════════════════════════════════════════════
// All screenshots are taken within ONE page load to avoid reloading
// 12 grid images 14 times (which would be ~200 image loads).

test.describe("BG Strategy Comparison Visual Regression", () => {
  test("full report capture", async ({ page }) => {
    test.setTimeout(180_000); // 3 min for all 14 screenshots
    await loadReport(page);

    // ── 1. Full-page screenshot ──
    await expect(page).toHaveScreenshot("bg-compare-full.png", {
      fullPage: true,
      maxDiffPixels: 2000, // 12 large grid composites; allow rendering diffs
    });

    // ── 2. Per-category rankings tables ──
    const winnerTables = page.locator("table.winner");
    await expect(winnerTables.first()).toBeVisible({ timeout: 10_000 });

    await expect(winnerTables.nth(0)).toHaveScreenshot(
      "bg-compare-rankings-clothing.png",
      { maxDiffPixels: 100 },
    );
    await expect(winnerTables.nth(1)).toHaveScreenshot(
      "bg-compare-rankings-electronics.png",
      { maxDiffPixels: 100 },
    );
    await expect(winnerTables.nth(2)).toHaveScreenshot(
      "bg-compare-rankings-beauty.png",
      { maxDiffPixels: 100 },
    );

    // ── 3. Detailed metrics table ──
    const metricsTable = page.locator("div[style*='overflow-x:auto'] table");
    await expect(metricsTable).toBeVisible({ timeout: 10_000 });
    await expect(metricsTable).toHaveScreenshot(
      "bg-compare-metrics-table.png",
      { maxDiffPixels: 300 },
    );

    // ── 4. Each grid section — by position (.nth) ──
    // The 12 <div class="grid-section"> elements appear in the same order
    // as GRID_SECTIONS: 4 Clothing → 4 Electronics → 4 Beauty.
    const allGrids = page.locator(".grid-section");
    const gridCount = await allGrids.count();
    expect(gridCount).toBe(GRID_SECTIONS.length);

    for (const [i, section] of GRID_SECTIONS.entries()) {
      const gridDiv = allGrids.nth(i);

      await expect(gridDiv).toBeVisible({ timeout: 10_000 });
      await gridDiv.scrollIntoViewIfNeeded();
      await page.waitForTimeout(300);

      await expect(gridDiv).toHaveScreenshot(
        `bg-compare-grid-${section.filename}.png`,
        { maxDiffPixels: 200 },
      );
    }
  });
});
