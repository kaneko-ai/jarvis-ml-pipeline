import path from 'path';

import { defineConfig, devices } from '@playwright/test';

const repoRoot = path.resolve(__dirname, '..', '..');
const dashboardBaseUrl = process.env.DASHBOARD_BASE_URL || 'http://localhost:4173';
const mockApiBase = process.env.MOCK_API_BASE || 'http://localhost:4010';

export default defineConfig({
  testDir: '.',
  timeout: 60000,  // タイムアウト延長
  retries: 2,      // リトライ追加
  workers: 1,      // 並列実行を無効化（安定性向上）

  use: {
    baseURL: dashboardBaseUrl,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: [
    {
      command: 'uv run python -m uvicorn tests.mock_server.app:app --port 4010 --log-level warning',
      cwd: repoRoot,
      url: `${mockApiBase}/api/health`,
      reuseExistingServer: true,
      timeout: 30000,
    },
    {
      command: 'python -m http.server 4173 -d dashboard',
      cwd: repoRoot,
      url: dashboardBaseUrl,
      reuseExistingServer: true,
      timeout: 30000,
    },
  ],
});
