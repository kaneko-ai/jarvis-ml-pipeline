import { expect, test } from '@playwright/test';

test.describe('public dashboard e2e', () => {
  test('index.html loads', async ({ page }) => {
    await page.goto('/index.html');
    await expect(page.getByRole('heading', { name: /JARVIS Research OS/i })).toBeVisible();
  });

  test('runs list renders fixture run', async ({ page }) => {
    await page.goto('/index.html');
    await page.getByText('📋 実行履歴').click();
    await expect(page.locator('#runs-table-container')).toContainText('fixture_run_001');
  });

  test('run detail shows manifest report', async ({ page }) => {
    await page.goto('/index.html');
    await page.getByText('📋 実行履歴').click();
    await page.locator('#runs-table-container tr', { hasText: 'fixture_run_001' }).first().click();
    await expect(page.locator('#run-modal')).toBeVisible();
    await expect(page.locator('#modal-body')).toContainText('Fixture Run Report');
    await expect(page.locator('#modal-body')).toContainText('fixture report for the public dashboard E2E test');
  });

  test('search loads index and renders results', async ({ page }) => {
    await page.goto('/index.html');
    await page.getByText('📑 検索').click();
    await page.fill('#search-input', 'biology');
    await page.getByRole('button', { name: '検索' }).click();
    await expect(page.locator('.search-result-title')).toContainText('Fixture Paper on Biology');
  });
});
