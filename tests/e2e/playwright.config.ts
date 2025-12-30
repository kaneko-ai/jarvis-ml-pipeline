import { defineConfig } from '@playwright/test';

const serverPort = process.env.DASHBOARD_PORT || '8000';
const baseURL = process.env.DASHBOARD_BASE_URL || `http://localhost:${serverPort}`;

export default defineConfig({
  testDir: __dirname,
  testMatch: '**/*.spec.ts',
  outputDir: 'playwright-results',
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL,
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  reporter: [['list']],
  webServer: {
    command: `python -m http.server ${serverPort} --directory public`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
  },
});
