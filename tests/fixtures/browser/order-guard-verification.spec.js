import { test, expect } from '@playwright/test';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

/**
 * Verified Security Guard Spec: GUARD-ORDER-001
 * Verifies that negative quantity triggers validation guard and disables submit button.
 */
test('GUARD-ORDER-001: validates and blocks negative quantity', async ({ page }) => {
  const fixture = path.resolve('tests/fixtures/browser/order-app.html');
  await page.goto(pathToFileURL(fixture).href);

  const qtyInput = page.locator('#item-qty');
  const errorMsg = page.locator('#error-qty');
  const submitBtn = page.locator('#btn-submit-order');

  // Input negative quantity
  await qtyInput.fill('-3');

  // Assert Security Guard holds
  await expect(errorMsg).toBeVisible({ timeout: 5000 });
  await expect(errorMsg).toHaveText('Quantity must be greater than 0');
  await expect(submitBtn).toBeDisabled();
});
