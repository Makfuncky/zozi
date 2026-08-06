import { spawn } from "child_process";
import http from "http";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..");
const host = "127.0.0.1";
const port = Number(process.env.PORT ?? 5173);
const url = `http://${host}:${port}/`;
const recordingsDir = path.resolve(projectRoot, "recordings");
const durationMs = Number(process.env.DURATION_MS ?? 8000);
const startupTimeoutMs = Number(process.env.STARTUP_TIMEOUT_MS ?? 30000);
const warmupMs = Number(process.env.WARMUP_MS ?? 2000);

function waitForServer(url, timeoutMs) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const check = () => {
      if (Date.now() - start > timeoutMs) {
        reject(new Error(`Timed out waiting for ${url}`));
        return;
      }

      http
        .get(url, (res) => {
          if (res.statusCode === 200) {
            resolve();
          } else {
            res.resume();
            setTimeout(check, 250);
          }
        })
        .on("error", () => setTimeout(check, 250));
    };

    check();
  });
}

async function main() {
  console.log("Starting Vite dev server...");
  const server = spawn(
    "npm",
    ["run", "dev", "--", "--host", host, "--port", String(port), "--strictPort"],
    {
      cwd: projectRoot,
      shell: true,
      stdio: ["ignore", "pipe", "pipe"],
    },
  );

  server.stdout.on("data", (chunk) => process.stdout.write(chunk));
  server.stderr.on("data", (chunk) => process.stdout.write(chunk));

  const cleanup = () => {
    if (!server.killed) {
      server.kill("SIGTERM");
    }
  };

  process.on("SIGINT", () => {
    cleanup();
    process.exit(1);
  });
  process.on("SIGTERM", cleanup);

  try {
    await waitForServer(url, startupTimeoutMs);
    console.log(`Dev server ready at ${url}`);

    const { chromium } = await import("playwright");
    if (!fs.existsSync(recordingsDir)) {
      fs.mkdirSync(recordingsDir, { recursive: true });
    }

    const browser = await chromium.launch();
    const context = await browser.newContext({
      viewport: { width: 1280, height: 720 },
      recordVideo: { dir: recordingsDir, size: { width: 1280, height: 720 } },
    });

    const page = await context.newPage();
    await page.goto(url);
    console.log(`Waiting ${warmupMs}ms for animation warm-up on ${url}...`);
    await page.waitForTimeout(warmupMs);
    console.log(`Recording ${durationMs}ms of animation...`);
    await page.waitForTimeout(durationMs);
    await page.close();
    await context.close();
    await browser.close();

    const recordings = fs.readdirSync(recordingsDir).filter((name) => name.endsWith(".webm"));
    const latest = recordings
      .map((name) => ({
        name,
        time: fs.statSync(path.join(recordingsDir, name)).mtimeMs,
      }))
      .sort((a, b) => b.time - a.time)[0];

    if (latest) {
      console.log(`Saved recording to ${path.join(recordingsDir, latest.name)}`);
    } else {
      console.log("Recording finished, but no video file was found.");
    }
  } catch (error) {
    console.error(error);
    process.exit(1);
  } finally {
    cleanup();
  }
}

main();
