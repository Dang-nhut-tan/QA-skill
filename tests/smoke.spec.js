import { test, expect } from '@playwright/test';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

/**
 * Baseline smoke verification to validate Playwright CLI is operational.
 */
test('TC-SYS-001: local fixture responds to a real user action', async ({ page }) => {
  const fixture = path.resolve('tests/fixtures/browser/smoke.html');
  await page.goto(pathToFileURL(fixture).href);
  await expect(page.getByRole('status')).toHaveText('Ready');
  await page.getByRole('button', { name: 'Run verification' }).click();
  await expect(page.getByRole('status')).toHaveText('Verification passed');
});
