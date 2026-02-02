import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: '.',
  timeout: 60000,  // タイムアウト延長
  retries: 2,      // リトライ追加
  workers: 1,      // 並列実行を無効化（安定性向上）

  use: {
    baseURL: process.env.DASHBOARD_BASE_URL || 'http://localhost:4173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'python -m http.server 4173 -d ../dashboard',
    url: 'http://localhost:4173',
    reuseExistingServer: !process.env.CI,
    timeout: 30000,
  },
});
