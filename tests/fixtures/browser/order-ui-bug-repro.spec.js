import { test, expect } from '@playwright/test';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

/**
 * Bug Reproduction Spec: GAP-ORDER-001
 * Reproduces real UI bug: Calculate shipping rates triggers uncaught exception and freezes button.
 */
test('GAP-ORDER-001: reproduces uncaught exception and frozen button on calculate shipping', async ({ page }) => {
  const fixture = path.resolve('tests/fixtures/browser/order-app.html');
  await page.goto(pathToFileURL(fixture).href);

  // Collect page errors to verify defect
  const errors = [];
  page.on('pageerror', (err) => {
    errors.push(err.message);
  });

  const shippingBtn = page.locator('#btn-calc-shipping');
  await shippingBtn.click();

  // Assert Bug is Confirmed: Uncaught exception occurred and button is frozen
  expect(errors.length, 'GAP Confirmed: Uncaught JavaScript error triggered').toBeGreaterThan(0);
  expect(errors[0]).toContain('Cannot read properties of undefined');
  await expect(shippingBtn).toHaveClass(/spinner-active/);
  await expect(shippingBtn).toBeDisabled();
});
