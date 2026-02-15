import { expect, test } from '@playwright/test';

const mockBase = process.env.MOCK_API_BASE || 'http://localhost:4010';

const selectors = {
  runRow: '#runs-table tbody tr',
  runLink: '#runs-table tbody tr a',
  exportTab: '[data-testid="tab-exports"]',
  exportLink: '#exports-list a',
  submissionTab: '[data-testid="tab-submission"]',
  submissionNotice: '[data-testid="submission-not-implemented"]',
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

  test('submission tab is marked out of personal core scope', async ({ page }) => {
    await page.goto('/run.html?id=RUN_MOCK_001');
    await expect(page.locator(selectors.submissionTab)).toBeDisabled();
    await expect(page.locator(selectors.submissionNotice)).toContainText('対象外');
  });
});
