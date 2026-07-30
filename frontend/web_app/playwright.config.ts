import path from "path";
import { defineConfig } from "@playwright/test";

const configDir = process.cwd();
const repoRoot = path.resolve(configDir, "../..");
const backendDir = path.join(repoRoot, "backend");
const frontendDir = configDir;
const pythonExecutable = process.platform === "win32"
  ? path.join(backendDir, ".venv", "Scripts", "python.exe")
  : path.join(backendDir, ".venv", "bin", "python");
const resolvedPython = pythonExecutable && pythonExecutable.length > 0 ? pythonExecutable : "python";

function quote(value: string) {
  return value.includes(" ") ? `"${value}"` : value;
}

export default defineConfig({
  testDir: "./e2e",
  testMatch: ["**/__tests__/**/*.spec.ts", "**/e2e/**/*.spec.ts"],
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  // Servers are started manually outside Playwright (backend crashes when
  // spawned through config.webServer on this machine due to ASGI/uvicorn
  // async_generator issues). Start them before running tests:
  //   cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000
  //   cd frontend/web_app && npx next dev --port 3000
  webServer: [],
});
