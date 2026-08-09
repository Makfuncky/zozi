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
  testDir: "./__tests__",
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  webServer: [],
});