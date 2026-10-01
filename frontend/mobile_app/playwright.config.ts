import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [['list'], ['json', { outputFile: 'playwright-results.json' }]],
  timeout: 60_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: process.env.PW_BASE_URL || 'http://localhost:8090',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    userAgent: 'Mozilla/5.0 (Playwright) ZOZI Mobile',
  },
  projects: [
    {
      name: 'mobile-web',
      use: {
        ...devices['Pixel 5'],
        viewport: { width: 390, height: 844 },
        deviceScaleFactor: 2,
      },
    },
  ],
  webServer: process.env.PW_WEB_SERVER
    ? {
        command: process.env.PW_WEB_SERVER,
        url: process.env.PW_BASE_URL || 'http://localhost:8090',
        reuseExistingServer: !process.env.CI,
        timeout: 30_000,
      }
    : undefined,
});