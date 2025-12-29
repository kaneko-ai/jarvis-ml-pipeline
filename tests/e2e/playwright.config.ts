import { defineConfig } from '@playwright/test';

const baseURL = process.env.DASHBOARD_BASE_URL || 'http://localhost:4173';

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
  reporter: [['list']]
});
