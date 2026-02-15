import { expect, test } from '@playwright/test';

const mockBase = process.env.MOCK_API_BASE || 'http://localhost:4010';

test.describe('public dashboard e2e', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/index.html');
    await page.evaluate(([base, token]) => {
      localStorage.setItem('JAVIS_API_BASE', base);
      localStorage.setItem('JAVIS_API_TOKEN', token);
    }, [mockBase, 'test-token']);
  });

  test('index.html loads', async ({ page }) => {
    await page.goto('/index.html');
    await expect(page.getByRole('heading', { name: 'Research OS Dashboard' })).toBeVisible();
  });

  test('runs list renders mock run', async ({ page }) => {
    await page.goto('/runs.html');
    await expect(page.locator('#runs-table tbody tr').first()).toBeVisible();
    await expect(page.locator('#runs-table')).toContainText('RUN_MOCK_001');
  });

  test('run detail shows personal-core submission scope', async ({ page }) => {
    await page.goto('/run.html?id=RUN_MOCK_001');
    await expect(page.locator('[data-testid="tab-submission"]')).toBeDisabled();
    await expect(page.locator('[data-testid="submission-not-implemented"]')).toContainText('対象外');
  });

  test('search page can save query locally', async ({ page }) => {
    await page.goto('/search.html');
    await page.fill('#savedQueryName', 'fixture');
    await page.fill('#savedQueryText', 'biology');
    await page.click('form#savedQueryForm button[type="submit"]');
    await expect(page.locator('#savedQueriesList')).toContainText('biology');
  });
});
