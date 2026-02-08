import { expect, test } from '@playwright/test';

const mockBase = process.env.MOCK_API_BASE || 'http://localhost:4010';

const selectors = {
  runRow: '#runs-table tbody tr',
  runLink: '#runs-table tbody tr a',
  exportTab: '[data-testid="tab-exports"]',
  exportLink: '#exports-list a',
  rankTab: '[data-testid="tab-rank"]',
  rankContent: '#rank-content',
};

test.describe('dashboard e2e (mock)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/index.html');
    await page.evaluate(([base, token]) => {
      localStorage.setItem('JAVIS_API_BASE', base);
      localStorage.setItem('JAVIS_API_TOKEN', token);
    }, [mockBase, 'test-token']);
  });

  test('runs to run detail and export links', async ({ page }) => {
    await page.goto('/runs.html');
    await expect(page.locator(selectors.runRow).first()).toBeVisible();
    await page.locator(selectors.runLink).first().click();
    await expect(page).toHaveURL(/run\.html\?id=/);
    await page.click(selectors.exportTab);
    await expect(page.locator(selectors.exportLink).first()).toBeVisible();
  });

  test('rank tab shows mock ranking result', async ({ page }) => {
    await page.goto('/run.html?id=RUN_MOCK_001');
    await page.click(selectors.rankTab);
    await expect(page.locator(selectors.rankContent)).toContainText('Mock Paper');
  });
});
