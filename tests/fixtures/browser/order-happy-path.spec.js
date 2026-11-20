import { test, expect } from '@playwright/test';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

/**
 * Golden Happy Path Test: TC-ORDER-001
 * Verifies that submitting valid order details displays the confirmation banner.
 */
test('TC-ORDER-001: creates order successfully with valid details', async ({ page }) => {
  const fixture = path.resolve('tests/fixtures/browser/order-app.html');
  await page.goto(pathToFileURL(fixture).href);

  await page.locator('#item-name').fill('Pro Laptop');
  await page.locator('#item-qty').fill('2');
  await page.locator('#item-price').fill('1200');

  await page.locator('#btn-submit-order').click();

  const banner = page.locator('#confirmation-banner');
  await expect(banner).toBeVisible({ timeout: 5000 });
  await expect(banner).toContainText('Order created successfully: ORD-1001');
});
