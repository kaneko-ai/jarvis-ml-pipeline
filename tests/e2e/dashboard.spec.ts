import { expect, test } from '@playwright/test';

const mockBase = process.env.MOCK_API_BASE || 'http://localhost:4010';

const selectors = {
  apiBase: '[data-testid="settings-api-base"]',
  capabilitiesQuery: '[data-testid="settings-capabilities-query"]',
  save: '[data-testid="settings-save-btn"]',
  healthStatus: '[data-testid="health-status"]',
  runRow: '[data-testid="run-row"]',
  runLink: '[data-testid="run-link"]',
  exportLink: '[data-testid="export-file-link"]',
  rankPanel: '[data-testid="rank-panel"]',
};

test.describe('dashboard e2e (mock)', () => {
  test('settings to runs to run detail', async ({ page }) => {
    await page.goto('/settings.html');
    await page.fill(selectors.apiBase, mockBase);
    await page.fill(selectors.capabilitiesQuery, '');
    await page.click(selectors.save);

    await page.goto('/index.html');
    await expect(page.locator(selectors.healthStatus)).toHaveText(/OK/);

    await page.goto('/runs.html');
    await expect(page.locator(selectors.runRow).first()).toBeVisible();
    await page.locator(selectors.runLink).first().click();
    await expect(page).toHaveURL(/run.html/);
    await expect(page.locator(selectors.exportLink).first()).toBeVisible();
  });

  test('capabilities disable rank', async ({ page }) => {
    await page.goto('/settings.html');
    await page.fill(selectors.apiBase, mockBase);
    await page.fill(selectors.capabilitiesQuery, 'research_rank=false');
    await page.click(selectors.save);

    await page.goto('/run.html?id=RUN_MOCK_001');
    await expect(page.locator(selectors.rankPanel)).toContainText('未実装');
  });
});
