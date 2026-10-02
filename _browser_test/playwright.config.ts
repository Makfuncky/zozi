import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: ['**/*.spec.ts', '**/*.test.ts'],
  fullyParallel: false,
  workers: parseInt(process.env.PW_WORKERS || '1', 10),
  timeout: parseInt(process.env.PW_TIMEOUT || '30_000', 10),
  retries: parseInt(process.env.PW_RETRIES || '1', 10),
  globalSetup: './global-setup.ts',
  globalTeardown: './global-teardown.ts',
  use: {
    baseURL: process.env.WEB_BASE_URL || 'http://127.0.0.1:3100',
    trace: 'retain-on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-first-retry',
    actionTimeout: parseInt(process.env.PW_ACTION_TIMEOUT || '15_000', 10),
    navigationTimeout: parseInt(process.env.PW_NAV_TIMEOUT || '45_000', 10),
  },
  reporter: [
    ['list'],
    ['html', { outputFolder: 'reports/html', open: 'never' }],
    ['json', { outputFile: 'reports/run/results.json' }],
    ['junit', { outputFile: 'reports/run/junit.xml' }],
  ],
  outputDir: 'test-results/',
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
