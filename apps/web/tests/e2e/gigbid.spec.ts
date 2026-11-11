import { expect, test } from '@playwright/test';

test.describe('GigBid E2E Flows', () => {
  test('1. Onboarding & portfolio display', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Sign-in & Onboarding' })).toBeVisible();
    await page.getByRole('button', { name: 'Sign In & Save Profile' }).click();
    await expect(page.getByText('Signed in and profile configured!')).toBeVisible();
  });

  test('2. Analyze job and approve proposal', async ({ page }) => {
    await page.goto('/inbox');
    await expect(page.getByRole('heading', { name: 'Job Inbox' })).toBeVisible();
    const analyzeBtn = page.getByRole('button', { name: 'Analyze & Draft' }).first();
    await analyzeBtn.click();
    await page.getByRole('link', { name: 'Open Studio' }).first().click();
    await expect(page.getByText('Human Approval Gate')).toBeVisible();
    await page.getByRole('button', { name: 'Approve & Submit Draft' }).click();
    await expect(page.getByText('Approved & submitted!')).toBeVisible();
  });

  test('3. Edit draft and promote to Style Memory', async ({ page }) => {
    await page.goto('/inbox');
    const analyzeBtns = page.getByRole('button', { name: 'Analyze & Draft' });
    await analyzeBtns.nth(1).click();
    await page.getByRole('link', { name: 'Open Studio' }).nth(1).click();
    const box = page.getByLabel('Edit Cover Letter');
    await box.fill('Updated concise opening backed by [ai_ml_engineer-case-02]. Proposed bid fits budget.');
    await page.getByRole('button', { name: 'Save Edit & Approve' }).click();
    await expect(page.getByText('Edited, promoted to Style Memory, & submitted!')).toBeVisible();
  });

  test('4. Reject proposal with a reason', async ({ page }) => {
    await page.goto('/inbox');
    const analyzeBtns = page.getByRole('button', { name: 'Analyze & Draft' });
    await analyzeBtns.nth(2).click();
    await page.getByRole('link', { name: 'Open Studio' }).nth(2).click();
    await page.getByPlaceholder('Rejection reason...').fill('Margin too low for scope');
    await page.getByRole('button', { name: 'Reject' }).click();
    await expect(page.getByText('Rejected with reason.')).toBeVisible();
  });

  test('5. Degraded-mode banner when Marketplace MCP is offline', async ({ page }) => {
    await page.goto('/runs');
    await page.getByRole('button', { name: 'Simulate Marketplace MCP Offline' }).click();
    await page.goto('/inbox');
    await expect(page.getByRole('alert')).toContainText('Degraded Mode');
    // Restore for subsequent tests
    await page.goto('/runs');
    await page.getByRole('button', { name: 'Restore Marketplace MCP Server' }).click();
  });
});
